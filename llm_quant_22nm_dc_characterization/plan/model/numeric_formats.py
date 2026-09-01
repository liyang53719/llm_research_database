from __future__ import annotations

import bisect
import math
import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable

import numpy as np


class OperandFormat(IntEnum):
    INT4 = 0
    INT8 = 1
    FP8_E4M3FN = 2
    BF16 = 3


def float32_to_u32(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", float(np.float32(value))))[0]


def u32_to_float32(bits: int) -> np.float32:
    return np.float32(struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0])


def float32_to_bf16(value: float) -> int:
    bits = float32_to_u32(value)
    lsb = (bits >> 16) & 1
    return ((bits + 0x7FFF + lsb) >> 16) & 0xFFFF


def bf16_to_float32(bits: int) -> np.float32:
    return u32_to_float32((bits & 0xFFFF) << 16)


def sign_extend(value: int, width: int) -> int:
    value &= (1 << width) - 1
    sign = 1 << (width - 1)
    return value - (1 << width) if value & sign else value


def int_to_twos(value: int, width: int) -> int:
    return value & ((1 << width) - 1)


def fp8_e4m3fn_to_float32(bits: int) -> np.float32:
    bits &= 0xFF
    sign = -1.0 if bits & 0x80 else 1.0
    exp = (bits >> 3) & 0xF
    mant = bits & 0x7
    bias = 7
    if exp == 0:
        if mant == 0:
            return np.float32(math.copysign(0.0, sign))
        return np.float32(sign * (mant / 8.0) * (2.0 ** (1 - bias)))
    if exp == 0xF and mant == 0x7:
        return np.float32(np.nan)
    return np.float32(sign * (1.0 + mant / 8.0) * (2.0 ** (exp - bias)))


_FINITE_PAIRS = sorted(
    (float(fp8_e4m3fn_to_float32(bits)), bits)
    for bits in range(256)
    if not np.isnan(fp8_e4m3fn_to_float32(bits))
)
_FINITE_VALUES = [x[0] for x in _FINITE_PAIRS]


def float32_to_fp8_e4m3fn(value: float) -> int:
    x = float(np.float32(value))
    if math.isnan(x):
        return 0x7F
    if x == 0.0:
        return 0x80 if math.copysign(1.0, x) < 0 else 0x00
    x = max(_FINITE_VALUES[0], min(_FINITE_VALUES[-1], x))
    idx = bisect.bisect_left(_FINITE_VALUES, x)
    candidates = []
    for j in (idx - 1, idx):
        if 0 <= j < len(_FINITE_PAIRS):
            candidates.append(_FINITE_PAIRS[j])
    def key(pair):
        candidate, bits = pair
        return (abs(candidate - x), bits & 1, bits)
    return min(candidates, key=key)[1]


def decode_operand(raw: int, fmt: OperandFormat) -> np.float32:
    if fmt == OperandFormat.INT4:
        return np.float32(sign_extend(raw, 4))
    if fmt == OperandFormat.INT8:
        return np.float32(sign_extend(raw, 8))
    if fmt == OperandFormat.FP8_E4M3FN:
        return fp8_e4m3fn_to_float32(raw)
    if fmt == OperandFormat.BF16:
        return bf16_to_float32(raw)
    raise ValueError(fmt)


def encode_operand(value: float, fmt: OperandFormat) -> int:
    if fmt == OperandFormat.INT4:
        v = int(np.rint(value))
        if not -8 <= v <= 7:
            raise ValueError("INT4 out of range")
        return int_to_twos(v, 4)
    if fmt == OperandFormat.INT8:
        v = int(np.rint(value))
        if not -128 <= v <= 127:
            raise ValueError("INT8 out of range")
        return int_to_twos(v, 8)
    if fmt == OperandFormat.FP8_E4M3FN:
        return float32_to_fp8_e4m3fn(value)
    if fmt == OperandFormat.BF16:
        return float32_to_bf16(value)
    raise ValueError(fmt)


def fp32_mac(acc: float, a: float, b: float) -> np.float32:
    product = np.float32(np.float32(a) * np.float32(b))
    return np.float32(np.float32(acc) + product)


def native_mixed_dot(
    lhs: Iterable[int],
    rhs: Iterable[int],
    lhs_fmt: OperandFormat,
    rhs_fmt: OperandFormat,
) -> np.float32:
    acc = np.float32(0.0)
    for a_raw, b_raw in zip(lhs, rhs):
        acc = fp32_mac(acc, decode_operand(a_raw, lhs_fmt), decode_operand(b_raw, rhs_fmt))
    return acc


def converted_mixed_dot(
    lhs: Iterable[int],
    rhs: Iterable[int],
    lhs_fmt: OperandFormat,
    rhs_fmt: OperandFormat,
    target_fmt: OperandFormat,
) -> np.float32:
    acc = np.float32(0.0)
    for a_raw, b_raw in zip(lhs, rhs):
        a = decode_operand(a_raw, lhs_fmt)
        b = decode_operand(b_raw, rhs_fmt)
        aq = decode_operand(encode_operand(a, target_fmt), target_fmt)
        bq = decode_operand(encode_operand(b, target_fmt), target_fmt)
        acc = fp32_mac(acc, aq, bq)
    return acc


@dataclass(frozen=True)
class ConversionCoverage:
    source_format: str
    target_format: str
    total_codes: int
    exact_codes: int
    exact_fraction: float
    max_abs_error: float
    rms_error: float


def conversion_coverage(
    source_fmt: OperandFormat,
    target_fmt: OperandFormat,
) -> ConversionCoverage:
    values = range(-8, 8) if source_fmt == OperandFormat.INT4 else range(-128, 128)
    errors = []
    exact = 0
    for value in values:
        decoded = float(
            decode_operand(encode_operand(float(value), target_fmt), target_fmt)
        )
        error = decoded - value
        errors.append(error)
        exact += int(error == 0.0)
    return ConversionCoverage(
        source_format=source_fmt.name,
        target_format=target_fmt.name,
        total_codes=len(errors),
        exact_codes=exact,
        exact_fraction=exact / len(errors),
        max_abs_error=max(abs(x) for x in errors),
        rms_error=math.sqrt(sum(x * x for x in errors) / len(errors)),
    )

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable, Sequence

import numpy as np


class V2Mode(IntEnum):
    I4_I8 = 0
    I8_I8 = 1
    FP8_FP8 = 2
    BF16_BF16 = 3
    I4_FP8 = 4
    I4_BF16 = 5
    I8_BF16 = 6


PRODUCTS_PER_CYCLE: dict[V2Mode, int] = {
    V2Mode.I4_I8: 8,
    V2Mode.I8_I8: 4,
    V2Mode.FP8_FP8: 16,
    V2Mode.BF16_BF16: 4,
    V2Mode.I4_FP8: 16,
    V2Mode.I4_BF16: 8,
    V2Mode.I8_BF16: 4,
}

ITEMS_PER_LANE: dict[V2Mode, int] = {
    V2Mode.I4_I8: 2,
    V2Mode.I8_I8: 1,
    V2Mode.FP8_FP8: 4,
    V2Mode.BF16_BF16: 1,
    V2Mode.I4_FP8: 4,
    V2Mode.I4_BF16: 2,
    V2Mode.I8_BF16: 1,
}


def sign_extend(raw: int, width: int) -> int:
    raw &= (1 << width) - 1
    sign = 1 << (width - 1)
    return raw - (1 << width) if raw & sign else raw


def twos(value: int, width: int) -> int:
    return value & ((1 << width) - 1)


def mul4x4_unsigned(a: int, b: int) -> int:
    if not (0 <= a < 16 and 0 <= b < 16):
        raise ValueError((a, b))
    return a * b


def compose_u4_u8(a4: int, b8: int) -> tuple[int, tuple[int, int]]:
    p0 = mul4x4_unsigned(a4 & 0xF, b8 & 0xF)
    p1 = mul4x4_unsigned(a4 & 0xF, (b8 >> 4) & 0xF)
    return p0 + (p1 << 4), (p0, p1)


def compose_u8_u8(a8: int, b8: int) -> tuple[int, tuple[int, int, int, int]]:
    a0, a1 = a8 & 0xF, (a8 >> 4) & 0xF
    b0, b1 = b8 & 0xF, (b8 >> 4) & 0xF
    p00 = mul4x4_unsigned(a0, b0)
    p01 = mul4x4_unsigned(a0, b1)
    p10 = mul4x4_unsigned(a1, b0)
    p11 = mul4x4_unsigned(a1, b1)
    return p00 + ((p01 + p10) << 4) + (p11 << 8), (p00, p01, p10, p11)


def f32_from_bits(bits: int) -> np.float32:
    return np.float32(struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0])


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", float(np.float32(value))))[0]


def bf16_to_float(raw: int) -> np.float32:
    return f32_from_bits((raw & 0xFFFF) << 16)


def float_to_bf16(value: float, *, flush_subnormal: bool = True) -> int:
    bits = f32_bits(value)
    exp = (bits >> 23) & 0xFF
    frac = bits & 0x7FFFFF
    sign = (bits >> 31) & 1
    if exp == 0xFF:
        return (sign << 15) | 0x7F80 | (0x40 if frac else 0)
    lsb = (bits >> 16) & 1
    rounded = (bits + 0x7FFF + lsb) & 0xFFFFFFFF
    bf = (rounded >> 16) & 0xFFFF
    if flush_subnormal and ((bf >> 7) & 0xFF) == 0:
        return (bf >> 15) << 15
    return bf


def bf16_add(a_raw: int, b_raw: int, *, flush_subnormal: bool = True) -> int:
    with np.errstate(over="ignore", invalid="ignore"):
        value = np.float32(bf16_to_float(a_raw) + bf16_to_float(b_raw))
    return float_to_bf16(float(value), flush_subnormal=flush_subnormal)


def fp8_e4m3fn_to_float(raw: int) -> np.float32:
    raw &= 0xFF
    sign = -1.0 if raw & 0x80 else 1.0
    exp = (raw >> 3) & 0xF
    mant = raw & 0x7
    if exp == 0:
        if mant == 0:
            return np.float32(math.copysign(0.0, sign))
        return np.float32(sign * mant * (2.0 ** -9))
    if exp == 0xF and mant == 0x7:
        return np.float32(np.nan)
    return np.float32(sign * (8 + mant) * (2.0 ** (exp - 10)))


@dataclass(frozen=True)
class BinaryOperand:
    sign: int
    significand: int
    scale_exp: int
    is_zero: bool = False
    is_inf: bool = False
    is_nan: bool = False


def decode_fp8(raw: int) -> BinaryOperand:
    raw &= 0xFF
    sign = (raw >> 7) & 1
    exp = (raw >> 3) & 0xF
    mant = raw & 0x7
    if exp == 0 and mant == 0:
        return BinaryOperand(sign, 0, 0, is_zero=True)
    if exp == 0xF and mant == 0x7:
        return BinaryOperand(sign, 0, 0, is_nan=True)
    if exp == 0:
        return BinaryOperand(sign, mant, -9)
    return BinaryOperand(sign, 8 + mant, exp - 10)


def decode_bf16(raw: int) -> BinaryOperand:
    raw &= 0xFFFF
    sign = (raw >> 15) & 1
    exp = (raw >> 7) & 0xFF
    mant = raw & 0x7F
    if exp == 0 and mant == 0:
        return BinaryOperand(sign, 0, 0, is_zero=True)
    if exp == 0xFF:
        return BinaryOperand(sign, 0, 0, is_inf=(mant == 0), is_nan=(mant != 0))
    if exp == 0:
        return BinaryOperand(sign, mant, -133)
    return BinaryOperand(sign, 128 + mant, exp - 134)


def raw_product_to_bf16(
    sign: int,
    raw_product: int,
    scale_exp: int,
    *,
    is_zero: bool = False,
    is_inf: bool = False,
    is_nan: bool = False,
    flush_subnormal: bool = True,
) -> int:
    """Narrow (<=16-bit) product normalization directly into BF16."""
    sign &= 1
    raw_product &= 0xFFFF
    if is_nan:
        return (sign << 15) | 0x7FC0
    if is_inf:
        return (sign << 15) | 0x7F80
    if is_zero or raw_product == 0:
        return sign << 15

    msb = raw_product.bit_length() - 1
    unbiased_exp = scale_exp + msb
    if unbiased_exp > 127:
        return (sign << 15) | 0x7F80
    if unbiased_exp < -126:
        if flush_subnormal:
            return sign << 15
        # Exact BF16 subnormal quantization through float32 is only a model fallback.
        value = math.ldexp(float(raw_product), scale_exp)
        if sign:
            value = -value
        return float_to_bf16(value, flush_subnormal=False)

    if msb > 7:
        shift = msb - 7
        sig8 = raw_product >> shift
        guard = (raw_product >> (shift - 1)) & 1
        sticky = 1 if shift > 1 and (raw_product & ((1 << (shift - 1)) - 1)) else 0
        round_up = guard and (sticky or (sig8 & 1))
        sig9 = sig8 + int(round_up)
        if sig9 >= 0x100:
            sig8 = sig9 >> 1
            unbiased_exp += 1
            if unbiased_exp > 127:
                return (sign << 15) | 0x7F80
        else:
            sig8 = sig9
    else:
        sig8 = raw_product << (7 - msb)

    biased_exp = unbiased_exp + 127
    return (sign << 15) | ((biased_exp & 0xFF) << 7) | (sig8 & 0x7F)


def product_to_bf16(a: BinaryOperand, b: BinaryOperand, raw_product: int) -> int:
    invalid = (a.is_zero and b.is_inf) or (b.is_zero and a.is_inf)
    return raw_product_to_bf16(
        a.sign ^ b.sign,
        raw_product,
        a.scale_exp + b.scale_exp,
        is_zero=a.is_zero or b.is_zero,
        is_inf=(a.is_inf or b.is_inf) and not invalid,
        is_nan=a.is_nan or b.is_nan or invalid,
    )


def integer_operand(raw: int, width: int) -> BinaryOperand:
    value = sign_extend(raw, width)
    return BinaryOperand(int(value < 0), abs(value), 0, is_zero=(value == 0))


def lane_reduce_bf16(items: Sequence[int], accumulator: int = 0) -> int:
    padded = list(items[:4]) + [0] * (4 - len(items))
    pair01 = bf16_add(padded[0], padded[1])
    pair23 = bf16_add(padded[2], padded[3])
    lane_sum = bf16_add(pair01, pair23)
    return bf16_add(accumulator, lane_sum)


@dataclass(frozen=True)
class CycleResult:
    mode: V2Mode
    int_lane_sums: tuple[int, int, int, int]
    bf16_lane_items: tuple[tuple[int, int, int, int], ...]
    brick_products: tuple[int, ...]


class FusionMul16V2Model:
    BRICKS = 16

    def run_cycle(self, mode: V2Mode, lhs: Sequence[int], rhs: Sequence[int]) -> CycleResult:
        required = PRODUCTS_PER_CYCLE[mode]
        if len(lhs) < required or len(rhs) < required:
            raise ValueError(f"{mode.name} needs {required} inputs")

        int_products: list[int] = []
        fp_products: list[int] = []
        bricks: list[int] = []

        if mode == V2Mode.I4_I8:
            for a_raw, b_raw in zip(lhs[:8], rhs[:8]):
                a = sign_extend(a_raw, 4)
                b = sign_extend(b_raw, 8)
                mag, parts = compose_u4_u8(abs(a), abs(b))
                bricks.extend(parts)
                int_products.append(-mag if (a < 0) ^ (b < 0) else mag)
        elif mode == V2Mode.I8_I8:
            for a_raw, b_raw in zip(lhs[:4], rhs[:4]):
                a = sign_extend(a_raw, 8)
                b = sign_extend(b_raw, 8)
                mag, parts = compose_u8_u8(abs(a), abs(b))
                bricks.extend(parts)
                int_products.append(-mag if (a < 0) ^ (b < 0) else mag)
        elif mode == V2Mode.FP8_FP8:
            for a_raw, b_raw in zip(lhs[:16], rhs[:16]):
                a, b = decode_fp8(a_raw), decode_fp8(b_raw)
                raw = mul4x4_unsigned(a.significand, b.significand)
                bricks.append(raw)
                fp_products.append(product_to_bf16(a, b, raw))
        elif mode == V2Mode.BF16_BF16:
            for a_raw, b_raw in zip(lhs[:4], rhs[:4]):
                a, b = decode_bf16(a_raw), decode_bf16(b_raw)
                raw, parts = compose_u8_u8(a.significand, b.significand)
                bricks.extend(parts)
                fp_products.append(product_to_bf16(a, b, raw))
        elif mode == V2Mode.I4_FP8:
            for a_raw, b_raw in zip(lhs[:16], rhs[:16]):
                a, b = integer_operand(a_raw, 4), decode_fp8(b_raw)
                raw = mul4x4_unsigned(a.significand, b.significand)
                bricks.append(raw)
                fp_products.append(product_to_bf16(a, b, raw))
        elif mode == V2Mode.I4_BF16:
            for a_raw, b_raw in zip(lhs[:8], rhs[:8]):
                a, b = integer_operand(a_raw, 4), decode_bf16(b_raw)
                raw, parts = compose_u4_u8(a.significand, b.significand)
                bricks.extend(parts)
                fp_products.append(product_to_bf16(a, b, raw))
        elif mode == V2Mode.I8_BF16:
            for a_raw, b_raw in zip(lhs[:4], rhs[:4]):
                a, b = integer_operand(a_raw, 8), decode_bf16(b_raw)
                raw, parts = compose_u8_u8(a.significand, b.significand)
                bricks.extend(parts)
                fp_products.append(product_to_bf16(a, b, raw))
        else:
            raise ValueError(mode)

        if len(bricks) != self.BRICKS:
            raise AssertionError((mode, len(bricks)))

        int_lanes = [0, 0, 0, 0]
        fp_lanes = [[0, 0, 0, 0] for _ in range(4)]
        items = ITEMS_PER_LANE[mode]
        if mode in (V2Mode.I4_I8, V2Mode.I8_I8):
            for lane in range(4):
                start = lane * items
                int_lanes[lane] = sum(int_products[start:start + items])
        else:
            for lane in range(4):
                start = lane * items
                for item, value in enumerate(fp_products[start:start + items]):
                    fp_lanes[lane][item] = value

        return CycleResult(
            mode=mode,
            int_lane_sums=tuple(int_lanes),
            bf16_lane_items=tuple(tuple(x) for x in fp_lanes),
            brick_products=tuple(bricks),
        )


def int16_magnitude_via_four_u8_products(a: int, b: int) -> int:
    """Reference for the optional 4-cycle INT16 emulation outside the main mode table."""
    sign = (a < 0) ^ (b < 0)
    am, bm = abs(a), abs(b)
    a0, a1 = am & 0xFF, (am >> 8) & 0xFF
    b0, b1 = bm & 0xFF, (bm >> 8) & 0xFF
    value = a0 * b0 + ((a0 * b1 + a1 * b0) << 8) + ((a1 * b1) << 16)
    return -value if sign else value

INT_VISIBLE_LATENCY = 4
FP_VISIBLE_LATENCY = 7


class PipelineScheduleModel:
    """Control-only latency/II model for the registered v2 architecture."""

    def __init__(self) -> None:
        self.mode: V2Mode | None = None
        self.cycle = 0
        self.pending: list[tuple[int, V2Mode, int]] = []

    def configure(self, mode: V2Mode) -> None:
        if self.pending:
            raise RuntimeError("configuration change requires an empty pipeline")
        self.mode = mode

    def issue(self, token: int) -> None:
        if self.mode is None:
            raise RuntimeError("mode must be configured before data")
        latency = INT_VISIBLE_LATENCY if self.mode in (V2Mode.I4_I8, V2Mode.I8_I8) else FP_VISIBLE_LATENCY
        self.pending.append((self.cycle + latency, self.mode, token))

    def step(self) -> list[tuple[V2Mode, int]]:
        self.cycle += 1
        ready = [(mode, token) for when, mode, token in self.pending if when == self.cycle]
        self.pending = [entry for entry in self.pending if entry[0] != self.cycle]
        return ready

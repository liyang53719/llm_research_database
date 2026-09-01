from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable, Sequence

import numpy as np


class FusionMode(IntEnum):
    I4_I4 = 0
    I4_I8 = 1
    I8_I8 = 2
    I16_I16 = 3
    FP8_FP8 = 4
    BF16_BF16 = 5
    I4_FP8 = 6
    I8_FP8 = 7
    I4_BF16 = 8
    I8_BF16 = 9


PRODUCTS_PER_CYCLE: dict[FusionMode, int] = {
    FusionMode.I4_I4: 16,
    FusionMode.I4_I8: 8,
    FusionMode.I8_I8: 4,
    FusionMode.I16_I16: 1,
    FusionMode.FP8_FP8: 16,
    FusionMode.BF16_BF16: 4,
    FusionMode.I4_FP8: 16,
    FusionMode.I8_FP8: 8,
    FusionMode.I4_BF16: 8,
    FusionMode.I8_BF16: 4,
}


BRICKS_PER_PRODUCT: dict[FusionMode, int] = {
    mode: 16 // count for mode, count in PRODUCTS_PER_CYCLE.items()
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


def compose_u16_u16(a16: int, b16: int) -> tuple[int, tuple[int, ...]]:
    partials: list[int] = []
    total = 0
    for ai in range(4):
        an = (a16 >> (4 * ai)) & 0xF
        for bi in range(4):
            bn = (b16 >> (4 * bi)) & 0xF
            p = mul4x4_unsigned(an, bn)
            partials.append(p)
            total += p << (4 * (ai + bi))
    return total, tuple(partials)


def signed_product_from_unsigned(a: int, aw: int, b: int, bw: int) -> int:
    av = sign_extend(a, aw)
    bv = sign_extend(b, bw)
    return av * bv


def _f32_from_bits(bits: int) -> np.float32:
    return np.float32(struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0])


def _f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", float(np.float32(value))))[0]


def bf16_to_float(raw: int) -> np.float32:
    return _f32_from_bits((raw & 0xFFFF) << 16)


def float_to_bf16(value: float) -> int:
    bits = _f32_bits(value)
    lsb = (bits >> 16) & 1
    return ((bits + 0x7FFF + lsb) >> 16) & 0xFFFF


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


def raw_binary_product_to_float(a: BinaryOperand, b: BinaryOperand, raw_product: int) -> np.float32:
    sign = -1.0 if a.sign ^ b.sign else 1.0
    if a.is_nan or b.is_nan or ((a.is_zero or b.is_zero) and (a.is_inf or b.is_inf)):
        return np.float32(np.nan)
    if a.is_inf or b.is_inf:
        return np.float32(math.copysign(math.inf, sign))
    if a.is_zero or b.is_zero or raw_product == 0:
        return np.float32(math.copysign(0.0, sign))
    with np.errstate(over="ignore", invalid="ignore"):
        return np.float32(sign * math.ldexp(raw_product, a.scale_exp + b.scale_exp))


def fp8_product(raw_a: int, raw_b: int) -> tuple[np.float32, tuple[int, ...]]:
    a = decode_fp8(raw_a)
    b = decode_fp8(raw_b)
    p = mul4x4_unsigned(a.significand, b.significand)
    return raw_binary_product_to_float(a, b, p), (p,)


def bf16_product(raw_a: int, raw_b: int) -> tuple[np.float32, tuple[int, ...]]:
    a = decode_bf16(raw_a)
    b = decode_bf16(raw_b)
    p, partials = compose_u8_u8(a.significand, b.significand)
    return raw_binary_product_to_float(a, b, p), partials


def mixed_integer_float_product(int_raw: int, int_width: int, fp_raw: int, fp_kind: str) -> tuple[np.float32, tuple[int, ...]]:
    iv = sign_extend(int_raw, int_width)
    sign = 1 if iv < 0 else 0
    magnitude = abs(iv)
    fp = decode_fp8(fp_raw) if fp_kind == "fp8" else decode_bf16(fp_raw)
    integer = BinaryOperand(sign=sign, significand=magnitude, scale_exp=0, is_zero=(magnitude == 0))
    if int_width == 4 and fp_kind == "fp8":
        raw = mul4x4_unsigned(magnitude, fp.significand)
        partials = (raw,)
    elif int_width == 8 and fp_kind == "fp8":
        raw, partials = compose_u4_u8(fp.significand, magnitude)
    elif int_width == 4 and fp_kind == "bf16":
        raw, partials = compose_u4_u8(magnitude, fp.significand)
    elif int_width == 8 and fp_kind == "bf16":
        raw, partials = compose_u8_u8(magnitude, fp.significand)
    else:
        raise ValueError((int_width, fp_kind))
    return raw_binary_product_to_float(integer, fp, raw), tuple(partials)


@dataclass(frozen=True)
class FusionResult:
    mode: FusionMode
    products: tuple[int | np.float32, ...]
    brick_products: tuple[int, ...]

    @property
    def products_per_cycle(self) -> int:
        return len(self.products)

    @property
    def brick_count(self) -> int:
        return len(self.brick_products)


class FusionMul16Model:
    BRICKS = 16

    def run(self, mode: FusionMode, lhs: Sequence[int], rhs: Sequence[int]) -> FusionResult:
        required = PRODUCTS_PER_CYCLE[mode]
        if len(lhs) < required or len(rhs) < required:
            raise ValueError(f"{mode.name} requires {required} logical inputs")

        products: list[int | np.float32] = []
        bricks: list[int] = []

        if mode == FusionMode.I4_I4:
            for a, b in zip(lhs[:16], rhs[:16]):
                av, bv = sign_extend(a, 4), sign_extend(b, 4)
                p = mul4x4_unsigned(abs(av), abs(bv))
                bricks.append(p)
                products.append(-p if (av < 0) ^ (bv < 0) else p)
        elif mode == FusionMode.I4_I8:
            for a, b in zip(lhs[:8], rhs[:8]):
                av, bv = sign_extend(a, 4), sign_extend(b, 8)
                mag, parts = compose_u4_u8(abs(av), abs(bv))
                bricks.extend(parts)
                products.append(-mag if (av < 0) ^ (bv < 0) else mag)
        elif mode == FusionMode.I8_I8:
            for a, b in zip(lhs[:4], rhs[:4]):
                av, bv = sign_extend(a, 8), sign_extend(b, 8)
                mag, parts = compose_u8_u8(abs(av), abs(bv))
                bricks.extend(parts)
                products.append(-mag if (av < 0) ^ (bv < 0) else mag)
        elif mode == FusionMode.I16_I16:
            av, bv = sign_extend(lhs[0], 16), sign_extend(rhs[0], 16)
            mag, parts = compose_u16_u16(abs(av), abs(bv))
            bricks.extend(parts)
            products.append(-mag if (av < 0) ^ (bv < 0) else mag)
        elif mode == FusionMode.FP8_FP8:
            for a, b in zip(lhs[:16], rhs[:16]):
                value, parts = fp8_product(a, b)
                products.append(value)
                bricks.extend(parts)
        elif mode == FusionMode.BF16_BF16:
            for a, b in zip(lhs[:4], rhs[:4]):
                value, parts = bf16_product(a, b)
                products.append(value)
                bricks.extend(parts)
        elif mode == FusionMode.I4_FP8:
            for a, b in zip(lhs[:16], rhs[:16]):
                value, parts = mixed_integer_float_product(a, 4, b, "fp8")
                products.append(value)
                bricks.extend(parts)
        elif mode == FusionMode.I8_FP8:
            for a, b in zip(lhs[:8], rhs[:8]):
                value, parts = mixed_integer_float_product(a, 8, b, "fp8")
                products.append(value)
                bricks.extend(parts)
        elif mode == FusionMode.I4_BF16:
            for a, b in zip(lhs[:8], rhs[:8]):
                value, parts = mixed_integer_float_product(a, 4, b, "bf16")
                products.append(value)
                bricks.extend(parts)
        elif mode == FusionMode.I8_BF16:
            for a, b in zip(lhs[:4], rhs[:4]):
                value, parts = mixed_integer_float_product(a, 8, b, "bf16")
                products.append(value)
                bricks.extend(parts)
        else:
            raise ValueError(mode)

        if len(bricks) != self.BRICKS:
            raise AssertionError((mode, len(bricks)))
        return FusionResult(mode, tuple(products), tuple(bricks))


def lane_groups(result: FusionResult) -> tuple[tuple[int | np.float32, ...], ...]:
    count = result.products_per_cycle
    if count == 16:
        width = 4
    elif count == 8:
        width = 2
    elif count == 4:
        width = 1
    elif count == 1:
        return (result.products, tuple(), tuple(), tuple())
    else:
        raise ValueError(count)
    return tuple(tuple(result.products[lane * width:(lane + 1) * width]) for lane in range(4))

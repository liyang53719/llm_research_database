from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable, Sequence

import numpy as np


class Mode(IntEnum):
    I4_I8 = 0
    I8_I8 = 1
    FP8_FP8 = 2
    BF16_BF16 = 3
    I4_FP8 = 4
    I4_BF16 = 5
    I8_BF16 = 6


MODE_NAMES = {
    Mode.I4_I8: "i4_i8",
    Mode.I8_I8: "i8_i8",
    Mode.FP8_FP8: "fp8_fp8",
    Mode.BF16_BF16: "bf16_bf16",
    Mode.I4_FP8: "i4_fp8",
    Mode.I4_BF16: "i4_bf16",
    Mode.I8_BF16: "i8_bf16",
}

PRODUCTS_PER_CYCLE = {
    Mode.I4_I8: 8,
    Mode.I8_I8: 4,
    Mode.FP8_FP8: 16,
    Mode.BF16_BF16: 4,
    Mode.I4_FP8: 16,
    Mode.I4_BF16: 8,
    Mode.I8_BF16: 4,
}

ITEMS_PER_LANE = {
    Mode.I4_I8: 2,
    Mode.I8_I8: 1,
    Mode.FP8_FP8: 4,
    Mode.BF16_BF16: 1,
    Mode.I4_FP8: 4,
    Mode.I4_BF16: 2,
    Mode.I8_BF16: 1,
}

INT_MODES = {Mode.I4_I8, Mode.I8_I8}
FP_MODES = set(Mode) - INT_MODES


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", float(np.float32(value))))[0]


def f32_from_bits(bits: int) -> np.float32:
    return np.float32(struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0])


def bf16_to_float(raw: int) -> np.float32:
    return f32_from_bits((int(raw) & 0xFFFF) << 16)


def float_to_bf16_rne(value: float, *, ftz: bool = True) -> int:
    """RNE float32->BF16 used by the v3 reduction/accumulator model."""
    bits = f32_bits(value)
    sign = (bits >> 31) & 1
    exp = (bits >> 23) & 0xFF
    frac = bits & 0x7FFFFF
    if exp == 0xFF:
        return (sign << 15) | 0x7F80 | (0x40 if frac else 0)
    lsb = (bits >> 16) & 1
    rounded = (bits + 0x7FFF + lsb) & 0xFFFFFFFF
    bf = (rounded >> 16) & 0xFFFF
    if ftz and ((bf >> 7) & 0xFF) == 0:
        return (bf >> 15) << 15
    return bf


def bf16_add_rne(a_raw: int, b_raw: int, *, ftz: bool = True) -> int:
    with np.errstate(over="ignore", invalid="ignore"):
        value = np.float32(bf16_to_float(a_raw) + bf16_to_float(b_raw))
    return float_to_bf16_rne(float(value), ftz=ftz)


def fp32_add_rne(a: np.float32, b: np.float32) -> np.float32:
    return np.float32(np.float32(a) + np.float32(b))


def sign_extend(raw: int, width: int) -> int:
    raw &= (1 << width) - 1
    sign = 1 << (width - 1)
    return raw - (1 << width) if raw & sign else raw


def twos(value: int, width: int) -> int:
    return int(value) & ((1 << width) - 1)


@dataclass(frozen=True)
class FPOperand:
    sign: int
    significand: int
    scale_exp: int
    is_zero: bool
    is_inf: bool
    is_nan: bool


def decode_fp8_e4m3fn(raw: int) -> FPOperand:
    raw &= 0xFF
    exponent = (raw >> 3) & 0xF
    fraction = raw & 0x7
    return FPOperand(
        sign=(raw >> 7) & 1,
        significand=fraction if exponent == 0 else 0x8 | fraction,
        scale_exp=-9 if exponent == 0 else exponent - 10,
        is_zero=exponent == 0 and fraction == 0,
        is_inf=False,
        is_nan=exponent == 0xF and fraction == 0x7,
    )


def decode_bf16(raw: int) -> FPOperand:
    raw &= 0xFFFF
    exponent = (raw >> 7) & 0xFF
    fraction = raw & 0x7F
    return FPOperand(
        sign=(raw >> 15) & 1,
        significand=fraction if exponent == 0 else 0x80 | fraction,
        scale_exp=-133 if exponent == 0 else exponent - 134,
        is_zero=exponent == 0 and fraction == 0,
        is_inf=exponent == 0xFF and fraction == 0,
        is_nan=exponent == 0xFF and fraction != 0,
    )


def raw16_to_bf16_contract(
    sign: int,
    raw: int,
    scale_exp: int,
    *,
    zero: bool = False,
    inf: bool = False,
    nan: bool = False,
    support_specials: bool = True,
) -> int:
    """Bit-exact model of fusion_mul16_v4_raw16_to_bf16_rne.sv.

    This is a low-area RNE/FTZ-before-rounding contract. BF16 subnormal outputs
    are flushed to signed zero. NaN is canonicalized to fraction 0x40.
    """
    sign &= 1
    raw &= 0xFFFF
    if support_specials and nan:
        return (sign << 15) | 0x7FC0
    if support_specials and inf:
        return (sign << 15) | 0x7F80
    if zero or raw == 0:
        return sign << 15

    msb_index = raw.bit_length() - 1
    unbiased_exp = int(scale_exp) + msb_index
    if unbiased_exp > 127:
        return (sign << 15) | 0x7F80
    if unbiased_exp < -126:
        return sign << 15

    if msb_index > 7:
        shift = msb_index - 7
        significand8 = raw >> shift
        guard = (raw >> (shift - 1)) & 1
        sticky = bool(raw & ((1 << (shift - 1)) - 1)) if shift > 1 else False
        round_up = bool(guard and (sticky or (significand8 & 1)))
        rounded = significand8 + int(round_up)
        if rounded & 0x100:
            significand8 = (rounded >> 1) & 0xFF
            unbiased_exp += 1
        else:
            significand8 = rounded & 0xFF
    else:
        significand8 = (raw << (7 - msb_index)) & 0xFF

    if unbiased_exp > 127:
        return (sign << 15) | 0x7F80
    return (sign << 15) | ((unbiased_exp + 127) << 7) | (significand8 & 0x7F)


def _fp_product(a: FPOperand, b: FPOperand, *, support_specials: bool) -> int:
    sign = a.sign ^ b.sign
    zero = a.is_zero or b.is_zero
    inf = (a.is_inf or b.is_inf) and not zero
    nan = a.is_nan or b.is_nan or (zero and (a.is_inf or b.is_inf))
    return raw16_to_bf16_contract(
        sign,
        a.significand * b.significand,
        a.scale_exp + b.scale_exp,
        zero=zero,
        inf=inf,
        nan=nan,
        support_specials=support_specials,
    )


def scalar_product(mode: Mode, lhs_raw: int, rhs_raw: int, *, support_specials: bool = True) -> int:
    mode = Mode(mode)
    if mode == Mode.I4_I8:
        return sign_extend(lhs_raw, 4) * sign_extend(rhs_raw, 8)
    if mode == Mode.I8_I8:
        return sign_extend(lhs_raw, 8) * sign_extend(rhs_raw, 8)
    if mode == Mode.FP8_FP8:
        return _fp_product(decode_fp8_e4m3fn(lhs_raw), decode_fp8_e4m3fn(rhs_raw), support_specials=support_specials)
    if mode == Mode.BF16_BF16:
        return _fp_product(decode_bf16(lhs_raw), decode_bf16(rhs_raw), support_specials=support_specials)
    if mode == Mode.I4_FP8:
        lhs = FPOperand(int(sign_extend(lhs_raw, 4) < 0), abs(sign_extend(lhs_raw, 4)), 0, sign_extend(lhs_raw, 4) == 0, False, False)
        return _fp_product(lhs, decode_fp8_e4m3fn(rhs_raw), support_specials=support_specials)
    if mode == Mode.I4_BF16:
        lhs = FPOperand(int(sign_extend(lhs_raw, 4) < 0), abs(sign_extend(lhs_raw, 4)), 0, sign_extend(lhs_raw, 4) == 0, False, False)
        return _fp_product(lhs, decode_bf16(rhs_raw), support_specials=support_specials)
    if mode == Mode.I8_BF16:
        lhs = FPOperand(int(sign_extend(lhs_raw, 8) < 0), abs(sign_extend(lhs_raw, 8)), 0, sign_extend(lhs_raw, 8) == 0, False, False)
        return _fp_product(lhs, decode_bf16(rhs_raw), support_specials=support_specials)
    raise ValueError(mode)


def unpack_fields(word: int, width: int, count: int) -> list[int]:
    mask = (1 << width) - 1
    return [(int(word) >> (i * width)) & mask for i in range(count)]


def pack_fields(values: Sequence[int], width: int) -> int:
    mask = (1 << width) - 1
    word = 0
    for i, value in enumerate(values):
        word |= (int(value) & mask) << (i * width)
    return word


def products_from_packed(
    mode: Mode,
    lhs_packed: int,
    rhs_packed: int,
    *,
    support_specials: bool = True,
) -> list[list[int]]:
    """Return four lanes, each lane containing up to four scalar products."""
    mode = Mode(mode)
    lanes: list[list[int]] = [[] for _ in range(4)]
    if mode == Mode.I4_I8:
        lhs = unpack_fields(lhs_packed, 4, 8)
        rhs = unpack_fields(rhs_packed, 8, 8)
        for i in range(8):
            lanes[i // 2].append(scalar_product(mode, lhs[i], rhs[i]))
    elif mode == Mode.I8_I8:
        lhs = unpack_fields(lhs_packed, 8, 4)
        rhs = unpack_fields(rhs_packed, 8, 4)
        for i in range(4):
            lanes[i].append(scalar_product(mode, lhs[i], rhs[i]))
    elif mode == Mode.FP8_FP8:
        lhs = unpack_fields(lhs_packed, 8, 16)
        rhs = unpack_fields(rhs_packed, 8, 16)
        for i in range(16):
            lanes[i // 4].append(scalar_product(mode, lhs[i], rhs[i], support_specials=support_specials))
    elif mode == Mode.BF16_BF16:
        lhs = unpack_fields(lhs_packed, 16, 4)
        rhs = unpack_fields(rhs_packed, 16, 4)
        for i in range(4):
            lanes[i].append(scalar_product(mode, lhs[i], rhs[i], support_specials=support_specials))
    elif mode == Mode.I4_FP8:
        lhs = unpack_fields(lhs_packed, 4, 16)
        rhs = unpack_fields(rhs_packed, 8, 16)
        for i in range(16):
            lanes[i // 4].append(scalar_product(mode, lhs[i], rhs[i], support_specials=support_specials))
    elif mode == Mode.I4_BF16:
        lhs = unpack_fields(lhs_packed, 4, 8)
        rhs = unpack_fields(rhs_packed, 16, 8)
        for i in range(8):
            lanes[i // 2].append(scalar_product(mode, lhs[i], rhs[i], support_specials=support_specials))
    elif mode == Mode.I8_BF16:
        lhs = unpack_fields(lhs_packed, 8, 4)
        rhs = unpack_fields(rhs_packed, 16, 4)
        for i in range(4):
            lanes[i].append(scalar_product(mode, lhs[i], rhs[i], support_specials=support_specials))
    return lanes


def bf16_tree4(items: Sequence[int]) -> int:
    padded = list(items[:4]) + [0] * max(0, 4 - len(items))
    return bf16_add_rne(
        bf16_add_rne(int(padded[0]), int(padded[1])),
        bf16_add_rne(int(padded[2]), int(padded[3])),
    )


def wrap_signed(value: int, width: int) -> int:
    value &= (1 << width) - 1
    return sign_extend(value, width)


@dataclass
class CycleResult:
    int_valid: bool
    fp_valid: bool
    int_acc: tuple[int, int, int, int]
    fp_acc: tuple[np.float32, np.float32, np.float32, np.float32]


class FusionMul16V4FunctionalModel:
    """Transaction-level model of the final arithmetic contract.

    Latency is deliberately excluded; the separate PipelineModel covers cycle
    alignment. `clear()` is a standalone control operation and consumes no data.
    """

    def __init__(self, *, int_acc_width: int = 48, support_specials: bool = True) -> None:
        self.int_acc_width = int_acc_width
        self.support_specials = support_specials
        self.int_acc = [0, 0, 0, 0]
        self.fp_acc = [np.float32(0.0)] * 4

    def clear(self) -> None:
        self.int_acc = [0, 0, 0, 0]
        self.fp_acc = [np.float32(0.0)] * 4

    def issue(self, mode: Mode, lhs_packed: int, rhs_packed: int) -> CycleResult:
        lanes = products_from_packed(mode, lhs_packed, rhs_packed, support_specials=self.support_specials)
        if mode in INT_MODES:
            for lane in range(4):
                self.int_acc[lane] = wrap_signed(self.int_acc[lane] + sum(lanes[lane]), self.int_acc_width)
            return CycleResult(True, False, tuple(self.int_acc), tuple(self.fp_acc))
        for lane in range(4):
            lane_sum = bf16_tree4(lanes[lane])
            self.fp_acc[lane] = fp32_add_rne(self.fp_acc[lane], bf16_to_float(lane_sum))
        return CycleResult(False, True, tuple(self.int_acc), tuple(self.fp_acc))


@dataclass(frozen=True)
class PipelineEvent:
    cycle: int
    int_valid: bool
    fp_valid: bool
    int_last: bool
    fp_last: bool
    clear_done: bool


class PipelineModel:
    INT_LATENCY = 4
    FP_LATENCY = 7
    CLEAR_LATENCY = 7

    def __init__(self) -> None:
        self.pending: list[PipelineEvent] = []
        self.cycle = 0

    def issue_data(self, mode: Mode, *, last: bool = False) -> None:
        due = self.cycle + (self.INT_LATENCY if mode in INT_MODES else self.FP_LATENCY)
        self.pending.append(PipelineEvent(due, mode in INT_MODES, mode in FP_MODES,
                                          last and mode in INT_MODES, last and mode in FP_MODES, False))

    def issue_clear(self) -> None:
        self.pending.append(PipelineEvent(self.cycle + self.CLEAR_LATENCY, False, False, False, False, True))

    def tick(self) -> list[PipelineEvent]:
        self.cycle += 1
        ready = [event for event in self.pending if event.cycle == self.cycle]
        self.pending = [event for event in self.pending if event.cycle != self.cycle]
        return ready

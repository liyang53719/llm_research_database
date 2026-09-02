from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable, Sequence

import numpy as np


class AccumStyle(IntEnum):
    FULL_BF16 = 0
    BF16_TREE_FP32_RECURRENT = 1
    BF16_BLOCK64_FP32_CHECKPOINT = 2


def f32_bits(value: float) -> int:
    return struct.unpack('<I', struct.pack('<f', float(np.float32(value))))[0]


def f32_from_bits(bits: int) -> np.float32:
    return np.float32(struct.unpack('<f', struct.pack('<I', bits & 0xFFFFFFFF))[0])


def float_to_bf16(value: float, *, flush_subnormal: bool = True) -> int:
    """IEEE-like RNE conversion to BF16 with optional FTZ, matching v2."""
    bits = f32_bits(value)
    sign = (bits >> 31) & 1
    exp = (bits >> 23) & 0xFF
    frac = bits & 0x7FFFFF
    if exp == 0xFF:
        return (sign << 15) | 0x7F80 | (0x40 if frac else 0)
    lsb = (bits >> 16) & 1
    rounded = (bits + 0x7FFF + lsb) & 0xFFFFFFFF
    bf16 = (rounded >> 16) & 0xFFFF
    if flush_subnormal and ((bf16 >> 7) & 0xFF) == 0:
        return (bf16 >> 15) << 15
    return bf16


def bf16_to_float(raw: int) -> np.float32:
    return f32_from_bits((raw & 0xFFFF) << 16)


def bf16_to_fp32_bits(raw: int) -> int:
    return (raw & 0xFFFF) << 16


def bf16_add(a_raw: int, b_raw: int, *, flush_subnormal: bool = True) -> int:
    with np.errstate(over='ignore', invalid='ignore'):
        value = np.float32(bf16_to_float(a_raw) + bf16_to_float(b_raw))
    return float_to_bf16(float(value), flush_subnormal=flush_subnormal)


def fp32_add(a: np.float32, b: np.float32) -> np.float32:
    return np.float32(np.float32(a) + np.float32(b))


def quantize_bf16_array(values: np.ndarray, *, flush_subnormal: bool = True) -> np.ndarray:
    values = np.asarray(values, dtype=np.float32)
    bits = values.view(np.uint32)
    lsb = (bits >> 16) & np.uint32(1)
    rounded = bits + np.uint32(0x7FFF) + lsb
    bf = (rounded >> 16).astype(np.uint16)
    if flush_subnormal:
        exp = (bf >> np.uint16(7)) & np.uint16(0xFF)
        bf = np.where(exp == 0, bf & np.uint16(0x8000), bf).astype(np.uint16)
    return bf


def bf16_array_to_float(values: np.ndarray) -> np.ndarray:
    return (np.asarray(values, dtype=np.uint16).astype(np.uint32) << 16).view(np.float32)


def bf16_tree4(items: Sequence[int]) -> int:
    """The v2/v3 BF16 pair/lane reduction order."""
    padded = list(items[:4]) + [0] * max(0, 4 - len(items))
    s01 = bf16_add(int(padded[0]), int(padded[1]))
    s23 = bf16_add(int(padded[2]), int(padded[3]))
    return bf16_add(s01, s23)


def product_bits_from_quantized_inputs(a_bits: np.ndarray, b_bits: np.ndarray) -> np.ndarray:
    a = bf16_array_to_float(a_bits)
    b = bf16_array_to_float(b_bits)
    products = np.multiply(a, b, dtype=np.float32)
    return quantize_bf16_array(products)


def accumulate_full_bf16(product_bits: Sequence[int], *, items_per_cycle: int) -> np.float32:
    acc = 0
    for start in range(0, len(product_bits), items_per_cycle):
        lane_sum = bf16_tree4(product_bits[start:start + items_per_cycle])
        acc = bf16_add(acc, lane_sum)
    return bf16_to_float(acc)


def accumulate_bf16_tree_fp32_recurrent(
    product_bits: Sequence[int], *, items_per_cycle: int
) -> np.float32:
    acc = np.float32(0.0)
    for start in range(0, len(product_bits), items_per_cycle):
        lane_sum = bf16_tree4(product_bits[start:start + items_per_cycle])
        acc = fp32_add(acc, bf16_to_float(lane_sum))
    return acc


def accumulate_bf16_block_fp32_checkpoint(
    product_bits: Sequence[int], *, items_per_cycle: int, block_products: int = 64
) -> np.float32:
    if block_products <= 0 or block_products % items_per_cycle != 0:
        raise ValueError('block_products must be a positive multiple of items_per_cycle')
    checkpoint = np.float32(0.0)
    partial = 0
    products_in_partial = 0
    for start in range(0, len(product_bits), items_per_cycle):
        items = product_bits[start:start + items_per_cycle]
        lane_sum = bf16_tree4(items)
        partial = bf16_add(partial, lane_sum)
        products_in_partial += len(items)
        if products_in_partial == block_products:
            checkpoint = fp32_add(checkpoint, bf16_to_float(partial))
            partial = 0
            products_in_partial = 0
        elif products_in_partial > block_products:
            raise AssertionError('input grouping crossed the block boundary')
    if products_in_partial:
        checkpoint = fp32_add(checkpoint, bf16_to_float(partial))
    return checkpoint


def accumulate(
    style: AccumStyle,
    product_bits: Sequence[int],
    *,
    items_per_cycle: int,
    block_products: int = 64,
) -> np.float32:
    if style == AccumStyle.FULL_BF16:
        return accumulate_full_bf16(product_bits, items_per_cycle=items_per_cycle)
    if style == AccumStyle.BF16_TREE_FP32_RECURRENT:
        return accumulate_bf16_tree_fp32_recurrent(
            product_bits, items_per_cycle=items_per_cycle
        )
    if style == AccumStyle.BF16_BLOCK64_FP32_CHECKPOINT:
        return accumulate_bf16_block_fp32_checkpoint(
            product_bits,
            items_per_cycle=items_per_cycle,
            block_products=block_products,
        )
    raise ValueError(style)


@dataclass
class CycleOutput:
    valid: bool
    value: np.float32 | None
    checkpoint_pulse: bool = False


class FullBF16CycleModel:
    def __init__(self, items_per_cycle: int) -> None:
        self.items_per_cycle = items_per_cycle
        self.acc = 0

    def clear(self) -> None:
        self.acc = 0

    def issue(self, items: Sequence[int]) -> CycleOutput:
        lane_sum = bf16_tree4(items[:self.items_per_cycle])
        self.acc = bf16_add(self.acc, lane_sum)
        return CycleOutput(True, bf16_to_float(self.acc))


class FP32RecurrentCycleModel:
    def __init__(self, items_per_cycle: int) -> None:
        self.items_per_cycle = items_per_cycle
        self.acc = np.float32(0.0)

    def clear(self) -> None:
        self.acc = np.float32(0.0)

    def issue(self, items: Sequence[int]) -> CycleOutput:
        lane_sum = bf16_tree4(items[:self.items_per_cycle])
        self.acc = fp32_add(self.acc, bf16_to_float(lane_sum))
        return CycleOutput(True, self.acc)


class Block64CheckpointCycleModel:
    """Functional schedule model; FP32 checkpoint update may be delayed in RTL."""

    def __init__(self, items_per_cycle: int, block_products: int = 64) -> None:
        if block_products % items_per_cycle:
            raise ValueError('block size must divide by items_per_cycle')
        self.items_per_cycle = items_per_cycle
        self.block_products = block_products
        self.partial = 0
        self.count = 0
        self.checkpoint = np.float32(0.0)

    def clear(self) -> None:
        self.partial = 0
        self.count = 0
        self.checkpoint = np.float32(0.0)

    def issue(self, items: Sequence[int]) -> CycleOutput:
        lane_sum = bf16_tree4(items[:self.items_per_cycle])
        self.partial = bf16_add(self.partial, lane_sum)
        self.count += len(items[:self.items_per_cycle])
        pulse = False
        if self.count == self.block_products:
            self.checkpoint = fp32_add(self.checkpoint, bf16_to_float(self.partial))
            self.partial = 0
            self.count = 0
            pulse = True
        elif self.count > self.block_products:
            raise AssertionError('block boundary crossed')
        return CycleOutput(pulse, self.checkpoint if pulse else None, pulse)

    def flush(self) -> CycleOutput:
        if self.count:
            self.checkpoint = fp32_add(self.checkpoint, bf16_to_float(self.partial))
            self.partial = 0
            self.count = 0
            return CycleOutput(True, self.checkpoint, True)
        return CycleOutput(False, None, False)

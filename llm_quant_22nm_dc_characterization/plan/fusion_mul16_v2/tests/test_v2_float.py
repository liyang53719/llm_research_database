from __future__ import annotations

import math
import random
import unittest

import numpy as np

from model.fusion_mul16_v2_model import (
    FusionMul16V2Model,
    V2Mode,
    bf16_to_float,
    decode_bf16,
    decode_fp8,
    float_to_bf16,
    fp8_e4m3fn_to_float,
    raw_product_to_bf16,
    sign_extend,
)


def same_bf16(a: int, b: int) -> bool:
    af = bf16_to_float(a)
    bf = bf16_to_float(b)
    if np.isnan(af) and np.isnan(bf):
        return True
    return a == b


class FloatV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = FusionMul16V2Model()

    def test_fp8_products_exhaustive_to_bf16(self) -> None:
        for a in range(256):
            af = fp8_e4m3fn_to_float(a)
            for b in range(256):
                bf = fp8_e4m3fn_to_float(b)
                got = self.model.run_cycle(V2Mode.FP8_FP8, [a] * 16, [b] * 16).bf16_lane_items[0][0]
                with np.errstate(over="ignore", invalid="ignore"):
                    expected = float_to_bf16(float(np.float32(af * bf)))
                self.assertTrue(same_bf16(got, expected), (a, b, hex(got), hex(expected)))

    def test_i4_fp8_exhaustive_to_bf16(self) -> None:
        for a in range(16):
            av = sign_extend(a, 4)
            for b in range(256):
                got = self.model.run_cycle(V2Mode.I4_FP8, [a] * 16, [b] * 16).bf16_lane_items[0][0]
                with np.errstate(over="ignore", invalid="ignore"):
                    expected = float_to_bf16(float(np.float32(av * fp8_e4m3fn_to_float(b))))
                self.assertTrue(same_bf16(got, expected), (a, b, hex(got), hex(expected)))

    def test_bf16_and_mixed_directed(self) -> None:
        directed = [
            0x0000, 0x8000, 0x0001, 0x007F, 0x0080, 0x3F80, 0x4000,
            0xBF80, 0x7F7F, 0xFF7F, 0x7F80, 0xFF80, 0x7FC1,
        ]
        rng = random.Random(71)
        samples = directed + [rng.randrange(0x10000) for _ in range(2500)]
        for a, b in zip(samples, reversed(samples)):
            af, bf = bf16_to_float(a), bf16_to_float(b)
            got = self.model.run_cycle(V2Mode.BF16_BF16, [a] * 4, [b] * 4).bf16_lane_items[0][0]
            with np.errstate(over="ignore", invalid="ignore"):
                expected = float_to_bf16(float(np.float32(af * bf)))
            self.assertTrue(same_bf16(got, expected), (hex(a), hex(b), hex(got), hex(expected)))

        for width, mode, count in ((4, V2Mode.I4_BF16, 8), (8, V2Mode.I8_BF16, 4)):
            raw_range = 16 if width == 4 else 256
            for a in range(raw_range):
                av = sign_extend(a, width)
                for b in directed:
                    got = self.model.run_cycle(mode, [a] * count, [b] * count).bf16_lane_items[0][0]
                    with np.errstate(over="ignore", invalid="ignore"):
                        expected = float_to_bf16(float(np.float32(av * bf16_to_float(b))))
                    self.assertTrue(same_bf16(got, expected), (width, a, hex(b), hex(got), hex(expected)))

    def test_raw_normalizer_is_16_bit(self) -> None:
        for raw in [1, 2, 3, 15, 16, 127, 128, 255, 256, 4095, 65535]:
            for scale in [-20, -10, -1, 0, 5, 100]:
                got = raw_product_to_bf16(0, raw, scale)
                with np.errstate(over="ignore", invalid="ignore"):
                    expected = float_to_bf16(float(np.float32(math.ldexp(raw, scale))))
                self.assertTrue(same_bf16(got, expected), (raw, scale, hex(got), hex(expected)))

    def test_fp8_widen_to_bf16_is_exact(self) -> None:
        for raw in range(256):
            value = fp8_e4m3fn_to_float(raw)
            widened = bf16_to_float(float_to_bf16(float(value)))
            if np.isnan(value):
                self.assertTrue(np.isnan(widened))
            else:
                self.assertEqual(float(value), float(widened))


if __name__ == "__main__":
    unittest.main()

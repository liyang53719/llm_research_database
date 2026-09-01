from __future__ import annotations

import math
import random
import unittest

import numpy as np

from model.fusion_mul16_model import (
    FusionMode,
    FusionMul16Model,
    bf16_to_float,
    fp8_e4m3fn_to_float,
    sign_extend,
)


def same_float(a: np.float32, b: np.float32) -> bool:
    if np.isnan(a) and np.isnan(b):
        return True
    if a == b:
        return math.copysign(1.0, float(a)) == math.copysign(1.0, float(b)) or a != 0
    return False


class FloatFusionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = FusionMul16Model()

    def test_fp8_fp8_exhaustive(self) -> None:
        for a in range(256):
            af = fp8_e4m3fn_to_float(a)
            for b in range(256):
                bf = fp8_e4m3fn_to_float(b)
                got = self.model.run(FusionMode.FP8_FP8, [a] * 16, [b] * 16).products[0]
                with np.errstate(over="ignore", invalid="ignore"):
                    expected = np.float32(af * bf)
                self.assertTrue(same_float(got, expected), (a, b, got, expected))

    def test_i4_fp8_exhaustive(self) -> None:
        for a in range(16):
            av = sign_extend(a, 4)
            for b in range(256):
                expected = np.float32(av * fp8_e4m3fn_to_float(b))
                got = self.model.run(FusionMode.I4_FP8, [a] * 16, [b] * 16).products[0]
                self.assertTrue(same_float(got, expected), (a, b, got, expected))

    def test_i8_fp8_exhaustive(self) -> None:
        for a in range(256):
            av = sign_extend(a, 8)
            for b in range(256):
                expected = np.float32(av * fp8_e4m3fn_to_float(b))
                got = self.model.run(FusionMode.I8_FP8, [a] * 8, [b] * 8).products[0]
                self.assertTrue(same_float(got, expected), (a, b, got, expected))

    def test_bf16_and_mixed_stratified(self) -> None:
        directed = [
            0x0000, 0x8000, 0x0001, 0x007F, 0x0080, 0x3F80, 0x4000,
            0x7F7F, 0xFF7F, 0x7F80, 0xFF80, 0x7FC1,
        ]
        rng = random.Random(23)
        samples = directed + [rng.randrange(0x10000) for _ in range(1500)]
        for a, b in zip(samples, reversed(samples)):
            af, bf = bf16_to_float(a), bf16_to_float(b)
            got = self.model.run(FusionMode.BF16_BF16, [a] * 4, [b] * 4).products[0]
            expected = np.float32(af * bf)
            self.assertTrue(same_float(got, expected), (hex(a), hex(b), got, expected))

        for int_width, mode, count in [
            (4, FusionMode.I4_BF16, 8),
            (8, FusionMode.I8_BF16, 4),
        ]:
            raw_range = 16 if int_width == 4 else 256
            for a in range(raw_range):
                av = sign_extend(a, int_width)
                for b in directed:
                    got = self.model.run(mode, [a] * count, [b] * count).products[0]
                    with np.errstate(over="ignore", invalid="ignore"):
                        expected = np.float32(av * bf16_to_float(b))
                    self.assertTrue(same_float(got, expected), (int_width, a, hex(b), got, expected))

    def test_float_mode_brick_counts(self) -> None:
        for mode, count in [
            (FusionMode.FP8_FP8, 16),
            (FusionMode.BF16_BF16, 4),
            (FusionMode.I4_FP8, 16),
            (FusionMode.I8_FP8, 8),
            (FusionMode.I4_BF16, 8),
            (FusionMode.I8_BF16, 4),
        ]:
            result = self.model.run(mode, [0] * count, [0] * count)
            self.assertEqual(result.brick_count, 16)
            self.assertEqual(result.products_per_cycle, count)


if __name__ == "__main__":
    unittest.main()

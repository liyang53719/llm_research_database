from __future__ import annotations

import random
import unittest

from model.fusion_mul16_model import FusionMode, FusionMul16Model, sign_extend, twos


class IntegerFusionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = FusionMul16Model()

    def test_i4_i4_exhaustive(self) -> None:
        for a in range(16):
            for b in range(16):
                result = self.model.run(FusionMode.I4_I4, [a] * 16, [b] * 16)
                expected = sign_extend(a, 4) * sign_extend(b, 4)
                self.assertEqual(result.products, (expected,) * 16)
                self.assertEqual(result.brick_count, 16)

    def test_i4_i8_exhaustive(self) -> None:
        for a in range(16):
            for b in range(256):
                result = self.model.run(FusionMode.I4_I8, [a] * 8, [b] * 8)
                expected = sign_extend(a, 4) * sign_extend(b, 8)
                self.assertEqual(result.products, (expected,) * 8)
                self.assertEqual(result.brick_count, 16)

    def test_i8_i8_exhaustive(self) -> None:
        for a in range(256):
            for b in range(256):
                result = self.model.run(FusionMode.I8_I8, [a] * 4, [b] * 4)
                expected = sign_extend(a, 8) * sign_extend(b, 8)
                self.assertEqual(result.products, (expected,) * 4)
                self.assertEqual(result.brick_count, 16)

    def test_i16_i16_boundaries_and_random(self) -> None:
        values = [-32768, -32767, -1024, -1, 0, 1, 1023, 32766, 32767]
        rng = random.Random(19)
        values.extend(rng.randint(-32768, 32767) for _ in range(5000))
        for a, b in zip(values, reversed(values)):
            result = self.model.run(FusionMode.I16_I16, [twos(a, 16)], [twos(b, 16)])
            self.assertEqual(result.products[0], a * b)
            self.assertEqual(result.brick_count, 16)

    def test_products_per_cycle(self) -> None:
        expected = {
            FusionMode.I4_I4: 16,
            FusionMode.I4_I8: 8,
            FusionMode.I8_I8: 4,
            FusionMode.I16_I16: 1,
        }
        for mode, count in expected.items():
            result = self.model.run(mode, [0] * count, [0] * count)
            self.assertEqual(result.products_per_cycle, count)
            self.assertEqual(result.brick_count, 16)


if __name__ == "__main__":
    unittest.main()

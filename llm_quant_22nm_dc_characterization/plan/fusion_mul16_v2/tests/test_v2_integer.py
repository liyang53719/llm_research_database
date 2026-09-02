from __future__ import annotations

import random
import unittest

from model.fusion_mul16_v2_model import (
    FusionMul16V2Model,
    V2Mode,
    int16_magnitude_via_four_u8_products,
    sign_extend,
)


class IntegerV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = FusionMul16V2Model()

    def test_i4_i8_exhaustive(self) -> None:
        for a in range(16):
            for b in range(256):
                result = self.model.run_cycle(V2Mode.I4_I8, [a] * 8, [b] * 8)
                product = sign_extend(a, 4) * sign_extend(b, 8)
                self.assertEqual(result.int_lane_sums, (2 * product,) * 4)
                self.assertEqual(len(result.brick_products), 16)

    def test_i8_i8_exhaustive(self) -> None:
        for a in range(256):
            for b in range(256):
                result = self.model.run_cycle(V2Mode.I8_I8, [a] * 4, [b] * 4)
                product = sign_extend(a, 8) * sign_extend(b, 8)
                self.assertEqual(result.int_lane_sums, (product,) * 4)
                self.assertEqual(len(result.brick_products), 16)

    def test_int16_temporal_reference(self) -> None:
        rng = random.Random(61)
        values = [-32768, -32767, -255, -1, 0, 1, 255, 32766, 32767]
        values += [rng.randint(-32768, 32767) for _ in range(5000)]
        for a, b in zip(values, reversed(values)):
            self.assertEqual(int16_magnitude_via_four_u8_products(a, b), a * b)

    def test_removed_modes(self) -> None:
        names = {mode.name for mode in V2Mode}
        self.assertNotIn("I4_I4", names)
        self.assertNotIn("I16_I16", names)
        self.assertNotIn("I8_FP8", names)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from model.fusion_mul16_v2_model import (
    FP_VISIBLE_LATENCY,
    INT_VISIBLE_LATENCY,
    PipelineScheduleModel,
    V2Mode,
)


class PipelineV2Tests(unittest.TestCase):
    def test_configuration_precedes_data(self) -> None:
        model = PipelineScheduleModel()
        with self.assertRaises(RuntimeError):
            model.issue(0)
        model.configure(V2Mode.FP8_FP8)
        model.issue(1)
        with self.assertRaises(RuntimeError):
            model.configure(V2Mode.BF16_BF16)

    def test_integer_ii_one(self) -> None:
        model = PipelineScheduleModel()
        model.configure(V2Mode.I4_I8)
        outputs = []
        for token in range(8):
            model.issue(token)
            outputs.extend(model.step())
        for _ in range(INT_VISIBLE_LATENCY + 2):
            outputs.extend(model.step())
        self.assertEqual([token for _, token in outputs], list(range(8)))

    def test_fp_ii_one(self) -> None:
        model = PipelineScheduleModel()
        model.configure(V2Mode.FP8_FP8)
        outputs = []
        for token in range(8):
            model.issue(token)
            outputs.extend(model.step())
        for _ in range(FP_VISIBLE_LATENCY + 2):
            outputs.extend(model.step())
        self.assertEqual([token for _, token in outputs], list(range(8)))


if __name__ == "__main__":
    unittest.main()

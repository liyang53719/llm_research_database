from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from numeric_formats import (
    OperandFormat,
    converted_mixed_dot,
    encode_operand,
    native_mixed_dot,
)

class MixedDotTests(unittest.TestCase):
    def test_i4_fp8_converter_path_exact(self):
        lhs = [encode_operand(x, OperandFormat.INT4) for x in [-8,-7,-3,-1,0,1,3,7]]
        rhs = [encode_operand(x, OperandFormat.FP8_E4M3FN)
               for x in [-3.25,1.5,0.5,-0.25,4.0,2.0,-1.0,0.75]]
        self.assertEqual(
            float(native_mixed_dot(lhs, rhs, OperandFormat.INT4, OperandFormat.FP8_E4M3FN)),
            float(converted_mixed_dot(lhs, rhs, OperandFormat.INT4,
                                      OperandFormat.FP8_E4M3FN,
                                      OperandFormat.FP8_E4M3FN))
        )

    def test_i8_fp8_converter_path_loses_information(self):
        lhs = [encode_operand(x, OperandFormat.INT8) for x in [17,31,63,95,127]]
        rhs = [encode_operand(1.0, OperandFormat.FP8_E4M3FN)] * len(lhs)
        self.assertNotEqual(
            float(native_mixed_dot(lhs, rhs, OperandFormat.INT8, OperandFormat.FP8_E4M3FN)),
            float(converted_mixed_dot(lhs, rhs, OperandFormat.INT8,
                                      OperandFormat.FP8_E4M3FN,
                                      OperandFormat.FP8_E4M3FN))
        )

    def test_i8_bf16_converter_path_exact(self):
        lhs = [encode_operand(x, OperandFormat.INT8) for x in [-128,-65,-16,-1,0,1,17,127]]
        rhs = [encode_operand(x, OperandFormat.BF16)
               for x in [-3.25,1.5,0.5,-0.25,4.0,2.0,-1.0,0.75]]
        self.assertEqual(
            float(native_mixed_dot(lhs, rhs, OperandFormat.INT8, OperandFormat.BF16)),
            float(converted_mixed_dot(lhs, rhs, OperandFormat.INT8,
                                      OperandFormat.BF16, OperandFormat.BF16))
        )

if __name__ == "__main__":
    unittest.main()

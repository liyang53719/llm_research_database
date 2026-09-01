from __future__ import annotations
import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from numeric_formats import (
    OperandFormat,
    conversion_coverage,
    decode_operand,
    encode_operand,
    fp8_e4m3fn_to_float32,
)

class NumericFormatTests(unittest.TestCase):
    def test_int4_to_fp8_exact(self):
        c = conversion_coverage(OperandFormat.INT4, OperandFormat.FP8_E4M3FN)
        self.assertEqual(c.exact_codes, 16)

    def test_int8_to_fp8_not_exact(self):
        c = conversion_coverage(OperandFormat.INT8, OperandFormat.FP8_E4M3FN)
        self.assertEqual(c.exact_codes, 80)
        self.assertEqual(c.max_abs_error, 4.0)

    def test_int8_to_bf16_exact(self):
        c = conversion_coverage(OperandFormat.INT8, OperandFormat.BF16)
        self.assertEqual(c.exact_codes, 256)

    def test_fp8_finite_roundtrip(self):
        for bits in range(256):
            v = fp8_e4m3fn_to_float32(bits)
            if np.isnan(v):
                continue
            out = decode_operand(encode_operand(float(v), OperandFormat.FP8_E4M3FN),
                                 OperandFormat.FP8_E4M3FN)
            self.assertEqual(float(v), float(out))

if __name__ == "__main__":
    unittest.main()

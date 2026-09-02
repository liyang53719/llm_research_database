from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'model'))

from accum_error_study import run_case  # noqa: E402


class ErrorOrderingTests(unittest.TestCase):
    def _rows(self, kind: str, length: int):
        rng = np.random.default_rng(20260902 + length)
        return {
            row['accum_style']: row
            for row in run_case(rng, kind, 'gaussian', length, 600)
        }

    def test_long_k_nrmse_ordering_fp8(self) -> None:
        rows = self._rows('fp8_proxy', 1024)
        self.assertLess(
            rows['bf16_tree_fp32_recurrent']['nrmse'],
            rows['bf16_block64_fp32_checkpoint']['nrmse'],
        )
        self.assertLess(
            rows['bf16_block64_fp32_checkpoint']['nrmse'],
            rows['full_bf16']['nrmse'],
        )

    def test_long_k_nrmse_ordering_bf16(self) -> None:
        rows = self._rows('bf16', 1024)
        self.assertLess(
            rows['bf16_tree_fp32_recurrent']['nrmse'],
            rows['bf16_block64_fp32_checkpoint']['nrmse'],
        )
        self.assertLess(
            rows['bf16_block64_fp32_checkpoint']['nrmse'],
            rows['full_bf16']['nrmse'],
        )

    def test_fp32_recurrent_tail_reduction(self) -> None:
        rows = self._rows('fp8_proxy', 1024)
        self.assertLess(
            rows['bf16_tree_fp32_recurrent']['p99_relative_error_filtered'],
            rows['full_bf16']['p99_relative_error_filtered'] * 0.35,
        )


if __name__ == '__main__':
    unittest.main()

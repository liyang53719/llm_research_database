from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / 'rtl'


class RTLStructureTests(unittest.TestCase):
    def text(self, name: str) -> str:
        return (RTL / name).read_text(encoding='utf-8')

    def test_no_multiplier_added_by_accumulators(self) -> None:
        for path in RTL.glob('*accum*.sv'):
            text = path.read_text(encoding='utf-8')
            self.assertNotRegex(text, r'(?<![<>=!])\*(?![=])', path.name)
            self.assertNotIn('DW_fp_mult', text, path.name)

    def test_common_tree_has_twelve_bf16_adders(self) -> None:
        text = self.text('fusion_mul16_v3_bf16_tree_dw.sv')
        # Three instances in a four-lane generate loop.
        self.assertEqual(text.count('DW_fp_add #(7, 8, 0)'), 3)
        self.assertIn('for (g = 0; g < 4;', text)

    def test_full_bf16_has_bf16_recurrent(self) -> None:
        text = self.text('fusion_mul16_v3_accum_full_bf16_dw.sv')
        self.assertEqual(text.count('DW_fp_add #(7, 8, 0)'), 1)
        self.assertNotIn('DW_fp_add #(23, 8, 0)', text)

    def test_fp32_recurrent_has_four_fp32_adders(self) -> None:
        text = self.text('fusion_mul16_v3_accum_fp32_recurrent_dw.sv')
        self.assertEqual(text.count('DW_fp_add #(23, 8, 0)'), 1)
        self.assertIn('for (g = 0; g < 4;', text)
        self.assertIn('{lane_sum[g], 16\'b0}', text)

    def test_block64_has_partial_and_checkpoint_adders(self) -> None:
        text = self.text('fusion_mul16_v3_accum_block64_fp32_checkpoint_dw.sv')
        self.assertEqual(text.count('DW_fp_add #(7, 8, 0)'), 1)
        self.assertEqual(text.count('DW_fp_add #(23, 8, 0)'), 1)
        self.assertIn('BLOCK_PRODUCTS = 64', text)
        self.assertIn('CHECKPOINT_WAIT_CYCLES = 2', text)
        self.assertIn('flush_i', text)

    def test_cluster_reuses_v2_product_pipe(self) -> None:
        text = self.text('fusion_mul16_v3_cluster.sv')
        self.assertIn('fusion_mul16_v2_product_pipe', text)
        self.assertIn('fusion_mul16_v2_config', text)
        sanitized = text.replace('::*', '')
        self.assertNotRegex(sanitized, r'(?<![<>=!])\*(?![=])')

    def test_balanced_delimiters_and_modules(self) -> None:
        for path in RTL.glob('*.sv'):
            text = path.read_text(encoding='utf-8')
            self.assertEqual(text.count('module '), text.count('endmodule'), path.name)
            self.assertEqual(text.count('('), text.count(')'), path.name)
            self.assertEqual(text.count('{'), text.count('}'), path.name)


if __name__ == '__main__':
    unittest.main()

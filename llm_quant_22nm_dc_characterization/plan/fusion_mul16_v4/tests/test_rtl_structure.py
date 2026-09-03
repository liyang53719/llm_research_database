from __future__ import annotations
import re,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class RTLStructureTests(unittest.TestCase):
    def text(self,name): return (ROOT/'rtl'/name).read_text()

    def test_exactly_one_brick_generate(self):
        t=self.text('fusion_mul16_v4_product_pipe.sv')
        self.assertEqual(t.count('fusion_mul16_v4_mul4x4_brick u_brick'),1)
        self.assertIn('for (g = 0; g < 16; g = g + 1)',t)

    def test_no_fp_multiplier(self):
        all_text='\n'.join(p.read_text() for p in (ROOT/'rtl').glob('*.sv'))
        self.assertNotIn('DW_fp_mult',all_text)

    def test_selected_accumulator_shape(self):
        tree=self.text('fusion_mul16_v4_bf16_tree_dw.sv')
        rec=self.text('fusion_mul16_v4_fp32_recurrent_accum_dw.sv')
        self.assertEqual(tree.count('DW_fp_add #(7, 8, IEEE_COMPLIANCE)'),3)
        self.assertIn('for (g = 0; g < 4; g = g + 1)',tree)
        self.assertEqual(rec.count('DW_fp_add #(23, 8, IEEE_COMPLIANCE)'),1)
        self.assertIn('for (g = 0; g < 4; g = g + 1)',rec)
        self.assertNotIn('partial_bf16',rec)

    def test_no_direct_int16_mode(self):
        pkg=self.text('fusion_mul16_v4_pkg.sv')
        self.assertNotIn('I16',pkg)
        self.assertEqual(pkg.count('MODE_'),14)  # seven enum + seven case references

    def test_packed_interface(self):
        top=self.text('fusion_mul16_v4.sv')
        self.assertIn('logic [127:0] lhs_packed_i',top)
        self.assertIn('logic [127:0] rhs_packed_i',top)
        self.assertNotIn('[15:0] lhs_i [',top)

    def test_rne_is_fixed(self):
        top=self.text('fusion_mul16_v4.sv')
        self.assertIn(".rnd_i(3'b000)",top)
        self.assertNotIn('cfg_rnd_i',top)

    def test_last_latency_constants(self):
        top=self.text('fusion_mul16_v4.sv')
        self.assertIn('INT_VISIBLE_LATENCY = 4',top)
        self.assertIn('FP_VISIBLE_LATENCY  = 7',top)

    def test_filelist_complete(self):
        listed={line.strip() for line in (ROOT/'rtl/fusion_mul16_v4.f').read_text().splitlines() if line.strip()}
        actual={p.name for p in (ROOT/'rtl').glob('*.sv')}
        self.assertEqual(listed,actual)

if __name__=='__main__': unittest.main()

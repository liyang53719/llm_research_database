from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'model'))
from fusion_mul16_v4_model import (  # noqa:E402
    Mode, PRODUCTS_PER_CYCLE, ITEMS_PER_LANE, INT_MODES,
    FusionMul16V4FunctionalModel, PipelineModel,
    bf16_to_float, pack_fields, products_from_packed,
    raw16_to_bf16_contract, scalar_product, sign_extend,
)


class FunctionalModelTests(unittest.TestCase):
    def test_mode_throughputs(self):
        self.assertEqual([PRODUCTS_PER_CYCLE[m] for m in Mode],[8,4,16,4,16,8,4])
        self.assertEqual([ITEMS_PER_LANE[m] for m in Mode],[2,1,4,1,4,2,1])

    def test_i4_i8_lane_mapping(self):
        lhs=pack_fields([0x8,0x7,0xf,0x1,0x2,0xe,0x3,0xd],4)
        rhs=pack_fields([0x80,0x7f,0xff,0x01,0x02,0xfe,0x03,0xfd],8)
        lanes=products_from_packed(Mode.I4_I8,lhs,rhs)
        flat=[p for lane in lanes for p in lane]
        expected=[sign_extend((lhs>>(i*4))&0xf,4)*sign_extend((rhs>>(i*8))&0xff,8) for i in range(8)]
        self.assertEqual(flat,expected)

    def test_i8_i8_lane_mapping(self):
        av=[-128,-1,1,127]; bv=[-128,7,-9,127]
        lhs=pack_fields(av,8); rhs=pack_fields(bv,8)
        lanes=products_from_packed(Mode.I8_I8,lhs,rhs)
        self.assertEqual([x[0] for x in lanes],[a*b for a,b in zip(av,bv)])

    def test_fp8_exact_known(self):
        # E4M3 encodings: 1.0=0x38, 2.0=0x40, -1.0=0xb8.
        self.assertEqual(bf16_to_float(scalar_product(Mode.FP8_FP8,0x38,0x40)),np.float32(2.0))
        self.assertEqual(bf16_to_float(scalar_product(Mode.FP8_FP8,0xb8,0x40)),np.float32(-2.0))

    def test_bf16_known(self):
        self.assertEqual(bf16_to_float(scalar_product(Mode.BF16_BF16,0x3f80,0x4000)),np.float32(2.0))
        self.assertEqual(bf16_to_float(scalar_product(Mode.I4_BF16,0xf,0x4000)),np.float32(-2.0))
        self.assertEqual(bf16_to_float(scalar_product(Mode.I8_BF16,0x80,0x3f80)),np.float32(-128.0))

    def test_rne_tie_even(self):
        # raw=0x101 normalized at bit 8 is exactly halfway; q=0x80 even -> stay.
        self.assertEqual(raw16_to_bf16_contract(0,0x101,-8),0x3f80)

    def test_integer_accumulation(self):
        model=FusionMul16V4FunctionalModel()
        model.clear()
        lhs=pack_fields([1]*8,4); rhs=pack_fields([2]*8,8)
        for _ in range(5): out=model.issue(Mode.I4_I8,lhs,rhs)
        self.assertEqual(out.int_acc,(20,20,20,20))
        self.assertFalse(out.fp_valid)

    def test_fp32_recurrent_accumulation(self):
        model=FusionMul16V4FunctionalModel()
        model.clear()
        lhs=pack_fields([0x38]*16,8); rhs=pack_fields([0x38]*16,8)
        for _ in range(9): out=model.issue(Mode.FP8_FP8,lhs,rhs)
        self.assertTrue(out.fp_valid)
        self.assertEqual(tuple(float(x) for x in out.fp_acc),(36.0,36.0,36.0,36.0))

    def test_pipeline_latencies(self):
        p=PipelineModel(); p.issue_data(Mode.I8_I8,last=True)
        seen=[]
        for _ in range(4): seen.extend(p.tick())
        self.assertEqual(len(seen),1); self.assertTrue(seen[0].int_last)
        p=PipelineModel(); p.issue_data(Mode.FP8_FP8,last=True)
        seen=[]
        for _ in range(7): seen.extend(p.tick())
        self.assertEqual(len(seen),1); self.assertTrue(seen[0].fp_last)
        p=PipelineModel(); p.issue_clear(); seen=[]
        for _ in range(7): seen.extend(p.tick())
        self.assertTrue(seen[0].clear_done)


class GeneratedEvidenceTests(unittest.TestCase):
    def test_full_domain_report(self):
        report=json.loads((ROOT/'results/full_input_domain_report.json').read_text())
        self.assertEqual(report['status'],'PASS')
        self.assertEqual(report['mismatches'],0)
        self.assertEqual(report['bf16_raw_pair_space'],2**32)
        self.assertGreaterEqual(report['literal_or_equivalence_checks'],30_000_000)

    def test_precision_proxy(self):
        report=json.loads((ROOT/'results/precision_sweep_report.json').read_text())
        self.assertEqual(report['status'],'PASS')
        self.assertEqual(report['failures'],[])
        self.assertEqual(report['rows'],100)


if __name__=='__main__': unittest.main()

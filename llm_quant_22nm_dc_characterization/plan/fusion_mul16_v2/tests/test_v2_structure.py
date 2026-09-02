from __future__ import annotations

import csv
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / "rtl"


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//.*", "", text)


class StructureV2Tests(unittest.TestCase):
    def test_multiply_exists_only_in_brick(self) -> None:
        offenders = []
        for path in RTL.glob("*.sv"):
            text = strip_comments(path.read_text(encoding="utf-8"))
            if re.search(r"\s\*\s", text) and path.name != "mul4x4_brick.sv":
                offenders.append(path.name)
        self.assertEqual(offenders, [])

    def test_exactly_one_brick_generate_loop(self) -> None:
        text = strip_comments((RTL / "fusion_mul16_v2_product_pipe.sv").read_text(encoding="utf-8"))
        self.assertIn("for (g = 0; g < 16; g = g + 1)", text)
        self.assertEqual(text.count("mul4x4_brick u_brick"), 1)

    def test_packed_interface_and_no_wide_fp_product(self) -> None:
        text = strip_comments((RTL / "fusion_mul16_v2_cluster.sv").read_text(encoding="utf-8"))
        self.assertIn("logic [127:0] lhs_packed_i", text)
        self.assertIn("logic [127:0] rhs_packed_i", text)
        self.assertNotIn("logic [15:0] lhs_i [0:15]", text)
        self.assertNotIn("logic [31:0] fp_product", "\n".join(p.read_text() for p in RTL.glob("*.sv")))

    def test_mode_set_is_trimmed(self) -> None:
        text = (RTL / "fusion_mul16_v2_pkg.sv").read_text(encoding="utf-8")
        for name in ["MODE_I4_I8", "MODE_I8_I8", "MODE_FP8_FP8", "MODE_BF16_BF16", "MODE_I4_FP8", "MODE_I4_BF16", "MODE_I8_BF16"]:
            self.assertIn(name, text)
        for name in ["MODE_I4_I4", "MODE_I16_I16", "MODE_I8_FP8"]:
            self.assertNotIn(name, text)

    def test_bf16_not_fp32_accumulator(self) -> None:
        text = "\n".join(p.read_text(encoding="utf-8") for p in RTL.glob("*.sv"))
        self.assertIn("DW_fp_add #(7, 8, 0)", text)
        self.assertNotIn("DW_fp_add #(23, 8", text)
        self.assertNotIn("raw_binary_product_to_fp32", text)

    def test_config_beat_has_priority_over_data(self) -> None:
        text = strip_comments((RTL / "fusion_mul16_v2_config.sv").read_text(encoding="utf-8"))
        self.assertIn("accept_data_o = valid_i && cfg_loaded_q && !configuration_beat", text)
        self.assertIn("mode_onehot_q <= mode_to_onehot(cfg_mode_i)", text)
        cluster = strip_comments((RTL / "fusion_mul16_v2_cluster.sv").read_text(encoding="utf-8"))
        self.assertIn("fusion_mul16_v2_config", cluster)
        self.assertIn(".valid_i(accept_data)", cluster)

    def test_dc_is_1ghz_only(self) -> None:
        cfg = json.loads((ROOT / "config/characterization_1ghz.json").read_text())
        self.assertEqual(cfg["clock_period_ns"], 1.0)
        with (ROOT / "config/dc_experiments_1ghz.csv").open(encoding="utf-8-sig") as f:
            groups = list(csv.DictReader(f))
        self.assertGreaterEqual(len(groups), 12)
        self.assertEqual(cfg["expected_runs"], len(groups))

    def test_module_delimiters(self) -> None:
        names = []
        for path in RTL.glob("*.sv"):
            text = strip_comments(path.read_text(encoding="utf-8"))
            self.assertEqual(text.count("("), text.count(")"), path.name)
            self.assertEqual(text.count("{"), text.count("}"), path.name)
            modules = re.findall(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)", text)
            self.assertEqual(len(modules), text.count("endmodule"), path.name)
            names.extend(modules)
        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()

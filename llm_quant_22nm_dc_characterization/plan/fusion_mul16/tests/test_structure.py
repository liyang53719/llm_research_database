from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / "rtl"


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//.*", "", text)
    return text


class StructureTests(unittest.TestCase):
    def test_only_brick_contains_multiply_operator(self) -> None:
        offenders = []
        for path in RTL.glob("*.sv"):
            text = strip_comments(path.read_text(encoding="utf-8"))
            # Ignore preprocessor and constant dimension arithmetic. Hardware multiply
            # must appear as a whitespace-delimited '*' token in this coding contract.
            if re.search(r"\s\*\s", text) and path.name != "mul4x4_brick.sv":
                offenders.append(path.name)
        self.assertEqual(offenders, [])

    def test_brick_has_single_arithmetic_multiply(self) -> None:
        text = strip_comments((RTL / "mul4x4_brick.sv").read_text(encoding="utf-8"))
        self.assertEqual(len(re.findall(r"\s\*\s", text)), 1)

    def test_product_core_elaborates_exactly_16_bricks(self) -> None:
        text = strip_comments((RTL / "fusion_mul16_product_core.sv").read_text(encoding="utf-8"))
        self.assertIn("for (g = 0; g < 16; g = g + 1)", text)
        self.assertEqual(text.count("mul4x4_brick u_brick"), 1)

    def test_mode_table_declares_all_ten_modes(self) -> None:
        text = (RTL / "fusion_mul16_pkg.sv").read_text(encoding="utf-8")
        for name in [
            "MODE_I4_I4", "MODE_I4_I8", "MODE_I8_I8", "MODE_I16_I16",
            "MODE_FP8_FP8", "MODE_BF16_BF16", "MODE_I4_FP8",
            "MODE_I8_FP8", "MODE_I4_BF16", "MODE_I8_BF16",
        ]:
            self.assertIn(name, text)

    def test_all_rtl_delimiters_and_module_names(self) -> None:
        modules = []
        for path in RTL.glob("*.sv"):
            text = strip_comments(path.read_text(encoding="utf-8"))
            self.assertEqual(text.count("("), text.count(")"), path.name)
            self.assertEqual(text.count("{"), text.count("}"), path.name)
            names = re.findall(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)", text)
            self.assertEqual(len(names), text.count("endmodule"), path.name)
            modules.extend(names)
        self.assertEqual(len(modules), len(set(modules)))

    def test_no_floating_multiplier_macro_outside_bricks(self) -> None:
        offenders = []
        for path in RTL.glob("*.sv"):
            text = strip_comments(path.read_text(encoding="utf-8"))
            if "DW_fp_mult" in text:
                offenders.append(path.name)
        self.assertEqual(offenders, [])

    def test_dc_experiment_count(self) -> None:
        import csv
        import json
        with (ROOT / "config/dc_experiments.csv").open(encoding="utf-8-sig") as f:
            groups = list(csv.DictReader(f))
        cfg = json.loads((ROOT / "config/characterization.json").read_text(encoding="utf-8"))
        self.assertEqual(len(groups), 11)
        self.assertEqual(len(groups) * len(cfg["clock_periods_ns"]), 33)


if __name__ == "__main__":
    unittest.main()

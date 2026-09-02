from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DCPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = json.loads((ROOT / 'config/characterization_1ghz.json').read_text())
        with (ROOT / 'config/dc_experiments_1ghz.csv').open(encoding='utf-8-sig') as f:
            self.rows = list(csv.DictReader(f))

    def test_only_one_ghz(self) -> None:
        self.assertEqual(self.cfg['clock_period_ns'], 1.0)
        self.assertNotIn('clock_periods_ns', self.cfg)

    def test_expected_group_count(self) -> None:
        self.assertEqual(len(self.rows), 12)
        self.assertEqual(self.cfg['expected_runs'], 12)
        self.assertEqual(len({row['group_id'] for row in self.rows}), 12)

    def test_three_accum_styles_covered(self) -> None:
        styles = {int(row['accum_style']) for row in self.rows}
        self.assertEqual(styles, {0, 1, 2})
        for scope in ('accumulator_only', 'full_cluster', 'fixed_fp8', 'fixed_bf16'):
            scoped = {int(row['accum_style']) for row in self.rows if row['scope'] == scope}
            self.assertEqual(scoped, {0, 1, 2})

    def test_multicycle_only_for_checkpoint(self) -> None:
        for row in self.rows:
            expected = 'checkpoint_mc2' if int(row['accum_style']) == 2 else 'single_cycle'
            self.assertEqual(row['constraint_profile'], expected)


if __name__ == '__main__':
    unittest.main()

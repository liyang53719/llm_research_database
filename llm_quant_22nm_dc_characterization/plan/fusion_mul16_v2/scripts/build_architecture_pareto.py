#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rows(path: Path) -> list[dict]:
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    summary = {r['group_id']: r for r in rows(ROOT / 'results/local_dc/fusion16_v2_area_1ghz.csv')}
    shared = summary['V2_SHARED_FULL7_FTZ']
    separate = summary['V2_SEPARATE_FULL_FTZ']
    entries = [
        {'architecture': 'V2_SHARED_FULL7_FTZ', 'area_1ghz_um2': float(shared['mapped_cell_area_um2']),
         'wns_ns': float(shared['wns_ns']), 'timing_met_1ghz': int(float(shared['timing_met'])),
         'concurrent_mode_count': 1, 'throughput_match': 'single_selected_mode'},
        {'architecture': 'V2_SEPARATE_FULL_FTZ', 'area_1ghz_um2': float(separate['mapped_cell_area_um2']),
         'wns_ns': float(separate['wns_ns']), 'timing_met_1ghz': int(float(separate['timing_met'])),
         'concurrent_mode_count': 3, 'throughput_match': 'full_integer_fp8_bf16_concurrency'},
        {'architecture': 'V1_SHARED_FULL_REFERENCE', 'area_1ghz_um2': 23201.815,
         'wns_ns': -0.100014, 'timing_met_1ghz': 0, 'concurrent_mode_count': 1,
         'throughput_match': 'v1_reference_only'},
        {'architecture': 'V1_SEPARATE_FULL_REFERENCE', 'area_1ghz_um2': 27912.885,
         'wns_ns': -0.0086357, 'timing_met_1ghz': 0, 'concurrent_mode_count': 3,
         'throughput_match': 'v1_reference_only'},
    ]
    shared_area = entries[0]['area_1ghz_um2']
    separate_area = entries[1]['area_1ghz_um2']
    for row in entries:
        row['area_ratio_vs_v2_separate'] = row['area_1ghz_um2'] / separate_area
        row['area_saving_vs_v2_separate_pct'] = 100.0 * (1.0 - row['area_ratio_vs_v2_separate'])
        row['pareto_eligible_1ghz'] = int(row['timing_met_1ghz'] == 1)
        row['pareto_dominated'] = 0
    out = ROOT / 'results/local_dc/architecture_pareto.csv'
    with out.open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(entries[0]))
        writer.writeheader(); writer.writerows(entries)
    decision = json.loads((ROOT / 'results/local_dc/architecture_decision.json').read_text())
    decision.update({
        'shared_area_lt_separate': shared_area < separate_area,
        'both_shared_and_separate_timing_met': bool(entries[0]['timing_met_1ghz'] and entries[1]['timing_met_1ghz']),
        'architecture_accept': bool(decision.get('architecture_accept')),
        'pareto_scope': 'only 1GHz timing-eligible rows are candidates; area/throughput fields retain references',
    })
    (ROOT / 'results/local_dc/architecture_decision.json').write_text(json.dumps(decision, indent=2) + '\n')
    print(out)


if __name__ == '__main__':
    main()

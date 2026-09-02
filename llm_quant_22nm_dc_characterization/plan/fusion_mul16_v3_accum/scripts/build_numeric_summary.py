#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    source = ROOT / 'results/accum_error_comparison.csv'
    with source.open(encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))

    selected = []
    for row in rows:
        if row['distribution'] == 'gaussian' and row['dot_length'] in {'128', '1024', '4096'}:
            selected.append({
                'input_kind': row['input_kind'],
                'dot_length': int(row['dot_length']),
                'items_per_cycle': int(row['items_per_cycle']),
                'accum_style': row['accum_style'],
                'nrmse_pct': float(row['nrmse']) * 100.0,
                'median_relative_error_pct': float(row['median_relative_error_filtered']) * 100.0,
                'p95_relative_error_pct': float(row['p95_relative_error_filtered']) * 100.0,
                'p99_relative_error_pct': float(row['p99_relative_error_filtered']) * 100.0,
                'median_cancellation_ratio': float(row['median_cancellation_ratio']),
                'p99_cancellation_ratio': float(row['p99_cancellation_ratio']),
            })
    out = ROOT / 'results/gaussian_numeric_summary.csv'
    with out.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(selected[0]))
        writer.writeheader()
        writer.writerows(selected)

    gates = []
    styles = sorted({row['accum_style'] for row in rows})
    for style in styles:
        relevant = [
            row for row in rows
            if row['accum_style'] == style and row['dot_length'] == '4096'
        ]
        failures = []
        for row in relevant:
            nrmse = float(row['nrmse']) * 100.0
            p99 = float(row['p99_relative_error_filtered']) * 100.0
            if row['distribution'] == 'gaussian' and (nrmse > 1.25 or p99 > 15.0):
                failures.append(f'{row["input_kind"]}/gaussian nrmse={nrmse:.3f} p99={p99:.3f}')
            if row['distribution'] == 'positive' and nrmse > 1.0:
                failures.append(f'{row["input_kind"]}/positive nrmse={nrmse:.3f}')
            if row['distribution'] == 'outlier' and nrmse > 1.5:
                failures.append(f'{row["input_kind"]}/outlier nrmse={nrmse:.3f}')
        gates.append({
            'accum_style': style,
            'synthetic_gate_pass': int(not failures),
            'failure_count': len(failures),
            'failures': '; '.join(failures),
            'gate_scope': 'K=4096 synthetic proxy only; not target-model accuracy',
        })
    gate_path = ROOT / 'results/synthetic_numeric_gate.csv'
    with gate_path.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(gates[0]))
        writer.writeheader()
        writer.writerows(gates)
    print(f'wrote {out} and {gate_path}')


if __name__ == '__main__':
    main()

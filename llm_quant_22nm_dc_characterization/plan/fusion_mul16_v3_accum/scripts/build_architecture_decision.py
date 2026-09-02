#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STYLE_GROUPS = {
    'full_bf16': 'V3_CLUSTER_FULL_BF16_FULL7',
    'bf16_tree_fp32_recurrent': 'V3_CLUSTER_TREE_FP32_REC_FULL7',
    'bf16_block64_fp32_checkpoint': 'V3_CLUSTER_BLOCK64_FP32_CKPT_FULL7',
}
LATENCY_NOTES = {
    'full_bf16': 'BF16 tree 2 stages + BF16 recurrent update; II=1',
    'bf16_tree_fp32_recurrent': 'BF16 tree 2 stages + FP32 recurrent update; II=1 only if recurrence closes',
    'bf16_block64_fp32_checkpoint': 'BF16 tree + BF16 partial; FP32 checkpoint uses 2-cycle multicycle path; stream II=1',
}


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--dc', default=str(ROOT / 'results/local_dc/v3_area_1ghz.csv'))
    parser.add_argument('--numeric', default=str(ROOT / 'results/accum_error_comparison.csv'))
    parser.add_argument('--gates', default=str(ROOT / 'results/synthetic_numeric_gate.csv'))
    args = parser.parse_args()

    dc = {row['group_id']: row for row in read_csv(Path(args.dc))}
    numeric_rows = read_csv(Path(args.numeric))
    gates = {row['accum_style']: row for row in read_csv(Path(args.gates))}

    rows = []
    for style, group in STYLE_GROUPS.items():
        d = dc[group]
        metrics = {
            (row['input_kind'], row['distribution'], row['dot_length']): row
            for row in numeric_rows if row['accum_style'] == style
        }
        fp8 = metrics[('fp8_proxy', 'gaussian', '4096')]
        bf16 = metrics[('bf16', 'gaussian', '4096')]
        timing_met = int(float(d['timing_met']))
        synthetic_pass = int(gates[style]['synthetic_gate_pass'])
        rows.append({
            'accum_style': style,
            'full_cluster_group': group,
            'area_1ghz_um2': num(d['mapped_cell_area_um2']),
            'wns_1ghz_ns': num(d['wns_ns']),
            'timing_met_1ghz': timing_met,
            'synthetic_gate_pass': synthetic_pass,
            'fp8_k4096_nrmse_pct': float(fp8['nrmse']) * 100.0,
            'fp8_k4096_p99_pct': float(fp8['p99_relative_error_filtered']) * 100.0,
            'bf16_k4096_nrmse_pct': float(bf16['nrmse']) * 100.0,
            'bf16_k4096_p99_pct': float(bf16['p99_relative_error_filtered']) * 100.0,
            'multicycle_applied': int(float(d.get('multicycle_applied') or 0)),
            'pareto_eligible_synthetic': int(timing_met and synthetic_pass),
            'latency_and_ii': LATENCY_NOTES[style],
            'target_model_accuracy': 'OPEN',
        })

    eligible = [row for row in rows if row['pareto_eligible_synthetic']]
    selected = min(eligible, key=lambda row: row['area_1ghz_um2']) if eligible else None
    output_dir = ROOT / 'results/local_dc'
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / 'v3_architecture_comparison.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    decision = {
        'status': 'PROVISIONAL_SYNTHETIC_SELECTION' if selected else 'NO_ELIGIBLE_STYLE',
        'selected_style': selected['accum_style'] if selected else None,
        'selected_group': selected['full_cluster_group'] if selected else None,
        'selection_rule': 'lowest 1GHz mapped-cell area among timing-closed styles passing the synthetic K=4096 gate',
        'target_model_accuracy_gate': 'OPEN; final selection is not valid until target-model layer/logit regression passes',
        'rows': rows,
    }
    (output_dir / 'v3_architecture_decision.json').write_text(
        json.dumps(decision, indent=2), encoding='utf-8'
    )
    print(json.dumps(decision, indent=2))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with (ROOT / 'results/gaussian_numeric_summary.csv').open(encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    labels = {
        'full_bf16': 'Full BF16 accumulation',
        'bf16_tree_fp32_recurrent': 'BF16 tree + FP32 recurrent',
        'bf16_block64_fp32_checkpoint': 'BF16 Kblock64 + FP32 checkpoint',
    }

    for input_kind, metric, ylabel, filename in [
        ('fp8_proxy', 'nrmse_pct', 'NRMSE (%)', 'fp8_proxy_gaussian_nrmse.png'),
        ('fp8_proxy', 'p99_relative_error_pct', 'Filtered P99 relative error (%)', 'fp8_proxy_gaussian_p99.png'),
        ('bf16', 'nrmse_pct', 'NRMSE (%)', 'bf16_gaussian_nrmse.png'),
        ('bf16', 'p99_relative_error_pct', 'Filtered P99 relative error (%)', 'bf16_gaussian_p99.png'),
    ]:
        fig, ax = plt.subplots(figsize=(9.5, 6.0))
        for style in labels:
            selected = sorted(
                [r for r in rows if r['input_kind'] == input_kind and r['accum_style'] == style],
                key=lambda r: int(r['dot_length']),
            )
            ax.plot(
                [int(r['dot_length']) for r in selected],
                [float(r[metric]) for r in selected],
                marker='o',
                label=labels[style],
            )
        ax.set_xscale('log', base=2)
        ax.set_xticks([128, 1024, 4096], ['128', '1024', '4096'])
        ax.set_xlabel('Dot length K')
        ax.set_ylabel(ylabel)
        ax.set_title(f'{input_kind}: Gaussian dot accumulation error')
        ax.grid(True, linewidth=0.5)
        ax.legend()
        fig.tight_layout()
        fig.savefig(ROOT / 'results' / filename, dpi=200, bbox_inches='tight')
        plt.close(fig)
    print('numeric plots generated')


if __name__ == '__main__':
    main()

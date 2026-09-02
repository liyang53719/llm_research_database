#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_kv(path: Path) -> dict[str, str]:
    return {line.split('=', 1)[0]: line.split('=', 1)[1].strip()
            for line in path.read_text(encoding='utf-8', errors='ignore').splitlines()
            if '=' in line}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('run_dir')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    run_dir = Path(args.run_dir).resolve()
    summary = parse_kv(run_dir / 'summary.kv')
    operators: list[str] = []
    wide_fp_add: list[str] = []
    rtl_list = run_dir / 'rtl_files.list'
    paths = [Path(line.strip()) for line in rtl_list.read_text().splitlines() if line.strip()]
    for path in paths:
        if path.suffix != '.sv':
            continue
        text = re.sub(r'/\*.*?\*/', '', path.read_text(encoding='utf-8', errors='ignore'), flags=re.S)
        text = re.sub(r'//.*', '', text)
        if re.search(r'\s\*\s', text):
            operators.append(path.name)
        if re.search(r'DW_fp_add\s*#\s*\(\s*23\s*,\s*8', text):
            wide_fp_add.append(path.name)
    report = ''
    for name in ('report_resources_pre.rpt', 'report_resources_post.rpt',
                 'report_reference_pre.rpt', 'report_reference_post.rpt'):
        path = run_dir / 'reports' / name
        if path.exists():
            report += path.read_text(encoding='utf-8', errors='ignore')
    report_wide_fp_add = len(re.findall(r'\bDW_fp_add\b[^\n]*sig_width=23', report))
    result = {
        'brick_instance_count_precompile': int(float(summary.get('brick_instance_count_precompile', -1))),
        'dw_mult_4x4_instance_count_precompile': int(float(summary.get('dw_mult_instance_count_precompile', -1))),
        'blackbox_count': int(float(summary.get('blackbox_count', -1))),
        'mapped_cell_area_um2': float(summary.get('mapped_cell_area_um2', 0.0)),
        'source_multiply_operator_files': operators,
        'source_wide_fp32_adder_files': wide_fp_add,
        'report_wide_fp32_adder_rows': report_wide_fp_add,
    }
    result['additional_multiplier_operations'] = (
        max(0, len(operators) - 1) + result['report_wide_fp32_adder_rows'])
    result['pass'] = (
        result['brick_instance_count_precompile'] == 16
        and result['dw_mult_4x4_instance_count_precompile'] == 16
        and result['blackbox_count'] == 0
        and result['mapped_cell_area_um2'] > 0
        and operators == ['mul4x4_brick.sv']
        and not wide_fp_add
        and result['report_wide_fp32_adder_rows'] == 0
    )
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    if not result['pass']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()

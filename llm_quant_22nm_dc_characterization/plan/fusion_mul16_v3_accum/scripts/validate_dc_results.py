#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', default=str(ROOT / 'results/local_dc/v3_area_1ghz.csv'))
    parser.add_argument('--vcs', default=str(ROOT / 'results/vcs_crosscheck_summary.csv'))
    args = parser.parse_args()
    cfg = json.loads((ROOT / 'config/characterization_1ghz.json').read_text())
    with (ROOT / 'config/dc_experiments_1ghz.csv').open(encoding='utf-8-sig') as f:
        experiments = list(csv.DictReader(f))
    expected = {row['group_id']: row for row in experiments}
    with Path(args.raw).open(encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    errors = []
    warnings = []
    if len(rows) != cfg['expected_runs']:
        errors.append(f'expected {cfg["expected_runs"]} rows, found {len(rows)}')
    if set(by := {row['group_id']: row for row in rows}) != set(expected):
        errors.append('group set mismatch')
    libraries = {row.get('library_set_id') for row in rows}
    if libraries != {cfg['library_set_id']}:
        errors.append(f'library set mismatch: {libraries}')
    for row in rows:
        run = row['run_id']
        if row.get('status') != 'ok':
            errors.append(f'{run}: status={row.get("status")}')
        if row.get('rtl_input_sha256') != row.get('rtl_input_sha256_reported') or not row.get('rtl_input_sha256'):
            errors.append(f'{run}: RTL input hash mismatch')
        if row.get('compile_mode') != 'ultra' or row.get('compile_mode_reported') != 'ultra':
            errors.append(f'{run}: compile mode mismatch')
        if float(row.get('dc_max_cores') or 0) != 1:
            errors.append(f'{run}: dc cores mismatch')
        if int(float(row.get('dc_error_count') or 0)) != 0:
            errors.append(f'{run}: DC errors={row.get("dc_error_count")}')
        if int(float(row.get('reports_complete') or 0)) != 1:
            errors.append(f'{run}: incomplete reports')
        try:
            if float(row['mapped_cell_area_um2']) <= 0:
                errors.append(f'{run}: non-positive area')
        except Exception:
            errors.append(f'{run}: missing area')
        if str(row.get('blackbox_count')) not in {'0', '0.0'}:
            errors.append(f'{run}: blackbox={row.get("blackbox_count")}')
        if abs(float(row['clock_period_ns']) - 1.0) > 1e-12:
            errors.append(f'{run}: clock period is not 1.0 ns')
        expected_mc = 1 if row['constraint_profile'] == 'checkpoint_mc2' else 0
        if int(float(row.get('multicycle_applied') or 0)) != expected_mc:
            errors.append(f'{run}: multicycle application mismatch')
        if row.get('timing_met') not in {'1', 1, 1.0, '1.0'}:
            warnings.append(f'{run}: 1GHz timing fail')
        if int(float(row.get('constraint_violator_lines') or 0)):
            warnings.append(f'{run}: constraint violators present')
        exp = expected.get(run)
        if exp is not None:
            wanted_bricks = 0 if exp['top_kind'].startswith('accum_') else 16
            if float(row.get('brick_instance_count_precompile') or -1) != wanted_bricks:
                errors.append(f'{run}: brick count expected {wanted_bricks}')
            if float(row.get('dw_mult_instance_count_precompile') or -1) != wanted_bricks:
                errors.append(f'{run}: DW multiplier count expected {wanted_bricks}')
            if float(row.get('bf16_add_rows') or -1) != float(exp['expected_fp_add_bf16']):
                errors.append(f'{run}: BF16 adder rows expected {exp["expected_fp_add_bf16"]}')
            if float(row.get('fp32_add_rows') or -1) != float(exp['expected_fp_add_fp32']):
                errors.append(f'{run}: FP32 adder rows expected {exp["expected_fp_add_fp32"]}')
            wanted_mc = 1 if exp['constraint_profile'] == 'checkpoint_mc2' else 0
            if float(row.get('multicycle_applied') or -1) != wanted_mc:
                errors.append(f'{run}: multicycle application mismatch')

    vcs_path = Path(args.vcs)
    if not vcs_path.exists():
        errors.append('missing VCS crosscheck summary')
    else:
        with vcs_path.open(encoding='utf-8-sig') as f:
            vcs_rows = list(csv.DictReader(f))
        if len(vcs_rows) != 15 or any(row.get('passed') not in {'1', 1, True, 'True'} for row in vcs_rows):
            errors.append('VCS accumulator crosscheck did not pass 15/15 cases')

    mc = (ROOT / 'config/checkpoint_multicycle.tcl').read_text(encoding='utf-8')
    if 'set_multicycle_path 2 -setup' not in mc or 'set_multicycle_path 1 -hold' not in mc:
        errors.append('checkpoint multicycle Tcl missing setup=2/hold=1')

    report = ROOT / 'results/local_dc/validation_report.txt'
    report.write_text(
        'ERRORS\n' + ('\n'.join(errors) if errors else 'NONE')
        + '\n\nWARNINGS\n' + ('\n'.join(warnings) if warnings else 'NONE') + '\n',
        encoding='utf-8'
    )
    print(report.read_text())
    if errors:
        raise SystemExit(2)


if __name__ == '__main__':
    main()

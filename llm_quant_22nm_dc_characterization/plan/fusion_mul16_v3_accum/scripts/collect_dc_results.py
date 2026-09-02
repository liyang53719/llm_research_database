#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_REPORTS = ('report_area.rpt','report_qor.rpt','report_timing.rpt','report_resources.rpt','report_reference.rpt','report_exceptions.rpt','check_design_post.rpt')


def parse_kv(path: Path) -> dict[str, str]:
    data = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            data[key.strip()] = value.strip()
    return data


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def report_value(text: str, pattern: str):
    match = re.search(pattern, text)
    return number(match.group(1)) if match else None


def count_dw_add_rows(text: str) -> tuple[int, int]:
    bf16 = fp32 = 0
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not re.search(r'\bDW_fp_add\b', line): continue
        context = '\n'.join(lines[index:index + 8])
        sig = re.search(r'sig_width=([0-9]+)', context)
        exp = re.search(r'exp_width=([0-9]+)', context)
        if sig and exp and sig.group(1) == '7' and exp.group(1) == '8': bf16 += 1
        elif sig and exp and sig.group(1) == '23' and exp.group(1) == '8': fp32 += 1
    return bf16, fp32


def source_operator_files(rtl_list: Path) -> tuple[list[str], list[str]]:
    multiply, fp_mult = [], []
    if not rtl_list.exists(): return multiply, fp_mult
    for entry in rtl_list.read_text(encoding='utf-8', errors='ignore').splitlines():
        path = Path(entry.strip())
        if not path.exists() or path.suffix != '.sv': continue
        text = re.sub(r'/\*.*?\*/', '', path.read_text(encoding='utf-8', errors='ignore'), flags=re.S)
        text = re.sub(r'//.*', '', text)
        if re.search(r'\s\*\s', text): multiply.append(path.name)
        if 'DW_fp_mult' in text: fp_mult.append(path.name)
    return sorted(set(multiply)), sorted(set(fp_mult))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-dir', default=str(ROOT / 'build_dc_1ghz'))
    parser.add_argument('--output', default=str(ROOT / 'results/local_dc/v3_area_1ghz.csv'))
    args = parser.parse_args()
    rows = []
    for meta_path in sorted(Path(args.build_dir).glob('*/meta.json')):
        run_dir = meta_path.parent
        meta = json.loads(meta_path.read_text())
        kv = parse_kv(run_dir / 'summary.kv')
        area_text = (run_dir / 'reports/report_area.rpt').read_text(errors='ignore') if (run_dir / 'reports/report_area.rpt').exists() else ''
        constraint_text = (run_dir / 'reports/report_constraints.rpt').read_text(errors='ignore') if (run_dir / 'reports/report_constraints.rpt').exists() else ''
        reference_text = (run_dir / 'reports/report_reference.rpt').read_text(errors='ignore') if (run_dir / 'reports/report_reference.rpt').exists() else ''
        resource_text = (run_dir / 'reports/report_resources.rpt').read_text(errors='ignore') if (run_dir / 'reports/report_resources.rpt').exists() else ''
        stdout_text = (run_dir / 'dc_stdout.log').read_text(errors='ignore') if (run_dir / 'dc_stdout.log').exists() else ''
        bf16_add_rows, fp32_add_rows = count_dw_add_rows(resource_text)
        multiply_files, fp_mult_files = source_operator_files(run_dir / 'rtl_files.list')
        reports_complete = all((run_dir / 'reports' / name).exists() for name in REQUIRED_REPORTS)
        row = {
            **meta,
            'library_set_id': kv.get('library_set_id', ''),
            'compile_mode': kv.get('compile_mode', ''),
            'compile_mode_reported': kv.get('compile_mode', ''),
            'mapped_cell_area_um2': number(kv.get('mapped_cell_area_um2')),
            'combinational_area_um2': report_value(area_text, r'Combinational area:\s*([0-9eE+\-.]+)'),
            'noncombinational_area_um2': report_value(area_text, r'Noncombinational area:\s*([0-9eE+\-.]+)'),
            'buf_inv_area_um2': report_value(area_text, r'Buf/Inv area:\s*([0-9eE+\-.]+)'),
            'leaf_cell_count': number(kv.get('leaf_cell_count')),
            'blackbox_count': number(kv.get('blackbox_count')),
            'brick_instance_count_precompile': number(kv.get('brick_instance_count_precompile')),
            'dw_mult_instance_count_precompile': number(kv.get('dw_mult_instance_count_precompile')),
            'dw_mult_4x4_rows': number(kv.get('dw_mult_instance_count_precompile')),
            'other_multiplier_rows': 0 if multiply_files == ['mul4x4_brick.sv'] and not fp_mult_files else None,
            'bf16_add_rows': bf16_add_rows,
            'fp32_add_rows': fp32_add_rows,
            'source_multiply_operator_files': ';'.join(multiply_files),
            'source_fp_mult_files': ';'.join(fp_mult_files),
            'wns_ns': number(kv.get('wns_ns')),
            'critical_delay_ns': number(kv.get('critical_delay_ns')),
            'achieved_fmax_mhz': number(kv.get('achieved_fmax_mhz')),
            'timing_met': int(float(kv['timing_met'])) if kv.get('timing_met') not in ('', None, 'NA') else None,
            'multicycle_applied': int(float(kv.get('multicycle_applied', 0))),
            'tool_version': kv.get('tool_version', ''),
            'constraint_violator_lines': sum(1 for line in constraint_text.splitlines() if 'VIOLATED' in line),
            'dc_error_count': len(re.findall(r'^Error(?::|-\[)', stdout_text, flags=re.M)),
            'rtl_input_sha256_reported': kv.get('rtl_input_sha256', ''),
            'library_setup_sha256': kv.get('library_setup_sha256', ''),
            'dc_max_cores': number(kv.get('dc_max_cores')),
            'multicycle_source': kv.get('extra_constraint_tcl', ''),
            'reports_complete': int(reports_complete),
            'status': 'ok' if kv and reports_complete else 'missing_evidence',
            'report_dir': str((run_dir / 'reports').resolve()),
        }
        rows.append(row)
    if not rows:
        raise SystemExit('no results found')
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with output.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f'wrote {len(rows)} rows to {output}')


if __name__ == '__main__':
    main()

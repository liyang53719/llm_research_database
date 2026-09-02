#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def parse_kv(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            result[key.strip()] = value.strip()
    return result


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def regex_number(text: str, pattern: str):
    match = re.search(pattern, text, flags=re.M)
    return number(match.group(1)) if match else None


def count_resource_rows(text: str) -> dict[str, int]:
    result = {
        'dw_mult_4x4_rows': 0,
        'other_multiplier_rows': 0,
        'bf16_add_rows': 0,
        'fp32_add_rows': 0,
    }
    lines = text.splitlines()
    for index, line in enumerate(lines):
        context = '\n'.join(lines[index:index + 8])
        if 'DW_mult_uns' in line:
            aw = re.search(r'a_width=([0-9]+)', context)
            bw = re.search(r'b_width=([0-9]+)', context)
            if aw and bw and aw.group(1) == '4' and bw.group(1) == '4':
                result['dw_mult_4x4_rows'] += 1
            elif aw and bw:
                result['other_multiplier_rows'] += 1
        if re.search(r'\bDW_fp_add\b', line):
            sig = re.search(r'sig_width=([0-9]+)', context)
            exp = re.search(r'exp_width=([0-9]+)', context)
            if sig and exp and sig.group(1) == '7' and exp.group(1) == '8':
                result['bf16_add_rows'] += 1
            elif sig and exp and sig.group(1) == '23' and exp.group(1) == '8':
                result['fp32_add_rows'] += 1
    return result


def count_source_fp_adds(root: Path, rtl_list: Path) -> tuple[int, int]:
    text = ''
    if rtl_list.exists():
        for entry in rtl_list.read_text(encoding='utf-8', errors='ignore').splitlines():
            path = Path(entry.strip())
            if path.exists():
                text += path.read_text(encoding='utf-8', errors='ignore')
    bf16 = len(re.findall(r'DW_fp_add\s*#\s*\(\s*7\s*,\s*8', text))
    fp32 = len(re.findall(r'DW_fp_add\s*#\s*\(\s*23\s*,\s*8', text))
    return bf16, fp32


def parse_timing(text: str) -> dict[str, str | float | None]:
    start = re.search(r'^\s*Startpoint:\s*(.+)$', text, flags=re.M)
    end = re.search(r'^\s*Endpoint:\s*(.+)$', text, flags=re.M)
    group = re.search(r'^\s*Path Group:\s*(.+)$', text, flags=re.M)
    path_type = re.search(r'^\s*Path Type:\s*(.+)$', text, flags=re.M)
    slack = re.search(r'^\s*slack\s+\([^)]*\)\s+(-?[0-9.eE+]+)', text, flags=re.M)
    if not slack:
        slack = re.search(r'^\s*slack\s+(-?[0-9.eE+]+)', text, flags=re.M)
    return {
        'critical_startpoint': start.group(1).strip() if start else '',
        'critical_endpoint': end.group(1).strip() if end else '',
        'critical_path_group': group.group(1).strip() if group else '',
        'critical_path_type': path_type.group(1).strip() if path_type else '',
        'reported_slack_ns': number(slack.group(1)) if slack else None,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-dir', default='build_dc_1ghz')
    parser.add_argument('--output-dir', default='results/local_dc')
    args = parser.parse_args()
    build = ROOT / args.build_dir
    out = ROOT / args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    critical_rows: list[dict] = []
    for meta_path in sorted(build.glob('*/meta.json')):
        run_dir = meta_path.parent
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        kv = parse_kv(run_dir / 'summary.kv')
        resource_path = run_dir / 'reports/report_resources_post.rpt'
        area_path = run_dir / 'reports/report_area.rpt'
        timing_path = run_dir / 'reports/report_timing.rpt'
        resource_text = resource_path.read_text(encoding='utf-8', errors='ignore') if resource_path.exists() else ''
        area_text = area_path.read_text(encoding='utf-8', errors='ignore') if area_path.exists() else ''
        timing_text = timing_path.read_text(encoding='utf-8', errors='ignore') if timing_path.exists() else ''
        stdout_path = run_dir / 'dc_stdout.log'
        stdout_text = stdout_path.read_text(encoding='utf-8', errors='ignore') if stdout_path.exists() else ''
        counts = count_resource_rows(resource_text)
        source_bf16_adds, source_fp32_adds = count_source_fp_adds(ROOT, run_dir / 'rtl_files.list')
        timing = parse_timing(timing_text)
        dc_error_count = len(re.findall(r'^Error(?::|-\[)', stdout_text, flags=re.M))
        reports_complete = all((run_dir / 'reports' / name).exists() for name in
                               ('report_area.rpt','report_timing.rpt','report_resources_pre.rpt',
                                'report_reference_pre.rpt','report_resources_post.rpt',
                                'report_reference_post.rpt','check_design_post.rpt'))
        row = {
            **meta,
            'library_set_id': kv.get('library_set_id', ''),
            'mapped_cell_area_um2': number(kv.get('mapped_cell_area_um2')),
            'combinational_area_um2': regex_number(area_text, r'^Combinational area:\s*([0-9.eE+-]+)'),
            'noncombinational_area_um2': regex_number(area_text, r'^Noncombinational area:\s*([0-9.eE+-]+)'),
            'buf_inv_area_um2': regex_number(area_text, r'^Buf/Inv area:\s*([0-9.eE+-]+)'),
            'leaf_cell_count': number(kv.get('leaf_cell_count')),
            'blackbox_count': number(kv.get('blackbox_count')),
            'brick_instance_count_precompile': number(kv.get('brick_instance_count_precompile')),
            'dw_mult_instance_count_precompile': number(kv.get('dw_mult_instance_count_precompile')),
            **counts,
            'source_bf16_add_instances': source_bf16_adds,
            'source_fp32_add_instances': source_fp32_adds,
            'wns_ns': number(kv.get('wns_ns')),
            'critical_delay_ns': number(kv.get('critical_delay_ns')),
            'achieved_fmax_mhz': number(kv.get('achieved_fmax_mhz')),
            'timing_met': int(float(kv['timing_met'])) if kv.get('timing_met') not in (None, '', 'NA') else None,
            **timing,
            'dc_error_count': dc_error_count,
            'tool_version': kv.get('tool_version', ''),
            'rtl_input_sha256_reported': kv.get('rtl_input_sha256', ''),
            'library_setup_sha256': kv.get('library_setup_sha256', ''),
            'dc_max_cores': number(kv.get('dc_max_cores')),
            'compile_mode_reported': kv.get('compile_mode', ''),
            'input_transition': number(kv.get('input_transition')),
            'output_load': number(kv.get('output_load')),
            'max_transition': number(kv.get('max_transition')),
            'clock_uncertainty_ratio': number(kv.get('clock_uncertainty_ratio')),
            'input_delay_ratio': number(kv.get('input_delay_ratio')),
            'output_delay_ratio': number(kv.get('output_delay_ratio')),
            'status': 'ok' if kv and reports_complete else 'missing_evidence',
            'report_dir': str((run_dir / 'reports').resolve()),
        }
        rows.append(row)
        critical_rows.append({
            'group_id': row['group_id'],
            'wns_ns': row['wns_ns'],
            'critical_delay_ns': row['critical_delay_ns'],
            'achieved_fmax_mhz': row['achieved_fmax_mhz'],
            'timing_met': row['timing_met'],
            'critical_startpoint': row['critical_startpoint'],
            'critical_endpoint': row['critical_endpoint'],
            'critical_path_group': row['critical_path_group'],
            'critical_path_type': row['critical_path_type'],
        })

    if not rows:
        raise SystemExit('No DC results found')
    write_csv(out / 'fusion16_v2_area_1ghz.csv', rows)
    write_csv(out / 'critical_path_summary.csv', critical_rows)
    print(f'Wrote {len(rows)} area rows and {len(critical_rows)} critical-path rows')


if __name__ == '__main__':
    main()

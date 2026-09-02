#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--vcs', default='vcs')
    parser.add_argument('--manifest', default=str(ROOT / 'results/vcs_vectors/manifest.csv'))
    parser.add_argument('--output', default=str(ROOT / 'results/vcs_crosscheck_summary.csv'))
    args = parser.parse_args()

    build = ROOT / 'build_vcs'
    build.mkdir(exist_ok=True)
    simv = build / 'simv'
    dw_sim = os.environ.get('DW_SIM', '')
    if not dw_sim and os.environ.get('SYNOPSYS'):
        dw_sim = str(Path(os.environ['SYNOPSYS']) / 'dw/sim_ver')
    if not dw_sim or not Path(dw_sim).is_dir():
        raise SystemExit('Set DW_SIM or SYNOPSYS to the DesignWare sim_ver directory')
    rtl = [
        ROOT / 'rtl/fusion_mul16_v3_bf16_tree_dw.sv',
        ROOT / 'rtl/fusion_mul16_v3_accum_full_bf16_dw.sv',
        ROOT / 'rtl/fusion_mul16_v3_accum_fp32_recurrent_dw.sv',
        ROOT / 'rtl/fusion_mul16_v3_accum_block64_fp32_checkpoint_dw.sv',
        ROOT / 'rtl/fusion_mul16_v3_accum_compare.sv',
        ROOT / 'tb/fusion_mul16_v3_accum_compare_tb.sv',
    ]
    compile_cmd = [
        args.vcs, '-full64', '-sverilog', '-timescale=1ns/1ps',
        '-y', dw_sim, '+libext+.v',
        '-o', str(simv), *map(str, rtl)
    ]
    subprocess.run(compile_cmd, cwd=ROOT, check=True)

    with Path(args.manifest).open(encoding='utf-8-sig') as f:
        cases = list(csv.DictReader(f))
    rows = []
    for case in cases:
        vector_path = ROOT / 'results/vcs_vectors' / case['vector_file']
        cmd = [
            str(simv),
            f'+VECTORS={vector_path}',
            f'+CYCLES={case["cycles"]}',
            f'+ITEMS={case["items_per_cycle"]}',
            f'+FLUSH={case["needs_flush"]}',
        ]
        for lane in range(4):
            cmd += [
                f'+FULL{lane}={case[f"full_bf16_lane{lane}"]}',
                f'+FP32{lane}={case[f"fp32_recurrent_lane{lane}"]}',
                f'+BLOCK{lane}={case[f"block64_checkpoint_lane{lane}"]}',
            ]
        proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
        passed = proc.returncode == 0 and 'PASS ' in proc.stdout and 'FAIL ' not in proc.stdout
        rows.append({
            **case,
            'returncode': proc.returncode,
            'passed': int(passed),
            'stdout_tail': '\n'.join(proc.stdout.splitlines()[-8:]),
            'stderr_tail': '\n'.join(proc.stderr.splitlines()[-8:]),
        })
        if not passed:
            raise SystemExit(f'VCS failure for case {case["case_id"]}:\n{proc.stdout}\n{proc.stderr}')

    output = Path(args.output)
    with output.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f'VCS passed {len(rows)}/{len(rows)} cases')


if __name__ == '__main__':
    main()

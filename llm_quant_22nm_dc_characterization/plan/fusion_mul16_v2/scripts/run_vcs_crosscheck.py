#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], cwd: Path, log: Path) -> str:
    process = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    text = process.stdout + process.stderr
    log.write_text(text, encoding='utf-8')
    if process.returncode:
        raise SystemExit(f"Command failed ({process.returncode}): {' '.join(command)}\n{text}")
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--vcs', default='vcs')
    parser.add_argument('--per-mode', type=int, default=512)
    parser.add_argument('--work-dir', default='build_sim_v2')
    args = parser.parse_args()
    work = ROOT / args.work_dir
    work.mkdir(parents=True, exist_ok=True)

    run([
        'python3', str(ROOT/'scripts/gen_vcs_vectors.py'),
        '--per-mode', str(args.per_mode), '--output-dir', 'results/vcs_vectors'
    ], ROOT, work/'gen_vectors.log')

    product_sources = [
        ROOT/'rtl/fusion_mul16_v2_pkg.sv',
        ROOT/'rtl/mul4x4_brick.sv',
        ROOT/'rtl/raw16_to_bf16_rne.sv',
        ROOT/'rtl/fusion_mul16_v2_product_pipe.sv',
        ROOT/'tb/fusion_mul16_v2_product_pipe_tb.sv',
    ]
    simv_product = work/'simv_product'
    run([args.vcs, '-full64', '-sverilog', '-timescale=1ns/1ps',
         '-top', 'fusion_mul16_v2_product_pipe_tb', '-o', str(simv_product)]
        + [str(x) for x in product_sources], ROOT, work/'compile_product.log')

    total_vectors = 0
    for path in sorted((ROOT/'results/vcs_vectors').glob('*.vec')):
        mode = int(path.name.split('_', 1)[0])
        text = run([str(simv_product), f'+MODE={mode}', f'+VECTORS={path}'],
                   ROOT, work/f'run_mode_{mode}.log')
        match = re.search(r'PASS mode=(\d+) vectors=(\d+) failures=0', text)
        if not match:
            raise SystemExit(f'Missing PASS signature for mode {mode}')
        total_vectors += int(match.group(2))

    config_sources = [
        ROOT/'rtl/fusion_mul16_v2_pkg.sv',
        ROOT/'rtl/fusion_mul16_v2_config.sv',
        ROOT/'tb/fusion_mul16_v2_config_tb.sv',
    ]
    simv_config = work/'simv_config'
    run([args.vcs, '-full64', '-sverilog', '-timescale=1ns/1ps',
         '-top', 'fusion_mul16_v2_config_tb', '-o', str(simv_config)]
        + [str(x) for x in config_sources], ROOT, work/'compile_config.log')
    text = run([str(simv_config)], ROOT, work/'run_config.log')
    if 'PASS config_protocol failures=0' not in text:
        raise SystemExit('Configuration protocol test failed')

    print(f'PASS: {total_vectors} product vectors across 7 modes; config protocol PASS')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_REPORTS = ('report_area.rpt','report_qor.rpt','report_timing.rpt','report_resources.rpt','report_reference.rpt','report_exceptions.rpt','check_design_post.rpt')

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def complete(run_dir: Path, row: dict) -> bool:
    summary=run_dir/'summary.kv'
    if not summary.exists() or not all((run_dir/'reports'/name).exists() for name in REQUIRED_REPORTS): return False
    kv={line.split('=',1)[0]:line.split('=',1)[1].strip() for line in summary.read_text(errors='ignore').splitlines() if '=' in line}
    return kv.get('rtl_input_sha256')==row.get('rtl_input_sha256')


def run_one(row, dc_shell, lib_setup, force, cpus, max_cores):
    run_dir = Path(row['run_dir'])
    summary = run_dir / 'summary.kv'
    if complete(run_dir,row) and not force:
        return row['run_id'], 0, 'SKIP'
    env = os.environ.copy()
    env.update({
        'RUN_ID': row['run_id'],
        'RUN_DIR': str(run_dir),
        'RTL_LIST': str(run_dir / 'rtl_files.list'),
        'LIB_SETUP': str(lib_setup),
        'CLK_PERIOD_NS': '1.0',
        'EXTRA_CONSTRAINT_TCL': row.get('extra_constraint_tcl', ''),
        'RTL_INPUT_SHA256': row['rtl_input_sha256'],
        'DC_MAX_CORES': str(max_cores),
        'LIBRARY_SETUP_SHA256': sha256(lib_setup),
    })
    log = run_dir / 'dc_stdout.log'
    with log.open('w', encoding='utf-8') as f:
        proc = subprocess.run(
            ['taskset','-c',cpus,dc_shell, '-64bit', '-f', str(ROOT / 'scripts/dc_synth_v3.tcl')],
            cwd=run_dir,
            env=env,
            stdout=f,
            stderr=subprocess.STDOUT,
        )
    return row['run_id'], proc.returncode, 'RUN'


def main():
    global ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-dir', default=str(ROOT / 'build_dc_1ghz'))
    parser.add_argument('--lib-setup', required=True)
    parser.add_argument('--dc-shell', default=os.environ.get('DC_SHELL', 'dc_shell'))
    parser.add_argument('--jobs', type=int, default=1)
    parser.add_argument('--root', default=str(ROOT))
    parser.add_argument('--max-cores', type=int, default=1)
    parser.add_argument('--cpus', default='8-23')
    parser.add_argument('--run-id', action='append', default=[])
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    ROOT = Path(args.root).resolve()
    if args.jobs < 1 or args.max_cores < 1 or args.jobs * args.max_cores > 2 or args.cpus != '8-23':
        raise SystemExit('Require jobs>=1, max-cores>=1, jobs*max-cores<=2, cpus=8-23')
    manifest = Path(args.build_dir) / 'runs.csv'
    with manifest.open(encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    if args.run_id:
        wanted=set(args.run_id); rows=[r for r in rows if r['run_id'] in wanted]
        if wanted-{r['run_id'] for r in rows}: raise SystemExit('Unknown run id')
    failures = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [
            pool.submit(run_one, row, args.dc_shell, Path(args.lib_setup).resolve(), args.force, args.cpus, args.max_cores)
            for row in rows
        ]
        for future in as_completed(futures):
            run_id, rc, action = future.result()
            print(f'[{action}] {run_id}: rc={rc}', flush=True)
            if rc:
                failures.append(run_id)
    if failures:
        raise SystemExit('failed runs:\n' + '\n'.join(failures))


if __name__ == '__main__':
    main()

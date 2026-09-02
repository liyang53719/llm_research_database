#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REQUIRED_REPORTS=('report_area.rpt','report_timing.rpt','report_resources_pre.rpt','report_reference_pre.rpt','report_resources_post.rpt','report_reference_post.rpt','check_design_post.rpt')

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def complete(run_dir: Path, row: dict) -> bool:
    summary=run_dir/'summary.kv'
    if not summary.exists() or not all((run_dir/'reports'/name).exists() for name in REQUIRED_REPORTS): return False
    kv={line.split('=',1)[0]:line.split('=',1)[1].strip() for line in summary.read_text(errors='ignore').splitlines() if '=' in line}
    return kv.get('rtl_input_sha256')==row.get('rtl_input_sha256')


def run_one(row,lib_setup,dc_shell,force,cpus,max_cores):
    run_dir=Path(row['run_dir'])
    if complete(run_dir,row) and not force:
        return row['run_id'],0,'SKIP'
    env=os.environ.copy()
    env.update({'RUN_ID':row['run_id'],'RUN_DIR':str(run_dir),
                'RTL_LIST':str(run_dir/'rtl_files.list'),'LIB_SETUP':str(lib_setup),
                'TOP':row['top_module'],'KEEP_BRICKS':str(row['keep_bricks']),
                'RTL_INPUT_SHA256':row['rtl_input_sha256'],'DC_MAX_CORES':str(max_cores),
                'LIBRARY_SETUP_SHA256':sha256(lib_setup)})
    with (run_dir/'dc_stdout.log').open('w',encoding='utf-8') as log:
        p=subprocess.run(['taskset','-c',cpus,dc_shell,'-64bit','-f',str(ROOT/'scripts/dc_synth_v2.tcl')],
                         cwd=run_dir,env=env,stdout=log,stderr=subprocess.STDOUT)
    return row['run_id'],p.returncode,'RUN'


def main():
    global ROOT
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',default=str(ROOT))
    ap.add_argument('--build-dir',default='build_dc_1ghz')
    ap.add_argument('--lib-setup',required=True)
    ap.add_argument('--dc-shell',default=os.environ.get('DC_SHELL','dc_shell'))
    ap.add_argument('--jobs',type=int,default=1)
    ap.add_argument('--max-cores',type=int,default=1)
    ap.add_argument('--cpus',default='8-23')
    ap.add_argument('--run-id',action='append',default=[])
    ap.add_argument('--force',action='store_true')
    a=ap.parse_args()
    ROOT=Path(a.root).resolve()
    if a.jobs<1 or a.max_cores<1 or a.jobs*a.max_cores>2 or a.cpus!='8-23': raise SystemExit('Require jobs>=1, max-cores>=1, jobs*max-cores<=2, cpus=8-23')
    with (ROOT/a.build_dir/'runs.csv').open(encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    if a.run_id:
        wanted=set(a.run_id); rows=[r for r in rows if r['run_id'] in wanted]
        if wanted-{r['run_id'] for r in rows}: raise SystemExit('Unknown run id')
    lib=Path(a.lib_setup).resolve()
    failures=[]
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        futures=[pool.submit(run_one,r,lib,a.dc_shell,a.force,a.cpus,a.max_cores) for r in rows]
        for fut in as_completed(futures):
            rid,rc,action=fut.result(); print(f'[{action}] {rid}: rc={rc}',flush=True)
            if rc: failures.append(rid)
    if failures: raise SystemExit('Failed:\n'+'\n'.join(failures))

if __name__=='__main__': main()

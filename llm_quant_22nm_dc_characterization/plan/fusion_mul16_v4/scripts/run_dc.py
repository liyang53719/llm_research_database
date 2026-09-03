#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,os,subprocess
import hashlib
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REQUIRED_REPORTS=('report_qor.rpt','report_area.rpt','report_timing.rpt','report_hold.rpt','report_constraints.rpt','report_resources.rpt','report_reference.rpt','check_design_post.rpt')

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def complete(rd: Path, row: dict) -> bool:
    summary=rd/'summary.kv'
    if not summary.exists() or not all((rd/'reports'/name).exists() for name in REQUIRED_REPORTS):
        return False
    kv={line.split('=',1)[0]:line.split('=',1)[1].strip() for line in summary.read_text(errors='ignore').splitlines() if '=' in line}
    return kv.get('rtl_input_sha256')==row.get('rtl_input_sha256')
def one(r,dc,lib,force,cpus,max_cores):
    rd=Path(r['run_dir'])
    if complete(rd,r) and not force:return r['run_id'],0,'SKIP'
    env=os.environ.copy(); env.update(RUN_ID=r['run_id'],RUN_DIR=str(rd),RTL_LIST=str(rd/'rtl_files.list'),LIB_SETUP=str(lib),CLK_PERIOD_NS='1.0',RTL_INPUT_SHA256=r['rtl_input_sha256'],DC_MAX_CORES=str(max_cores),LIBRARY_SETUP_SHA256=sha256(lib))
    with (rd/'dc_stdout.log').open('w') as f: p=subprocess.run(['taskset','-c',cpus,dc,'-64bit','-f',str(ROOT/'scripts/dc_synth_v4.tcl')],cwd=rd,env=env,stdout=f,stderr=subprocess.STDOUT)
    return r['run_id'],p.returncode,'RUN'
def main():
    global ROOT
    ap=argparse.ArgumentParser(); ap.add_argument('--build-dir',default='build_dc_1ghz'); ap.add_argument('--lib-setup',required=True); ap.add_argument('--dc-shell',default=os.getenv('DC_SHELL','dc_shell')); ap.add_argument('--jobs',type=int,default=1); ap.add_argument('--max-cores',type=int,default=1); ap.add_argument('--cpus',default='8-23'); ap.add_argument('--root',default=str(ROOT)); ap.add_argument('--run-id',action='append',default=[]); ap.add_argument('--force',action='store_true'); a=ap.parse_args()
    ROOT=Path(a.root).resolve()
    if a.jobs<1 or a.max_cores<1 or a.jobs*a.max_cores>2 or a.cpus!='8-23': raise SystemExit('Require jobs>=1, max-cores>=1, jobs*max-cores<=2, cpus=8-23')
    with (ROOT/a.build_dir/'runs.csv').open(encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    if a.run_id:
        wanted=set(a.run_id); rows=[r for r in rows if r['run_id'] in wanted]
        if wanted-{r['run_id'] for r in rows}: raise SystemExit('Unknown run id')
    failed=[]
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        futs=[pool.submit(one,r,a.dc_shell,Path(a.lib_setup).resolve(),a.force,a.cpus,a.max_cores) for r in rows]
        for fut in as_completed(futs):
            rid,rc,act=fut.result(); print(f'[{act}] {rid}: {rc}',flush=True)
            if rc: failed.append(rid)
    if failed: raise SystemExit('failed:\n'+'\n'.join(failed))
if __name__=='__main__':main()

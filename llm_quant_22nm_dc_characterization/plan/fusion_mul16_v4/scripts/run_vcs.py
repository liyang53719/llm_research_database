#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--vcs',default='vcs'); ap.add_argument('--dw-sim',default=''); ap.add_argument('--manifest',default='results/vectors/manifest.csv'); args=ap.parse_args()
    build=ROOT/'build_vcs'; build.mkdir(exist_ok=True); simv=build/'simv'
    files=[ROOT/'rtl'/x.strip() for x in (ROOT/'rtl/fusion_mul16_v4.f').read_text().splitlines() if x.strip()]
    cmd=[args.vcs,'-full64','-sverilog','-timescale=1ns/1ps','+define+FUSION_USE_DW','-o',str(simv),str(ROOT/'tb/dw_mult_uns_compat.sv'),*map(str,files),str(ROOT/'tb/fusion_mul16_v4_top_tb.sv')]
    if args.dw_sim: cmd.extend(['-y',args.dw_sim,'+libext+.v'])
    subprocess.run(cmd,cwd=ROOT,check=True)
    with (ROOT/args.manifest).open(encoding='utf-8-sig') as f: cases=list(csv.DictReader(f))
    rows=[]
    for c in cases:
        run=[str(simv),f'+VECTORS={ROOT/"results/vectors"/c["vector_file"]}',f'+MODE={c["mode"]}',f'+BEATS={c["beats"]}',f'+KIND={c["result_kind"]}',f'+LAT={c["latency_stages"]}',f'+CLAT={c["clear_latency_stages"]}']
        for lane in range(4): run += [f'+INT{lane}={c[f"int_lane{lane}"]}',f'+FP{lane}={c[f"fp_lane{lane}"]}']
        p=subprocess.run(run,cwd=ROOT,text=True,capture_output=True)
        passed=p.returncode==0 and 'PASS ' in p.stdout and 'FAIL ' not in p.stdout
        rows.append({**c,'returncode':p.returncode,'passed':int(passed),'stdout_tail':'\n'.join(p.stdout.splitlines()[-10:]),'stderr_tail':'\n'.join(p.stderr.splitlines()[-10:])})
        if not passed: raise SystemExit(f'VCS failed {c["case_id"]}\n{p.stdout}\n{p.stderr}')
    out=ROOT/'results/vcs/vcs_summary.csv'; out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',newline='',encoding='utf-8-sig') as f: w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f'VCS PASS {len(rows)}/{len(rows)}')
if __name__=='__main__': main()

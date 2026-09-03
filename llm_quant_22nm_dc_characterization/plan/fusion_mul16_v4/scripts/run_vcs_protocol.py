#!/usr/bin/env python3
from __future__ import annotations
import argparse,subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--vcs',default='vcs'); ap.add_argument('--dw-sim',default=''); args=ap.parse_args()
    build=ROOT/'build_vcs_protocol'; build.mkdir(exist_ok=True); simv=build/'simv'
    files=[ROOT/'rtl'/x.strip() for x in (ROOT/'rtl/fusion_mul16_v4.f').read_text().splitlines() if x.strip()]
    cmd=[args.vcs,'-full64','-sverilog','-timescale=1ns/1ps','+define+FUSION_USE_DW','-o',str(simv),str(ROOT/'tb/dw_mult_uns_compat.sv'),*map(str,files),str(ROOT/'tb/fusion_mul16_v4_protocol_tb.sv')]
    if args.dw_sim: cmd.extend(['-y',args.dw_sim,'+libext+.v'])
    subprocess.run(cmd,cwd=ROOT,check=True)
    p=subprocess.run([str(simv)],cwd=ROOT,text=True,capture_output=True)
    passed=p.returncode==0 and 'PASS protocol failures=0' in p.stdout and 'FAIL ' not in p.stdout
    (ROOT/'results/vcs').mkdir(parents=True,exist_ok=True)
    out={'passed':passed,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    (ROOT/'results/vcs/protocol_summary.json').write_text(json.dumps(out,indent=2))
    if not passed: raise SystemExit(p.stdout+'\n'+p.stderr)
    print('VCS protocol PASS')
if __name__=='__main__':main()

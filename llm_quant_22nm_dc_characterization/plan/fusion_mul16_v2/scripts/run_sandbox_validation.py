#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def run(cmd):
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
    print('$',' '.join(map(str,cmd)))
    print(p.stdout)
    if p.stderr: print(p.stderr)
    if p.returncode: raise SystemExit(p.returncode)
    return {'command':' '.join(map(str,cmd)),'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--skip-accum-study',action='store_true'); a=ap.parse_args()
    logs=[]
    logs.append(run([sys.executable,'-m','unittest','discover','-s','tests','-v']))
    logs.append(run([sys.executable,'scripts/gen_test_vectors.py','--per-mode','64','--output','results/rtl_vectors_smoke.jsonl']))
    logs.append(run([sys.executable,'scripts/gen_dc_runs.py']))
    if not a.skip_accum_study:
        logs.append(run([sys.executable,'model/bf16_accum_study.py','--output','results/bf16_accum_error.csv']))
    (ROOT/'results/sandbox_validation.json').write_text(json.dumps(logs,indent=2),encoding='utf-8')
    print('Sandbox validation complete')

if __name__=='__main__': main()

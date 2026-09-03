#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess
import os
from pathlib import Path

p=argparse.ArgumentParser(); p.add_argument('--output-dir',default='results'); p.add_argument('--cxx',default='g++'); a=p.parse_args()
root=Path(__file__).resolve().parents[1]
bin_path=root/'build_full_domain_scan'
subprocess.run([a.cxx,'-O3','-std=c++17',str(root/'model/full_domain_scan.cpp'),'-o',str(bin_path)],check=True)
# Catapult's bundled GCC may emit GLIBCXX symbols newer than the system
# runtime.  Run with the libstdc++/libgcc directory belonging to the selected
# compiler, while preserving the caller's EDA library path.
compiler_libstd = Path(subprocess.check_output([a.cxx,'-print-file-name=libstdc++.so.6'], text=True).strip()).resolve()
if not compiler_libstd.is_file():
    raise SystemExit(f'compiler libstdc++ not found: {compiler_libstd}')
run_env = os.environ.copy()
run_env['LD_LIBRARY_PATH'] = str(compiler_libstd.parent) + ':' + run_env.get('LD_LIBRARY_PATH', '')
subprocess.run([str(bin_path),'--output-dir',str(root/a.output_dir)],check=True,env=run_env)
print(root/a.output_dir/'full_input_domain_report.json')

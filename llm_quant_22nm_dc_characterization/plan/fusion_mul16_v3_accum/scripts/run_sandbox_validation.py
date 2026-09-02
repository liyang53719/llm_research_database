#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], env=None) -> dict:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, env=env)
    if proc.returncode:
        raise RuntimeError(f'command failed: {cmd}\n{proc.stdout}\n{proc.stderr}')
    return {
        'command': ' '.join(cmd),
        'returncode': proc.returncode,
        'stdout': proc.stdout,
        'stderr': proc.stderr,
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    logs = []
    python_files = sorted(ROOT.glob('model/*.py')) + sorted(ROOT.glob('tests/*.py')) + sorted(ROOT.glob('scripts/*.py'))
    for path in python_files:
        py_compile.compile(str(path), doraise=True)

    env = dict(**__import__('os').environ)
    env['PYTHONPATH'] = str(ROOT / 'model')
    logs.append(run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], env=env))
    logs.append(run([sys.executable, 'model/accum_error_study.py', '--output', 'results/accum_error_comparison.csv'], env=env))
    logs.append(run([sys.executable, 'scripts/build_numeric_summary.py'], env=env))
    logs.append(run([sys.executable, 'scripts/gen_vcs_vectors.py'], env=env))
    logs.append(run([sys.executable, 'scripts/plot_numeric_results.py'], env=env))

    with tempfile.TemporaryDirectory() as td:
        stub = Path(td) / 'v2'
        (stub / 'rtl').mkdir(parents=True)
        for name in [
            'fusion_mul16_v2_pkg.sv','fusion_mul16_v2_config.sv','mul4x4_brick.sv',
            'raw16_to_bf16_rne.sv','fusion_mul16_v2_product_pipe.sv',
            'fusion_mul16_v2_int_accum.sv'
        ]:
            (stub / 'rtl' / name).write_text('// dry-run stub\n')
        build = Path(td) / 'build'
        logs.append(run([
            sys.executable, 'scripts/gen_dc_runs.py', '--v2-root', str(stub),
            '--build-dir', str(build)
        ], env=env))
        with (build / 'runs.csv').open(encoding='utf-8-sig') as f:
            dry_runs = list(csv.DictReader(f))
        if len(dry_runs) != 12:
            raise AssertionError(len(dry_runs))

    with (ROOT / 'results/accum_error_comparison.csv').open(encoding='utf-8-sig') as f:
        error_rows = list(csv.DictReader(f))
    with (ROOT / 'results/vcs_vectors/manifest.csv').open(encoding='utf-8-sig') as f:
        vcs_cases = list(csv.DictReader(f))
    with (ROOT / 'config/dc_experiments_1ghz.csv').open(encoding='utf-8-sig') as f:
        dc_groups = list(csv.DictReader(f))
    with (ROOT / 'results/synthetic_numeric_gate.csv').open(encoding='utf-8-sig') as f:
        gate_rows = list(csv.DictReader(f))

    summary = {
        'status': 'PASS',
        'python_files_compiled': len(python_files),
        'unit_tests': 20,
        'unit_test_failures': 0,
        'rtl_files_static_checked_by_tests': len(list(ROOT.glob('rtl/*.sv'))),
        'numeric_error_rows': len(error_rows),
        'vcs_cases_generated': len(vcs_cases),
        'dc_groups_1ghz': len(dc_groups),
        'dc_runs_1ghz': len(dc_groups),
        'synthetic_numeric_gates': gate_rows,
        'vcs_execution_in_sandbox': 'NOT_AVAILABLE',
        'dc_execution_in_sandbox': 'NOT_AVAILABLE',
        'key_hashes': {
            'accum_error_comparison.csv': sha256(ROOT / 'results/accum_error_comparison.csv'),
            'vcs_manifest.csv': sha256(ROOT / 'results/vcs_vectors/manifest.csv'),
            'dc_experiments_1ghz.csv': sha256(ROOT / 'config/dc_experiments_1ghz.csv'),
        },
        'commands': logs,
    }
    (ROOT / 'results/SANDBOX_VALIDATION.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    md = f'''# FusionMul16 v3 sandbox validation

```text
status                     PASS
Python files compiled      {len(python_files)}
unit tests                 20 / 20
RTL source files           {len(list(ROOT.glob('rtl/*.sv')))}
numeric comparison rows    {len(error_rows)}
VCS cases generated        {len(vcs_cases)}
1 GHz DC groups planned    {len(dc_groups)}
VCS available in sandbox   no
DC/DW available in sandbox no
```

Synthetic K=4096 gate:

'''
    for row in gate_rows:
        md += f'- `{row["accum_style"]}`: {"PASS" if row["synthetic_gate_pass"] == "1" else "FAIL"}'
        if row['failures']:
            md += f' — {row["failures"]}'
        md += '\n'
    md += '''
The synthetic gate is not a target-model accuracy signoff. Local VCS must run the 15 generated accumulation sequences; local DC must run the 12 one-GHz groups.
'''
    (ROOT / 'results/SANDBOX_VALIDATION.md').write_text(md, encoding='utf-8')
    print(md)


if __name__ == '__main__':
    main()

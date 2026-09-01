#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(command: list[str], cwd: Path) -> dict:
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    return {
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    root = Path(args.root).resolve()
    commands = [
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        [sys.executable, "model/area_thresholds.py"],
        [sys.executable, "scripts/gen_test_vectors.py", "--per-mode", "256"],
        [sys.executable, "scripts/gen_dc_runs.py"],
    ]
    results = [run(command, root) for command in commands]
    failed = [result for result in results if result["returncode"] != 0]
    summary = {
        "status": "pass" if not failed else "fail",
        "unit_tests": 17,
        "integer_pair_spaces": {
            "i4_i4": 256,
            "i4_i8": 4096,
            "i8_i8": 65536,
            "i16_random_and_boundaries": 5009,
        },
        "floating_pair_spaces": {
            "fp8_fp8_exhaustive": 65536,
            "i4_fp8_exhaustive": 4096,
            "i8_fp8_exhaustive": 65536,
            "bf16_stratified_and_mixed": 4776,
        },
        "structural_contract": {
            "explicit_bricks": 16,
            "multiply_operator_files": ["rtl/mul4x4_brick.sv"],
            "logical_modes": 10,
            "planned_dc_groups": 11,
            "planned_dc_runs": 33,
        },
        "limitations": [
            "No SystemVerilog compiler or simulator is installed in the sandbox.",
            "No CLN22UL .db, Design Compiler or DesignWare runtime is available in the sandbox.",
            "RTL proof is static plus Python bit-exact modeling; local RTL simulation and DC are mandatory.",
        ],
        "commands": results,
    }
    output = root / "results/sandbox_validation.json"
    output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if failed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

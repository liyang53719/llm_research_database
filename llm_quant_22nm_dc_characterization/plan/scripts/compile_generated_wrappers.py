#!/usr/bin/env python3
from __future__ import annotations

import csv
import argparse
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--manifest",default="build_mixed/runs.csv")
    args=parser.parse_args()
    manifest = (ROOT / args.manifest).resolve()
    if not manifest.exists():
        raise SystemExit("Run scripts/gen_mixed_manifest.py first")
    with manifest.open(encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    first_by_group = {}
    for row in rows:
        first_by_group.setdefault(row["group_id"], row)

    stub = ROOT / "tests/dw_sim_stubs.sv"
    failures = []
    with tempfile.TemporaryDirectory(prefix="mixed_wrapper_compile_") as temp:
        temp_root = Path(temp)
        for group_id, row in sorted(first_by_group.items()):
            rtl_files = [
                line.strip()
                for line in Path(row["rtl_list"]).read_text().splitlines()
                if line.strip()
            ]
            output = temp_root / f"{group_id}.vvp"
            process = subprocess.run(
                ["iverilog", "-g2012", "-s", "char_top", "-o", str(output), str(stub), *rtl_files],
                text=True,
                capture_output=True,
            )
            if process.returncode:
                failures.append((group_id, process.stdout + process.stderr))
    if failures:
        for group_id, message in failures:
            print(f"FAILED {group_id}\n{message}")
        raise SystemExit(2)
    print(f"Compiled {len(first_by_group)} generated wrappers with Icarus")


if __name__ == "__main__":
    main()

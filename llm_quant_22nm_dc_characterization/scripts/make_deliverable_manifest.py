#!/usr/bin/env python3
from __future__ import annotations
import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results/deliverable_manifest.csv"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def selected_files():
    fixed_roots = [
        ROOT / "AGENT_TASK.md",
        ROOT / "README_CN.md",
        ROOT / "config",
        ROOT / "docs",
        ROOT / "rtl",
        ROOT / "scripts",
        ROOT / "results",
        ROOT / "build/runs.csv",
    ]
    for item in fixed_roots:
        if item.is_file():
            yield item
        elif item.is_dir():
            for path in sorted(item.rglob("*")):
                if path.is_file() and path != OUTPUT and "__pycache__" not in path.parts:
                    yield path
    for run_dir in sorted((ROOT / "build").glob("*__T*ns")):
        for name in ("meta.json", "char_top.sv", "rtl_files.list", "summary.kv", "dc_stdout.log"):
            path = run_dir / name
            if path.is_file():
                yield path
        reports = run_dir / "reports"
        if reports.is_dir():
            yield from (path for path in sorted(reports.iterdir()) if path.is_file())
        netlist = run_dir / "netlist"
        if netlist.is_dir():
            for name in ("char_top.v", "char_top.sdc"):
                path = netlist / name
                if path.is_file():
                    yield path


def main():
    paths = sorted(set(selected_files()))
    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["relative_path", "size_bytes", "sha256"])
        for path in paths:
            writer.writerow([path.relative_to(ROOT), path.stat().st_size, digest(path)])
    print(f"Wrote {OUTPUT} with {len(paths)} files")


if __name__ == "__main__":
    main()

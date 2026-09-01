#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import socket
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sanitize_text(text: str) -> str:
    replacements = [(str(ROOT), "<FUSION_MUL16_ROOT>")]
    for variable, replacement in [
        ("SYNOPSYS", "<SYNOPSYS_DC_ROOT>"),
        ("VCS_HOME", "<SYNOPSYS_VCS_ROOT>"),
    ]:
        value = os.environ.get(variable, "")
        if value:
            replacements.append((value, replacement))
    replacements += [(str(Path.home()), "<LOCAL_HOME>"),
                     (socket.gethostname(), "<LOCAL_HOST>")]
    for source, replacement in replacements:
        if source:
            text = text.replace(source, replacement)
    text = re.sub(r"/(?:[^/\s]+/)*cln22ul(?=/|\s|$)", "<CLN22UL_ROOT>", text)
    return text


def copy_text(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(sanitize_text(source.read_text(encoding="utf-8", errors="ignore")),
                      encoding="utf-8")


def rewrite_result_csv(source: Path, target: Path) -> None:
    with source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    for row in rows:
        run_id = row.get("run_id", "")
        if run_id:
            if "run_dir" in row:
                row["run_dir"] = f"evidence/runs/{run_id}"
            if "report_dir" in row:
                row["report_dir"] = f"evidence/runs/{run_id}/reports"
            if "rtl_list" in row:
                row["rtl_list"] = "<GENERATED_RTL_LIST>"
        for key, value in row.items():
            row[key] = sanitize_text(value)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", required=True)
    args = parser.parse_args()
    destination = Path(args.destination).resolve()
    if destination.exists():
        raise SystemExit("Destination must not already exist")
    if destination == ROOT or ROOT in destination.parents:
        raise SystemExit("Destination must be outside the source tree")
    destination.mkdir(parents=True)

    results = ROOT / "results/local_dc"
    if not results.is_dir():
        raise SystemExit("Missing results/local_dc")
    for source in sorted(results.rglob("*")):
        if not source.is_file():
            continue
        target = destination / "results/local_dc" / source.relative_to(results)
        if source.suffix.lower() == ".csv":
            rewrite_result_csv(source, target)
        else:
            copy_text(source, target)

    build = ROOT / "build_dc"
    for run_dir in sorted(path for path in build.iterdir() if path.is_dir()):
        target_run = destination / "evidence/runs" / run_dir.name
        for name in ["summary.kv", "meta.json"]:
            source = run_dir / name
            if source.exists():
                copy_text(source, target_run / name)
        report_dir = run_dir / "reports"
        if report_dir.is_dir():
            for source in sorted(report_dir.iterdir()):
                if source.is_file():
                    copy_text(source, target_run / "reports" / source.name)

    entries = []
    for path in sorted(destination.rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            entries.append({
                "relative_path": path.relative_to(destination).as_posix(),
                "size_bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            })
    manifest = destination / "PUBLIC_LOCAL_RESULTS_MANIFEST.csv"
    with manifest.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(entries[0]))
        writer.writeheader()
        writer.writerows(entries)
    print(json.dumps({"destination": str(destination), "files": len(entries) + 1}, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Export a sanitized, source-and-evidence-only v3 bundle."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH_RE = re.compile(r"/(?:home|tmp)/[^\s,;\"']+")


def sanitize(text: str) -> str:
    text = text.replace(str(ROOT), "<V3_ROOT>")
    text = text.replace("<CLN22UL_LIBRARY>", "<CLN22UL_LIBRARY>")
    text = text.replace("<EDA_TOOLS>", "<EDA_TOOLS>")
    text = text.replace("<LOCAL_HOME>", "<LOCAL_HOME>")
    text = text.replace("<HOST>", "<HOST>")
    text = PATH_RE.sub("<LOCAL_PATH>", text)
    return text


def copy_text(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(sanitize(src.read_text(encoding="utf-8-sig", errors="ignore")), encoding="utf-8")


def copy_binary(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_csv(src: Path, dst: Path, evidence_kind: str | None = None) -> None:
    with src.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fields = list(rows[0]) if rows else []
    for row in rows:
        run_id = row.get("run_id", "")
        if evidence_kind and run_id:
            if "run_dir" in row:
                row["run_dir"] = f"evidence/{evidence_kind}/{run_id}"
            if "report_dir" in row:
                row["report_dir"] = f"evidence/{evidence_kind}/{run_id}/reports"
        for key, value in row.items():
            if isinstance(value, str):
                row[key] = sanitize(value)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def copy_tree(src_dir: Path, dst_dir: Path) -> None:
    for src in sorted(src_dir.rglob("*")):
        if not src.is_file() or "__pycache__" in src.parts or src.suffix == ".pyc":
            continue
        rel = src.relative_to(src_dir)
        dst = dst_dir / rel
        if src.suffix.lower() == ".csv":
            copy_csv(src, dst)
        elif src.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            copy_binary(src, dst)
        else:
            copy_text(src, dst)


def copy_dc_evidence(dst: Path) -> None:
    build = ROOT / "build_dc_1ghz"
    for run in sorted(p for p in build.iterdir() if p.is_dir() and p.name.startswith("V3_")):
        out = dst / run.name
        summary = run / "summary.kv"
        if summary.is_file():
            copy_text(summary, out / "summary.kv")
        reports = run / "reports"
        for report in sorted(reports.glob("*.rpt")):
            copy_text(report, out / "reports" / report.name)


def write_public_manifest(dst: Path) -> None:
    manifest = dst / "PUBLIC_LOCAL_RESULTS_MANIFEST.csv"
    files = [p for p in sorted(dst.rglob("*")) if p.is_file() and p != manifest]
    with manifest.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["relative_path", "size_bytes", "sha256"])
        for path in files:
            writer.writerow([
                str(path.relative_to(dst)),
                path.stat().st_size,
                hashlib.sha256(path.read_bytes()).hexdigest(),
            ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination")
    args = parser.parse_args()
    dst = Path(args.destination).resolve()
    if dst.exists():
        raise SystemExit(f"refusing to overwrite existing destination: {dst}")
    dst.mkdir(parents=True)

    for name in ("AGENT_TASK.md", "README_CN.md", "GIT_UPLOAD.md", "VERSION.json"):
        copy_text(ROOT / name, dst / name)
    for name in ("config", "docs", "model", "rtl", "scripts", "tests"):
        copy_tree(ROOT / name, dst / name)

    results_dst = dst / "results"
    for src in sorted((ROOT / "results").rglob("*")):
        if not src.is_file() or "__pycache__" in src.parts:
            continue
        rel = src.relative_to(ROOT / "results")
        target = results_dst / rel
        if src.suffix.lower() == ".csv":
            copy_csv(src, target, "dc" if rel.parts and rel.parts[0] == "local_dc" else None)
        elif src.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            copy_binary(src, target)
        else:
            copy_text(src, target)
    copy_dc_evidence(dst / "evidence/dc")

    public_readme = (
        "# Sanitized FusionMul16 v3 local results\n\n"
        "- Python tests: 20/20 PASS.\n"
        "- Full accumulator VCS crosscheck: 15/15 PASS.\n"
        "- CLN22UL TT typical_max 0.80 V, compile_ultra, 1.000 ns: 12/12 DC runs PASS.\n"
        "- Execution policy: CPU 8-23, one DC job/core, cgroup MemoryMax=40G.\n"
        "- All local absolute paths, hostname, licensed library paths, raw DC logs, generated netlists/DDC and proprietary .db/.lib/.sldb files are excluded or sanitized.\n"
        "- P5 provisional selection: BF16 tree + FP32 recurrent; target-model accuracy remains OPEN.\n"
    )
    (dst / "PUBLIC_LOCAL_RESULTS.md").write_text(public_readme, encoding="utf-8")
    write_public_manifest(dst)
    print(dst)


if __name__ == "__main__":
    main()

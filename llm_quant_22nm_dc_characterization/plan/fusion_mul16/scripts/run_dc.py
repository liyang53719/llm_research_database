#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


REQUIRED_REPORTS = (
    "report_area.rpt", "report_timing.rpt", "report_resources_pre.rpt",
    "report_reference_pre.rpt", "report_resources_post.rpt",
    "report_reference_post.rpt", "check_design_post.rpt",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def complete(run_dir: Path, row: dict) -> bool:
    summary = run_dir / "summary.kv"
    if not summary.exists() or not all((run_dir / "reports" / r).exists() for r in REQUIRED_REPORTS):
        return False
    values = {}
    for line in summary.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values.get("rtl_bundle_sha256") == row.get("rtl_bundle_sha256")


def run_one(row: dict, root: Path, dc_shell: str, lib_setup: Path, force: bool,
            cpus: str, max_cores: int):
    run_dir = Path(row["run_dir"])
    if complete(run_dir, row) and not force:
        return row["run_id"], 0, "SKIP"
    env = os.environ.copy()
    env.update({
        "RUN_ID": row["run_id"],
        "RUN_DIR": str(run_dir),
        "RTL_LIST": str(run_dir / "rtl_files.list"),
        "LIB_SETUP": str(lib_setup),
        "TOP": row["top_module"],
        "CLK_PERIOD_NS": str(row["clock_period_ns"]),
        "KEEP_BRICKS": str(row["keep_brick_hierarchy"]),
        "RTL_BUNDLE_SHA256": row["rtl_bundle_sha256"],
        "DC_MAX_CORES": str(max_cores),
        "LIBRARY_SETUP_SHA256": sha256(lib_setup),
    })
    with (run_dir / "dc_stdout.log").open("w", encoding="utf-8") as log:
        proc = subprocess.run(
            ["taskset", "-c", cpus, dc_shell, "-64bit", "-f",
             str(root / "scripts/dc_synth_fusion.tcl")],
            cwd=run_dir,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    return row["run_id"], proc.returncode, "RUN"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--build-dir", default="build_dc")
    parser.add_argument("--lib-setup", required=True)
    parser.add_argument("--dc-shell", default=os.environ.get("DC_SHELL", "dc_shell"))
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--max-cores", type=int, default=1)
    parser.add_argument("--cpus", default="8-23")
    parser.add_argument("--run-id", action="append", default=[])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.jobs < 1 or args.max_cores < 1 or args.jobs * args.max_cores > 2:
        raise SystemExit("Require jobs >= 1, max-cores >= 1, and jobs*max-cores <= 2")
    if args.cpus != "8-23":
        raise SystemExit("This checkout requires --cpus 8-23")
    root = Path(args.root).resolve()
    manifest = root / args.build_dir / "runs.csv"
    lib_setup = Path(args.lib_setup).resolve()
    if not manifest.exists():
        raise SystemExit("Run gen_dc_runs.py first")
    with manifest.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if args.run_id:
        wanted = set(args.run_id)
        rows = [row for row in rows if row["run_id"] in wanted]
        missing = sorted(wanted - {row["run_id"] for row in rows})
        if missing:
            raise SystemExit("Unknown run IDs: " + ", ".join(missing))
    failures = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(run_one, row, root, args.dc_shell, lib_setup,
                               args.force, args.cpus, args.max_cores) for row in rows]
        for future in as_completed(futures):
            run_id, rc, action = future.result()
            print(f"[{action}] {run_id}: rc={rc}", flush=True)
            if rc != 0:
                failures.append(run_id)
    if failures:
        raise SystemExit("Failed runs:\n" + "\n".join(failures))


if __name__ == "__main__":
    main()

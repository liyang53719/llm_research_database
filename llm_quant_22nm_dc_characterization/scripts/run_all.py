#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import hashlib
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"

REQUIRED_REPORTS = (
    "report_area.rpt",
    "report_qor.rpt",
    "report_resources.rpt",
    "check_design_post.rpt",
)

def parse_kv(path):
    values = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values

def run_one(row, dc_shell, lib_setup, lib_setup_sha256, dc_max_cores, force=False):
    run_dir = Path(row["run_dir"])
    summary = run_dir / "summary.kv"
    reports_complete = all((run_dir / "reports" / name).exists() for name in REQUIRED_REPORTS)
    previous = parse_kv(summary)
    fingerprints_match = (
        previous.get("rtl_bundle_sha256") == row["rtl_bundle_sha256"]
        and previous.get("library_setup_sha256") == lib_setup_sha256
    )
    if summary.exists() and reports_complete and fingerprints_match and not force:
        return row["run_id"], 0, "SKIP"
    env = os.environ.copy()
    env.update({
        "RUN_ID": row["run_id"],
        "RUN_DIR": str(run_dir),
        "RTL_LIST": str(run_dir / "rtl_files.list"),
        "LIB_SETUP": str(lib_setup),
        "CLK_PERIOD_NS": str(row["clock_period_ns"]),
        "RTL_BUNDLE_SHA256": row["rtl_bundle_sha256"],
        "LIB_SETUP_SHA256": lib_setup_sha256,
        "DC_MAX_CORES": str(dc_max_cores),
    })
    log_path = run_dir / "dc_stdout.log"
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.run(
            [dc_shell, "-64bit", "-f", str(ROOT / "scripts/dc_synth.tcl")],
            cwd=run_dir,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    return row["run_id"], proc.returncode, "RUN"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=1, help="Parallel DC processes; keep within available license tokens.")
    ap.add_argument("--dc-max-cores", type=int, default=1, help="Cores used by each DC process.")
    ap.add_argument(
        "--dc-shell",
        default=os.environ.get(
            "DC_SHELL",
            "dc_shell",
        ),
    )
    ap.add_argument("--lib-setup", default=str(ROOT / "config/library_setup.local.tcl"))
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if args.jobs < 1 or args.dc_max_cores < 1:
        raise SystemExit("--jobs and --dc-max-cores must both be positive.")
    if args.jobs * args.dc_max_cores > 2:
        raise SystemExit("Resource policy violation: jobs * dc-max-cores must not exceed 2.")
    os.sched_setaffinity(0, set(range(8, 24)))

    manifest = BUILD / "runs.csv"
    if not manifest.exists():
        raise SystemExit("build/runs.csv not found. Run scripts/gen_runs.py first.")
    lib_setup = Path(args.lib_setup).resolve()
    if not lib_setup.exists():
        raise SystemExit(f"Library setup not found: {lib_setup}")
    lib_setup_sha256 = hashlib.sha256(lib_setup.read_bytes()).hexdigest()

    with manifest.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    failures = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [
            pool.submit(
                run_one, row, args.dc_shell, lib_setup, lib_setup_sha256,
                args.dc_max_cores, args.force,
            )
            for row in rows
        ]
        for fut in as_completed(futures):
            run_id, rc, action = fut.result()
            print(f"[{action}] {run_id}: rc={rc}", flush=True)
            if rc != 0:
                failures.append(run_id)

    if failures:
        print("FAILED RUNS:")
        for run_id in failures:
            print(run_id)
        raise SystemExit(2)
    print(f"Completed {len(rows)} runs.")

if __name__ == "__main__":
    main()

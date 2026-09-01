#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REQUIRED_REPORTS = (
    "report_area.rpt",
    "report_qor.rpt",
    "report_resources.rpt",
    "check_design_post.rpt",
)


def read_kv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def run_one(
    row: dict[str, str],
    parent_root: Path,
    dc_shell: str,
    lib_setup: Path,
    dc_max_cores: int,
    force: bool,
) -> tuple[str, int, str]:
    plan_root = Path(__file__).resolve().parents[1]
    run_id = row["run_id"]
    run_dir = Path(row.get("run_dir") or plan_root / "build_mixed" / run_id).resolve()
    rtl_list = Path(row.get("rtl_list") or run_dir / "rtl_files.list").resolve()
    summary = run_dir / "summary.kv"
    lib_setup_sha256 = hashlib.sha256(lib_setup.read_bytes()).hexdigest()

    reports_complete = all(
        (run_dir / "reports" / report).is_file() for report in REQUIRED_REPORTS
    )
    previous = read_kv(summary)
    fingerprints_match = (
        previous.get("rtl_bundle_sha256") == row.get("rtl_bundle_sha256")
        and previous.get("library_setup_sha256") == lib_setup_sha256
    )
    if summary.exists() and reports_complete and fingerprints_match and not force:
        return run_id, 0, "SKIP"
    if not rtl_list.exists():
        raise FileNotFoundError(
            f"{run_id}: missing {rtl_list}; generate char_top.sv and rtl_files.list first"
        )

    run_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        {
            "RUN_ID": run_id,
            "RUN_DIR": str(run_dir),
            "RTL_LIST": str(rtl_list),
            "LIB_SETUP": str(lib_setup),
            "CLK_PERIOD_NS": row["clock_period_ns"],
            "RTL_BUNDLE_SHA256": row.get("rtl_bundle_sha256", "UNKNOWN"),
            "LIB_SETUP_SHA256": lib_setup_sha256,
            "DC_MAX_CORES": str(dc_max_cores),
        }
    )
    with (run_dir / "dc_stdout.log").open("w", encoding="utf-8") as log:
        process = subprocess.run(
            [dc_shell, "-64bit", "-f", str(parent_root / "scripts" / "dc_synth.tcl")],
            cwd=run_dir,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    return run_id, process.returncode, "RUN"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--parent-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="llm_quant_22nm_dc_characterization directory",
    )
    parser.add_argument("--manifest", default="build_mixed/runs.csv")
    parser.add_argument("--lib-setup")
    parser.add_argument("--dc-shell", default=os.environ.get("DC_SHELL", "dc_shell"))
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--dc-max-cores", type=int, choices=[1, 2], default=1)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.jobs < 1:
        raise SystemExit("--jobs must be positive")
    if args.jobs * args.dc_max_cores > 2:
        raise SystemExit("Resource policy violation: jobs * dc-max-cores must not exceed 2")
    os.sched_setaffinity(0, set(range(8, 24)))

    plan_root = Path(__file__).resolve().parents[1]
    parent_root = Path(args.parent_root).resolve()
    manifest = Path(args.manifest)
    if not manifest.is_absolute():
        manifest = (plan_root / manifest).resolve()
    lib_setup = Path(
        args.lib_setup or parent_root / "config" / "library_setup.local.tcl"
    ).resolve()

    if shutil.which(args.dc_shell) is None:
        raise SystemExit(f"DC executable not found: {args.dc_shell}")
    if not (parent_root / "scripts" / "dc_synth.tcl").exists():
        raise SystemExit(f"Missing parent dc_synth.tcl under {parent_root}")
    if not lib_setup.exists():
        raise SystemExit(f"Missing library setup: {lib_setup}")
    if not manifest.exists():
        raise SystemExit(
            f"Missing {manifest}; local wrapper generation must create build_mixed/runs.csv"
        )

    with manifest.open(encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit(f"Empty manifest: {manifest}")
    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [
            pool.submit(
                run_one,
                row,
                parent_root,
                args.dc_shell,
                lib_setup,
                args.dc_max_cores,
                args.force,
            )
            for row in rows
        ]
        for future in as_completed(futures):
            run_id, returncode, action = future.result()
            print(f"[{action}] {run_id}: rc={returncode}", flush=True)
            if returncode:
                failures.append(run_id)

    if failures:
        print("FAILED RUNS:\n" + "\n".join(failures))
        raise SystemExit(2)
    print(f"Completed {len(rows)} runs")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

from gen_runs import SMOKE_GROUPS

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_REPORTS = (
    "report_area.rpt",
    "report_qor.rpt",
    "report_resources.rpt",
    "check_design_post.rpt",
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", choices=["L1", "L2"], default="L2")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    rank = {"L1": 1, "L2": 2}

    with (ROOT / "config/experiment_groups.csv").open(encoding="utf-8-sig") as f:
        groups = [r for r in csv.DictReader(f) if rank[r["tier"]] <= rank[args.tier]]
    if args.smoke:
        groups = [r for r in groups if r["group_id"] in SMOKE_GROUPS]

    manifest_path = ROOT / "build/runs.csv"
    if not manifest_path.exists():
        raise SystemExit("build/runs.csv not found.")
    with manifest_path.open(encoding="utf-8-sig") as f:
        manifest = list(csv.DictReader(f))
    expected = len(manifest)
    manifest_run_ids = {r["run_id"] for r in manifest}
    manifest_group_ids = {r["group_id"] for r in manifest}
    expected_group_ids = {g["group_id"] for g in groups}
    periods = sorted({float(r["clock_period_ns"]) for r in manifest})

    raw_path = ROOT / "results/area_22nm_raw.csv"
    if not raw_path.exists():
        raise SystemExit("Run scripts/collect_results.py first.")
    with raw_path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    errors = []
    warnings = []
    if manifest_group_ids != expected_group_ids:
        errors.append(
            "Manifest group set differs from requested acceptance tier: "
            f"expected={len(expected_group_ids)} observed={len(manifest_group_ids)}."
        )
    if len(rows) != expected:
        errors.append(f"Expected {expected} rows but found {len(rows)}.")
    if {r["run_id"] for r in rows} != manifest_run_ids:
        errors.append("Raw-result run IDs do not exactly match build/runs.csv.")

    by_group = defaultdict(list)
    for row in rows:
        if rank.get(row["tier"], 99) <= rank[args.tier]:
            by_group[row["group_id"]].append(row)
        try:
            if float(row["mapped_cell_area_um2"]) <= 0:
                errors.append(f'{row["run_id"]}: non-positive area.')
        except Exception:
            errors.append(f'{row["run_id"]}: missing mapped cell area.')
        if row.get("blackbox_count") not in ("0", "0.0", 0, 0.0):
            errors.append(f'{row["run_id"]}: blackbox_count={row.get("blackbox_count")}')
        if row.get("status") != "ok":
            errors.append(f'{row["run_id"]}: status={row.get("status")}')

        run_dir = Path(row.get("run_dir", ""))
        for report_name in REQUIRED_REPORTS:
            report_path = run_dir / "reports" / report_name
            if not report_path.is_file() or report_path.stat().st_size == 0:
                errors.append(f'{row["run_id"]}: missing or empty {report_name}.')
        stdout_path = run_dir / "dc_stdout.log"
        if not stdout_path.is_file():
            errors.append(f'{row["run_id"]}: missing dc_stdout.log.')
        else:
            stdout = stdout_path.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"^Error:", stdout, flags=re.MULTILINE):
                errors.append(f'{row["run_id"]}: dc_stdout.log contains an Error line.')

    for group in groups:
        grows = by_group.get(group["group_id"], [])
        if len(grows) != len(periods):
            errors.append(f'{group["group_id"]}: expected {len(periods)} periods, found {len(grows)}.')
        observed_periods = sorted(float(row["clock_period_ns"]) for row in grows)
        if observed_periods != periods:
            errors.append(f'{group["group_id"]}: period set differs from common manifest periods.')
        if grows and not any(row.get("timing_met") in ("1", 1, 1.0, "1.0") for row in grows):
            warnings.append(f'{group["group_id"]}: no common target period met timing; keep data but adjust clock sweep.')

    relaxed = max(periods)
    anchor = {}
    for row in rows:
        try:
            if abs(float(row["clock_period_ns"]) - relaxed) < 1e-9:
                anchor[row["group_id"]] = float(row["mapped_cell_area_um2"])
        except Exception:
            pass
    for small, large in (
        ("INT_MAC_W4_A4_N64", "INT_MAC_W8_A8_N64"),
        ("PE_W4A8_L4", "PE_W8A8_L4"),
        ("ARRAY_W4A8_4X4", "ARRAY_W4A8_16X16"),
    ):
        if small in anchor and large in anchor and not anchor[large] > anchor[small]:
            warnings.append(f"Sanity check: {large} area is not larger than {small} at relaxed period.")

    # Preserve and report non-monotonic points instead of modifying data. As
    # timing tightens (period decreases), mapped area normally stays flat or
    # increases. Any decrease is retained and flagged for topology review.
    for group_id, grows in sorted(by_group.items()):
        valid = []
        for row in grows:
            try:
                valid.append((float(row["clock_period_ns"]), float(row["mapped_cell_area_um2"])))
            except Exception:
                pass
        valid.sort(reverse=True)
        for (loose_period, loose_area), (tight_period, tight_area) in zip(valid, valid[1:]):
            if tight_area < loose_area * (1.0 - 1e-6):
                warnings.append(
                    f"{group_id}: area decreased when tightening {loose_period}ns -> "
                    f"{tight_period}ns ({loose_area} -> {tight_area} um2); retain and review DC topology."
                )

    # For array families, compare per-PE area at 8x8 and 16x16. A difference
    # above 20% is a warning, not a data-edit instruction.
    array_per_pe = defaultdict(dict)
    for row in rows:
        if row.get("category") != "array_scaling":
            continue
        try:
            rows_n = int(float(row["rows"]))
            cols_n = int(float(row["cols"]))
            period = float(row["clock_period_ns"])
            area_per_pe = float(row["mapped_cell_area_um2"]) / (rows_n * cols_n)
        except Exception:
            continue
        family = re.sub(r"_(4X4|8X8|16X16)$", "", row["group_id"])
        array_per_pe[(family, period)][rows_n] = area_per_pe
    for (family, period), sizes in sorted(array_per_pe.items()):
        if 8 in sizes and 16 in sizes:
            rel_delta = abs(sizes[16] - sizes[8]) / sizes[8]
            if rel_delta > 0.20:
                warnings.append(
                    f"{family}@{period}ns: area/PE 8x8={sizes[8]:.6f}, "
                    f"16x16={sizes[16]:.6f}, delta={rel_delta:.1%}; scaling not converged."
                )

    for field in (
        "library_set_id",
        "target_libraries",
        "compile_mode",
        "keep_hierarchy",
        "library_setup_sha256",
        "rtl_bundle_sha256",
        "tool_version",
    ):
        values = {row.get(field, "").strip() for row in rows if row.get(field, "").strip()}
        if len(values) != 1:
            errors.append(f"Comparison contract field {field} has {len(values)} non-empty values; expected one.")

    for row in (r for r in rows if r["group_id"] == "FP_MAC_BF16_E8M7"):
        resources_path = Path(row["run_dir"]) / "reports/report_resources.rpt"
        if resources_path.is_file():
            resources = resources_path.read_text(encoding="utf-8", errors="ignore")
            if not re.search(r"DW_.*fp|DW_fp", resources, flags=re.IGNORECASE):
                errors.append(f'{row["run_id"]}: report_resources has no DW floating-point component.')

    report = ROOT / "results/validation_report.txt"
    with report.open("w", encoding="utf-8") as f:
        f.write(
            f"Tier: {args.tier}\nSmoke: {args.smoke}\n"
            f"Expected runs: {expected}\nObserved rows: {len(rows)}\n"
            f"Common periods ns: {periods}\n"
        )
        f.write("\nERRORS\n")
        f.write("\n".join(errors) if errors else "NONE")
        f.write("\n\nWARNINGS\n")
        f.write("\n".join(warnings) if warnings else "NONE")
        f.write("\n")
    print(report.read_text(encoding="utf-8"))
    if errors:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

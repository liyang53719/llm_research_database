#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path


REQUIRED_REPORTS = (
    "report_area.rpt", "report_timing.rpt", "report_resources_pre.rpt",
    "report_reference_pre.rpt", "report_resources_post.rpt",
    "report_reference_post.rpt", "check_design_post.rpt",
)


def parse_kv(path: Path) -> dict:
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def count_other_mult_ops(report: str) -> int:
    # Width is proven by the explicit DW_mult_uns #(4,4) source boundary and
    # the precompile u_dw_mult instance count.  Post-map resource rows often
    # omit parameters, so do not misclassify parameter-less DW_mult_uns rows.
    forbidden = ("DW_fp_mult", "DW_mult_tc", "DW02_mult", "DW_mult_pipe",
                 "DW_mult_seq")
    return sum(report.count(name) for name in forbidden)


def dc_error_count(run_dir: Path) -> int:
    count = 0
    pattern = re.compile(r"^(?:Error:|Error-\[[^]]+\])", re.MULTILINE)
    for path in [run_dir / "dc_stdout.log", run_dir / "reports/analyze.log"]:
        if path.exists():
            count += len(pattern.findall(path.read_text(encoding="utf-8", errors="ignore")))
    return count


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--build-dir", default="build_dc")
    parser.add_argument("--output-dir", default="results/local_dc")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    build = root / args.build_dir
    output = root / args.output_dir
    output.mkdir(parents=True, exist_ok=True)

    rows = []
    for meta_path in sorted(build.glob("*/meta.json")):
        run_dir = meta_path.parent
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        kv = parse_kv(run_dir / "summary.kv")
        multiplier_evidence = ""
        for name in ["report_resources_pre.rpt", "report_resources_post.rpt",
                     "report_reference_pre.rpt", "report_reference_post.rpt"]:
            path = run_dir / "reports" / name
            if path.exists():
                multiplier_evidence += path.read_text(encoding="utf-8", errors="ignore")
        mult4 = int(float(kv.get("dw_mult_instance_count_precompile", 0))) if kv else 0
        mult_other = count_other_mult_ops(multiplier_evidence)
        reports_complete = all((run_dir / "reports" / name).exists() for name in REQUIRED_REPORTS)
        rows.append({
            **meta,
            "library_set_id": kv.get("library_set_id", ""),
            "mapped_cell_area_um2": number(kv.get("mapped_cell_area_um2")),
            "leaf_cell_count": number(kv.get("leaf_cell_count")),
            "blackbox_count": number(kv.get("blackbox_count")),
            "brick_instance_count_precompile": number(kv.get("brick_instance_count_precompile")),
            "dw_mult_instance_count_precompile": number(kv.get("dw_mult_instance_count_precompile")),
            "report_dw_mult_4x4_rows": mult4,
            "report_other_multiplier_rows": mult_other,
            "wns_ns": number(kv.get("wns_ns")),
            "critical_delay_ns": number(kv.get("critical_delay_ns")),
            "achieved_fmax_mhz": number(kv.get("achieved_fmax_mhz")),
            "timing_met": int(float(kv["timing_met"])) if kv.get("timing_met") not in (None, "", "NA") else None,
            "tool_version": kv.get("tool_version", ""),
            "rtl_bundle_sha256_reported": kv.get("rtl_bundle_sha256", ""),
            "library_setup_sha256": kv.get("library_setup_sha256", ""),
            "dc_max_cores": number(kv.get("dc_max_cores")),
            "compile_mode_reported": kv.get("compile_mode", ""),
            "input_transition": number(kv.get("input_transition")),
            "output_load": number(kv.get("output_load")),
            "max_transition": number(kv.get("max_transition")),
            "clock_uncertainty_ratio": number(kv.get("clock_uncertainty_ratio")),
            "input_delay_ratio": number(kv.get("input_delay_ratio")),
            "output_delay_ratio": number(kv.get("output_delay_ratio")),
            "dc_error_count": dc_error_count(run_dir),
            "status": "ok" if kv and reports_complete else "missing_evidence",
            "report_dir": str((run_dir / "reports").resolve()),
        })
    if not rows:
        raise SystemExit("No runs found")
    write_csv(output / "fusion16_area_raw.csv", rows)

    by_group = defaultdict(list)
    for row in rows:
        by_group[row["group_id"]].append(row)
    summary = []
    for group_id, group_rows in sorted(by_group.items()):
        good = [r for r in group_rows if r["status"] == "ok" and r["mapped_cell_area_um2"]]
        met = [r for r in good if r["timing_met"] == 1]
        at_1g = [r for r in good if abs(float(r["clock_period_ns"]) - 1.0) < 1e-12]
        one = at_1g[0] if at_1g else None
        first = group_rows[0]
        summary.append({
            "group_id": group_id,
            "top_module": first["top_module"],
            "category": first["category"],
            "throughput_contract": first["throughput_contract"],
            "comparison_role": first["comparison_role"],
            "run_count": len(group_rows),
            "valid_count": len(good),
            "timing_met_count": len(met),
            "best_feasible_area_um2": min((r["mapped_cell_area_um2"] for r in met), default=None),
            "fastest_period_met_ns": min((float(r["clock_period_ns"]) for r in met), default=None),
            "area_1ghz_um2": one["mapped_cell_area_um2"] if one else None,
            "wns_1ghz_ns": one["wns_ns"] if one else None,
            "timing_met_1ghz": one["timing_met"] if one else None,
            "brick_count_precompile": one["brick_instance_count_precompile"] if one else None,
            "dw_mult_count_precompile": one["dw_mult_instance_count_precompile"] if one else None,
            "report_other_multiplier_rows": one["report_other_multiplier_rows"] if one else None,
            "library_set_id": first.get("library_set_id", ""),
            "status": "complete" if len(good) == len(group_rows) else "incomplete",
        })
    write_csv(output / "fusion16_group_summary.csv", summary)
    print(f"Wrote {len(rows)} raw rows and {len(summary)} group summaries")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations
import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
RESULTS = ROOT / "results"

AREA_PATTERNS = {
    "combinational_area_um2": r"Combinational area:\s*([0-9eE+\-.]+)",
    "noncombinational_area_um2": r"Noncombinational area:\s*([0-9eE+\-.]+)",
    "buf_inv_area_um2": r"Buf/Inv area:\s*([0-9eE+\-.]+)",
    "net_interconnect_area_um2": r"Net Interconnect area:\s*([0-9eE+\-.]+)",
    "total_cell_area_report_um2": r"Total cell area:\s*([0-9eE+\-.]+)",
    "total_area_report_um2": r"Total area:\s*([0-9eE+\-.]+)",
}

def parse_kv(path):
    data = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    return data

def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def main():
    RESULTS.mkdir(exist_ok=True)
    rows = []
    manifest_path = BUILD / "runs.csv"
    if not manifest_path.exists():
        raise SystemExit("No build/runs.csv found.")
    with manifest_path.open(encoding="utf-8-sig") as f:
        manifest_rows = list(csv.DictReader(f))
    for manifest_row in manifest_rows:
        run_dir = Path(manifest_row["run_dir"])
        meta_path = run_dir / "meta.json"
        if not meta_path.exists():
            raise SystemExit(f"Missing metadata: {meta_path}")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        summary = parse_kv(run_dir / "summary.kv")
        area_text = ""
        area_path = run_dir / "reports/report_area.rpt"
        if area_path.exists():
            area_text = area_path.read_text(encoding="utf-8", errors="ignore")

        area_values = {}
        for key, pattern in AREA_PATTERNS.items():
            match = re.search(pattern, area_text)
            area_values[key] = to_float(match.group(1)) if match else None
        mapped_area = to_float(summary.get("mapped_cell_area_um2"))
        if mapped_area is None:
            mapped_area = area_values["total_cell_area_report_um2"]

        row = dict(meta)
        row.update({
            "library_set_id": summary.get("library_set_id", ""),
            "target_libraries": summary.get("target_libraries", ""),
            "compile_mode": summary.get("compile_mode", ""),
            "keep_hierarchy": summary.get("keep_hierarchy", ""),
            "operating_condition_requested": summary.get("operating_condition_requested", ""),
            "max_cores": summary.get("max_cores", ""),
            "library_setup_sha256": summary.get("library_setup_sha256", ""),
            "mapped_cell_area_um2": mapped_area,
            "leaf_cell_count": to_float(summary.get("leaf_cell_count")),
            "blackbox_count": to_float(summary.get("blackbox_count")),
            "wns_ns": to_float(summary.get("wns_ns")),
            "critical_delay_ns": to_float(summary.get("critical_delay_ns")),
            "achieved_fmax_mhz": to_float(summary.get("achieved_fmax_mhz")),
            "timing_met": int(float(summary["timing_met"])) if summary.get("timing_met") not in (None, "", "NA") else "",
            "tool_version": summary.get("tool_version", ""),
            "status": "ok" if summary else "missing_summary",
            "report_dir": str((run_dir / "reports").resolve()),
        })
        row.update(area_values)
        rows.append(row)

    if not rows:
        raise SystemExit("No runs found in build/runs.csv.")

    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    raw_path = RESULTS / "area_22nm_raw.csv"
    with raw_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    by_group = defaultdict(list)
    for row in rows:
        by_group[row["group_id"]].append(row)
    summary_rows = []
    for group_id, grows in sorted(by_group.items()):
        good = [r for r in grows if r["status"] == "ok" and r["mapped_cell_area_um2"] not in (None, 0)]
        met = [r for r in good if r["timing_met"] == 1]
        min_area = min((r["mapped_cell_area_um2"] for r in met), default=None)
        best_period = None
        if met:
            best_period = min(r["clock_period_ns"] for r in met)
        max_fmax = max((r["achieved_fmax_mhz"] for r in good if r["achieved_fmax_mhz"] is not None), default=None)
        first = grows[0]
        summary_rows.append({
            "group_id": group_id,
            "tier": first["tier"],
            "category": first["category"],
            "template": first["template"],
            "format": first["format"],
            "w_bits": first["w_bits"],
            "a_bits": first["a_bits"],
            "k_bits": first["k_bits"],
            "v_bits": first["v_bits"],
            "run_count": len(grows),
            "valid_area_count": len(good),
            "timing_met_count": len(met),
            "min_area_among_timing_met_um2": min_area,
            "fastest_period_met_ns": best_period,
            "max_achieved_fmax_mhz": max_fmax,
            "library_set_id": first.get("library_set_id", ""),
            "status": "complete" if len(good) == len(grows) else "incomplete",
        })
    group_path = RESULTS / "area_22nm_group_summary.csv"
    with group_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"Wrote {raw_path}")
    print(f"Wrote {group_path}")

if __name__ == "__main__":
    main()

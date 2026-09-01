#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path


AREA_PATTERNS = {
    "combinational_area_um2": r"Combinational area:\s*([0-9eE+\-.]+)",
    "noncombinational_area_um2": r"Noncombinational area:\s*([0-9eE+\-.]+)",
    "buf_inv_area_um2": r"Buf/Inv area:\s*([0-9eE+\-.]+)",
    "net_interconnect_area_um2": r"Net Interconnect area:\s*([0-9eE+\-.]+)",
    "total_cell_area_report_um2": r"Total cell area:\s*([0-9eE+\-.]+)",
}


def read_kv(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    return data


def number(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def integer(value: object) -> int | None:
    value_f = number(value)
    return None if value_f is None else int(value_f)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", default="build_mixed")
    parser.add_argument("--output-dir", default="results")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    build_dir = (root / args.build_dir).resolve()
    output_dir = (root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_rows: list[dict[str, object]] = []
    manifest_path = build_dir / "runs.csv"
    if not manifest_path.exists():
        raise SystemExit(f"Missing manifest: {manifest_path}")
    with manifest_path.open(encoding="utf-8-sig") as handle:
        manifest_rows = list(csv.DictReader(handle))
    for manifest_row in manifest_rows:
        run_dir = Path(manifest_row["run_dir"])
        meta_path = run_dir / "meta.json"
        if not meta_path.exists():
            raise SystemExit(f"Missing metadata: {meta_path}")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        summary = read_kv(run_dir / "summary.kv")
        area_report = run_dir / "reports" / "report_area.rpt"
        area_text = (
            area_report.read_text(encoding="utf-8", errors="ignore")
            if area_report.exists()
            else ""
        )
        row: dict[str, object] = {
            **meta,
            "library_set_id": summary.get("library_set_id", ""),
            "target_libraries": summary.get("target_libraries", ""),
            "compile_mode": summary.get("compile_mode", ""),
            "keep_hierarchy": summary.get("keep_hierarchy", ""),
            "max_cores": summary.get("max_cores", ""),
            "mapped_cell_area_um2": number(summary.get("mapped_cell_area_um2")),
            "leaf_cell_count": integer(summary.get("leaf_cell_count")),
            "blackbox_count": integer(summary.get("blackbox_count")),
            "wns_ns": number(summary.get("wns_ns")),
            "critical_delay_ns": number(summary.get("critical_delay_ns")),
            "achieved_fmax_mhz": number(summary.get("achieved_fmax_mhz")),
            "timing_met": integer(summary.get("timing_met")),
            "rtl_bundle_sha256_reported": summary.get("rtl_bundle_sha256", ""),
            "library_setup_sha256": summary.get("library_setup_sha256", ""),
            "tool_version": summary.get("tool_version", ""),
            "status": "ok" if summary else "missing_summary",
            "report_dir": str((run_dir / "reports").resolve()),
        }
        for key, pattern in AREA_PATTERNS.items():
            match = re.search(pattern, area_text)
            row[key] = number(match.group(1)) if match else None
        if row["mapped_cell_area_um2"] is None:
            row["mapped_cell_area_um2"] = row["total_cell_area_report_um2"]
        raw_rows.append(row)

    if not raw_rows:
        raise SystemExit(f"No meta.json found under {build_dir}")
    write_csv(output_dir / "mixed_area_raw.csv", raw_rows)

    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in raw_rows:
        groups[str(row["group_id"])].append(row)

    group_rows: list[dict[str, object]] = []
    for group_id, rows in sorted(groups.items()):
        good = [
            row for row in rows
            if row["status"] == "ok"
            and number(row["mapped_cell_area_um2"]) not in (None, 0.0)
        ]
        met = [row for row in good if integer(row["timing_met"]) == 1]
        at_1ghz = [
            row for row in good
            if abs(float(row["clock_period_ns"]) - 1.0) < 1e-9
        ]
        one = at_1ghz[0] if at_1ghz else None
        best = min(
            (float(row["mapped_cell_area_um2"]) for row in met),
            default=None,
        )
        one_area = number(one["mapped_cell_area_um2"]) if one else None
        first = rows[0]
        group_rows.append(
            {
                "group_id": group_id,
                "base_group": first.get("base_group", ""),
                "architecture_class": first["architecture_class"],
                "rtl_topology": first["rtl_topology"],
                "supported_modes": first["supported_modes"],
                "throughput_contract": first["throughput_contract"],
                "accumulator_contract": first["accumulator_contract"],
                "notes": first.get("notes", ""),
                "run_count": len(rows),
                "valid_area_count": len(good),
                "timing_met_count": len(met),
                "best_feasible_area_um2": best,
                "fastest_period_met_ns": min(
                    (float(row["clock_period_ns"]) for row in met),
                    default=None,
                ),
                "area_1ghz_um2": one_area,
                "wns_1ghz_ns": number(one["wns_ns"]) if one else None,
                "timing_met_1ghz": integer(one["timing_met"]) if one else None,
                "area_1ghz_vs_best_ratio": (
                    one_area / best
                    if one_area is not None and best not in (None, 0.0)
                    else None
                ),
                "library_set_id": first.get("library_set_id", ""),
                "compile_mode": first.get("compile_mode", ""),
                "status": "complete" if len(good) == len(rows) else "incomplete",
            }
        )
    write_csv(output_dir / "mixed_group_summary.csv", group_rows)
    print(f"Wrote {len(raw_rows)} raw rows and {len(group_rows)} group rows")


if __name__ == "__main__":
    main()

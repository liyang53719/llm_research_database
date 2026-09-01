#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_REPORTS = (
    "report_area.rpt",
    "report_qor.rpt",
    "report_resources.rpt",
    "check_design_post.rpt",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default="results/mixed_area_raw.csv")
    parser.add_argument("--manifest", default="build_mixed/runs.csv")
    args = parser.parse_args()

    cfg = json.loads((ROOT / "config/mixed_characterization.json").read_text())
    groups = read_csv(ROOT / "config/mixed_experiment_groups.csv")
    manifest = read_csv((ROOT / args.manifest).resolve())
    rows = read_csv((ROOT / args.raw).resolve())
    expected_groups = {row["group_id"] for row in groups}
    expected_runs = {row["run_id"] for row in manifest}
    periods = sorted(float(value) for value in cfg["clock_periods_ns"])

    errors: list[str] = []
    warnings: list[str] = []
    if len(groups) != cfg["unique_groups"]:
        errors.append(f"Configured group count {len(groups)} != {cfg['unique_groups']}")
    if len(manifest) != cfg["expected_dc_runs"]:
        errors.append(f"Manifest rows {len(manifest)} != {cfg['expected_dc_runs']}")
    if len(rows) != len(manifest):
        errors.append(f"Raw rows {len(rows)} != manifest rows {len(manifest)}")
    if {row["run_id"] for row in rows} != expected_runs:
        errors.append("Raw run IDs do not exactly match manifest")
    if {row["group_id"] for row in manifest} != expected_groups:
        errors.append("Manifest group set does not match experiment definition")

    by_group: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_group[row["group_id"]].append(row)
        run_id = row["run_id"]
        try:
            if float(row["mapped_cell_area_um2"]) <= 0:
                errors.append(f"{run_id}: non-positive mapped area")
        except Exception:
            errors.append(f"{run_id}: missing mapped area")
        if row.get("status") != "ok":
            errors.append(f"{run_id}: status={row.get('status')}")
        if row.get("blackbox_count") not in {"0", "0.0"}:
            errors.append(f"{run_id}: blackbox_count={row.get('blackbox_count')}")
        if row.get("rtl_bundle_sha256_reported") != row.get("rtl_bundle_sha256"):
            errors.append(f"{run_id}: reported RTL hash mismatch")

        run_dir = Path(row["run_dir"])
        for report in REQUIRED_REPORTS:
            path = run_dir / "reports" / report
            if not path.is_file() or path.stat().st_size == 0:
                errors.append(f"{run_id}: missing or empty {report}")
        stdout = run_dir / "dc_stdout.log"
        if not stdout.is_file():
            errors.append(f"{run_id}: missing dc_stdout.log")
        else:
            text = stdout.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"^(Error|Fatal):", text, flags=re.MULTILINE):
                errors.append(f"{run_id}: DC log contains Error/Fatal")

        if row.get("architecture_class") == "array":
            wrapper = (run_dir / "char_top.sv").read_text(encoding="utf-8")
            if "int_" not in wrapper or "fp_" not in wrapper:
                errors.append(f"{run_id}: array wrapper does not expose both INT and FP outputs")

    for group_id in sorted(expected_groups):
        grows = by_group.get(group_id, [])
        observed_periods = sorted(float(row["clock_period_ns"]) for row in grows)
        if observed_periods != periods:
            errors.append(f"{group_id}: period set {observed_periods} != {periods}")
        if grows and not any(row.get("timing_met") in {"1", "1.0"} for row in grows):
            warnings.append(f"{group_id}: no common period met timing")
        valid = sorted(
            (
                (float(row["clock_period_ns"]), float(row["mapped_cell_area_um2"]))
                for row in grows
            ),
            reverse=True,
        )
        for (loose_p, loose_a), (tight_p, tight_a) in zip(valid, valid[1:]):
            if tight_a < loose_a * (1.0 - 1e-6):
                warnings.append(
                    f"{group_id}: area decreased for {loose_p}ns -> {tight_p}ns "
                    f"({loose_a} -> {tight_a} um2); retain point"
                )

    for field in (
        "library_set_id",
        "target_libraries",
        "compile_mode",
        "library_setup_sha256",
        "rtl_bundle_sha256",
        "tool_version",
    ):
        values = {row.get(field, "").strip() for row in rows if row.get(field, "").strip()}
        if len(values) != 1:
            errors.append(f"Comparison field {field} has {len(values)} non-empty values")

    for row in rows:
        if row["architecture_class"] == "shared_native":
            expected = r"DW_fp_add"
        elif row["architecture_class"] in {"reference", "separate", "dual_domain", "convert_fp", "array"} and "FP" in row["supported_modes"]:
            expected = r"DW_.*fp|DW_fp"
        else:
            continue
        resources = Path(row["run_dir"]) / "reports/report_resources.rpt"
        if resources.is_file() and not re.search(expected, resources.read_text(errors="ignore"), re.IGNORECASE):
            errors.append(f"{row['run_id']}: required DW floating resource not reported")

    report = ROOT / "results/validation_report.txt"
    with report.open("w", encoding="utf-8") as handle:
        handle.write(
            f"Expected groups: {cfg['unique_groups']}\nExpected runs: {cfg['expected_dc_runs']}\n"
            f"Observed groups: {len(by_group)}\nObserved rows: {len(rows)}\n"
            f"Common periods ns: {periods}\n\nERRORS\n"
        )
        handle.write("\n".join(errors) if errors else "NONE")
        handle.write("\n\nWARNINGS\n")
        handle.write("\n".join(warnings) if warnings else "NONE")
        handle.write("\n")
    print(report.read_text(encoding="utf-8"))
    if errors:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--raw", default="results/local_dc/fusion16_area_raw.csv")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    cfg = json.loads((root / "config/characterization.json").read_text(encoding="utf-8"))
    with (root / "config/dc_experiments.csv").open(encoding="utf-8-sig") as f:
        experiments = list(csv.DictReader(f))
    expected_groups = {row["group_id"]: row for row in experiments}
    with (root / args.raw).open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    errors = []
    warnings = []
    if len(rows) != cfg["expected_runs"]:
        errors.append(f'Expected {cfg["expected_runs"]} rows, found {len(rows)}')
    run_ids = [row.get("run_id", "") for row in rows]
    if len(set(run_ids)) != len(run_ids):
        errors.append("Duplicate run_id rows")
    by_group = defaultdict(list)
    for row in rows:
        by_group[row["group_id"]].append(row)
        if row.get("status") != "ok":
            errors.append(f'{row.get("run_id")}: status={row.get("status")}')
        try:
            if float(row["mapped_cell_area_um2"]) <= 0:
                errors.append(f'{row.get("run_id")}: non-positive area')
        except Exception:
            errors.append(f'{row.get("run_id")}: missing area')
        if str(row.get("blackbox_count")) not in {"0", "0.0"}:
            errors.append(f'{row.get("run_id")}: blackbox={row.get("blackbox_count")}')
        if row.get("library_set_id") != cfg["library_contract"]["library_set_id"]:
            errors.append(f'{row.get("run_id")}: library_set_id mismatch')
        if cfg["library_contract"]["dc_version_reference"] not in row.get("tool_version", ""):
            errors.append(f'{row.get("run_id")}: tool version mismatch')
        if row.get("rtl_bundle_sha256") != row.get("rtl_bundle_sha256_reported"):
            errors.append(f'{row.get("run_id")}: RTL bundle hash mismatch')
        if row.get("compile_mode_reported") != "compile_ultra":
            errors.append(f'{row.get("run_id")}: compile mode mismatch')
        if str(row.get("dc_max_cores")) not in {"1", "1.0"}:
            errors.append(f'{row.get("run_id")}: dc_max_cores != 1')
        if str(row.get("dc_error_count")) not in {"0", "0.0"}:
            errors.append(f'{row.get("run_id")}: DC errors={row.get("dc_error_count")}')
        fixed = {
            "input_transition": 0.05,
            "output_load": 0.005,
            "max_transition": 0.20,
            "clock_uncertainty_ratio": 0.05,
            "input_delay_ratio": 0.10,
            "output_delay_ratio": 0.10,
        }
        for field, wanted_value in fixed.items():
            try:
                if abs(float(row[field]) - wanted_value) > 1e-12:
                    errors.append(f'{row.get("run_id")}: {field} mismatch')
            except Exception:
                errors.append(f'{row.get("run_id")}: missing {field}')
        expected = expected_groups.get(row.get("group_id", ""))
        if expected is None:
            errors.append(f'{row.get("run_id")}: unexpected group')
        else:
            wanted = expected["expected_4x4_bricks"]
            if str(row.get("brick_instance_count_precompile")) not in {wanted, wanted + ".0"}:
                errors.append(f'{row.get("run_id")}: brick count != {wanted}')
            if str(row.get("dw_mult_instance_count_precompile")) not in {wanted, wanted + ".0"}:
                errors.append(f'{row.get("run_id")}: DW multiplier count != {wanted}')

    if set(by_group) != set(expected_groups):
        errors.append("Group set mismatch")
    library_hashes = {row.get("library_setup_sha256", "") for row in rows}
    if len(library_hashes) != 1 or "" in library_hashes:
        errors.append("Library setup hash is missing or inconsistent")
    expected_periods = {float(value) for value in cfg["clock_periods_ns"]}
    for group_id, group_rows in by_group.items():
        if len(group_rows) != len(cfg["clock_periods_ns"]):
            errors.append(f"{group_id}: incomplete period sweep")
        got_periods = {float(row["clock_period_ns"]) for row in group_rows}
        if got_periods != expected_periods:
            errors.append(f"{group_id}: period set mismatch")

    for proof_group in ["BRICK16_BARE_PROOF", "FUSION16_CORE_PROOF"]:
        proof_rows = by_group.get(proof_group, [])
        for row in proof_rows:
            if str(row.get("brick_instance_count_precompile")) not in {"16", "16.0"}:
                errors.append(f'{row.get("run_id")}: brick count != 16')
            if str(row.get("dw_mult_instance_count_precompile")) not in {"16", "16.0"}:
                errors.append(f'{row.get("run_id")}: DW 4x4 instance count != 16')
            if str(row.get("report_other_multiplier_rows")) not in {"0", "0.0"}:
                errors.append(f'{row.get("run_id")}: extra multiplier rows detected')

    for group_id, group_rows in by_group.items():
        if not any(str(r.get("timing_met")) in {"1", "1.0"} for r in group_rows):
            warnings.append(f"{group_id}: no timing-met point")

    numeric_path = root / "results/local_dc/numeric_rtl_crosscheck.csv"
    if not numeric_path.exists():
        errors.append("Missing numeric_rtl_crosscheck.csv")
    else:
        with numeric_path.open(encoding="utf-8-sig") as f:
            numeric = list(csv.DictReader(f))
        if len(numeric) != 10:
            errors.append(f"Expected 10 numeric modes, found {len(numeric)}")
        numeric_expected = {
            "I4_I4": 256, "I4_I8": 4096, "I8_I8": 65536,
            "I16_I16": 100000, "FP8_FP8": 65536,
            "BF16_BF16": 100000, "I4_FP8": 4096,
            "I8_FP8": 65536, "I4_BF16": 50000, "I8_BF16": 50000,
        }
        for row in numeric:
            if int(row.get("mismatches", -1)) != 0:
                errors.append(f'{row.get("mode")}: RTL mismatches={row.get("mismatches")}')
            wanted = numeric_expected.get(row.get("mode", ""))
            if wanted is None or int(row.get("pair_count", -1)) < wanted:
                errors.append(f'{row.get("mode")}: insufficient numeric coverage')

    compile_path = root / "results/local_dc/rtl_compile_summary.csv"
    if not compile_path.exists():
        errors.append("Missing rtl_compile_summary.csv")
    else:
        with compile_path.open(encoding="utf-8-sig") as f:
            compile_rows = list(csv.DictReader(f))
        if len(compile_rows) != 10 or any(row.get("status") != "pass" for row in compile_rows):
            errors.append("RTL top compile gate failed or incomplete")

    latency_path = root / "results/local_dc/pipeline_latency.csv"
    if not latency_path.exists():
        errors.append("Missing pipeline_latency.csv")
    else:
        with latency_path.open(encoding="utf-8-sig") as f:
            latency_rows = list(csv.DictReader(f))
        got_latency = {row["path"]: int(row["latency_cycles"]) for row in latency_rows}
        if got_latency != {"integer": 1, "floating": 3}:
            errors.append(f"Pipeline latency mismatch: {got_latency}")
        if any(row.get("status") != "pass" for row in latency_rows):
            errors.append("Pipeline latency test failed")

    report = root / "results/local_dc/validation_report.txt"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "ERRORS\n" + ("\n".join(errors) if errors else "NONE")
        + "\n\nWARNINGS\n" + ("\n".join(warnings) if warnings else "NONE") + "\n",
        encoding="utf-8",
    )
    print(report.read_text(encoding="utf-8"))
    if errors:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

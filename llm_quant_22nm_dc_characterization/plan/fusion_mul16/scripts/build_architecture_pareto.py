#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def f(row: dict, key: str) -> float:
    return float(row[key])


def main() -> None:
    summary_rows = read_csv(ROOT / "results/local_dc/fusion16_group_summary.csv")
    summary = {row["group_id"]: row for row in summary_rows}
    required = {
        "FUSION16_INT_ONLY_PIPE", "FUSION16_FP8_ONLY_PIPE",
        "FUSION16_BF16_ONLY_PIPE", "FUSION16_SHARED_FULL_PIPE",
        "FUSION16_SEPARATE_FULL_PIPE", "FUSION16_DUAL_SHARED_PIPE",
    }
    missing = sorted(required - set(summary))
    if missing:
        raise SystemExit("Missing groups: " + ", ".join(missing))

    separate_area = f(summary["FUSION16_SEPARATE_FULL_PIPE"], "area_1ghz_um2")
    dedicated_groups = [
        summary["FUSION16_INT_ONLY_PIPE"],
        summary["FUSION16_FP8_ONLY_PIPE"],
        summary["FUSION16_BF16_ONLY_PIPE"],
    ]
    dedicated_sum = sum(f(row, "area_1ghz_um2") for row in dedicated_groups)

    definitions = [
        ("FUSION16_SHARED_FULL_PIPE", f(summary["FUSION16_SHARED_FULL_PIPE"], "area_1ghz_um2"),
         8, 4, 16, 4, 4, 1, int(float(summary["FUSION16_SHARED_FULL_PIPE"]["timing_met_1ghz"])),
         "exclusive_mode_match"),
        ("FUSION16_DUAL_SHARED_PIPE", f(summary["FUSION16_DUAL_SHARED_PIPE"], "area_1ghz_um2"),
         16, 8, 32, 8, 8, 2, int(float(summary["FUSION16_DUAL_SHARED_PIPE"]["timing_met_1ghz"])),
         "partial_concurrency_match"),
        ("FUSION16_SEPARATE_FULL_PIPE", separate_area,
         8, 4, 16, 4, 4, 3, int(float(summary["FUSION16_SEPARATE_FULL_PIPE"]["timing_met_1ghz"])),
         "full_concurrency_reference"),
        ("RIGHT_SIZED_DEDICATED_SUM", dedicated_sum,
         8, 4, 16, 4, 4, 3,
         int(all(int(float(row["timing_met_1ghz"])) for row in dedicated_groups)),
         "full_concurrency_component_sum"),
    ]
    rows = []
    for name, area, i4i8, i8i8, fp8, bf16, dots, concurrency, timing, match in definitions:
        rows.append({
            "architecture": name,
            "area_1ghz_um2": area,
            "timing_met_1ghz": timing,
            "int4xint8_products_per_cycle": i4i8,
            "int8xint8_products_per_cycle": i8i8,
            "fp8_products_per_cycle": fp8,
            "bf16_products_per_cycle": bf16,
            "dot_outputs_per_cycle": dots,
            "concurrent_mode_count": concurrency,
            "int_latency_cycles": 1,
            "fp_latency_cycles": 3,
            "accumulator_contract": "INT48 plus FP32 DW_fp_add ieee_compliance=0",
            "throughput_match": match,
            "reference_architecture": "FUSION16_SEPARATE_FULL_PIPE",
            "area_ratio": area / separate_area,
            "area_saving_pct": 100.0 * (1.0 - area / separate_area),
            "pareto_eligible_1ghz": timing,
            "pareto_scope": "area and declared throughput only; timing is a separate hard gate",
            "pareto_dominated": 0,
        })

    objectives = [
        "int4xint8_products_per_cycle", "int8xint8_products_per_cycle",
        "fp8_products_per_cycle", "bf16_products_per_cycle",
        "dot_outputs_per_cycle", "concurrent_mode_count",
    ]
    for row in rows:
        for other in rows:
            if row is other:
                continue
            no_worse = float(other["area_1ghz_um2"]) <= float(row["area_1ghz_um2"])
            no_worse &= all(int(other[key]) >= int(row[key]) for key in objectives)
            strict = float(other["area_1ghz_um2"]) < float(row["area_1ghz_um2"])
            strict |= any(int(other[key]) > int(row[key]) for key in objectives)
            if no_worse and strict:
                row["pareto_dominated"] = 1
                break

    output = ROOT / "results/local_dc/architecture_pareto.csv"
    with output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    shared = rows[0]
    dual = rows[1]
    proof_path = ROOT / "results/local_dc/brick_sharing_proof.json"
    proof = json.loads(proof_path.read_text(encoding="utf-8")) if proof_path.exists() else {}
    numeric = read_csv(ROOT / "results/local_dc/numeric_rtl_crosscheck.csv")
    numeric_pass = len(numeric) == 10 and all(int(row["mismatches"]) == 0 for row in numeric)
    shared_core_gates = (
        bool(shared["timing_met_1ghz"])
        and bool(proof.get("pass"))
        and numeric_pass
        and float(shared["area_1ghz_um2"]) < separate_area
    )
    decision = {
        "shared_1ghz_timing_met": bool(shared["timing_met_1ghz"]),
        "shared_exclusive_area_lt_separate": float(shared["area_1ghz_um2"]) < separate_area,
        "dual_1ghz_timing_met": bool(dual["timing_met_1ghz"]),
        "dual_area_lt_separate": float(dual["area_1ghz_um2"]) < separate_area,
        "dual_concurrency_boundary": "two independently selected modes, not three concurrent dedicated modes",
        "brick_sharing_proof_pass": bool(proof.get("pass")),
        "numeric_rtl_zero_mismatch": numeric_pass,
        "fp_accumulator_contract": "FP32 DW_fp_add ieee_compliance=0; model acceptance of denormal handling remains required",
        "shared_core_gates_pass": shared_core_gates,
        "decision_status": (
            "conditional_candidate_pending_model_fp_accumulator_acceptance"
            if shared_core_gates else "rejected_by_measured_core_gate"
        ),
    }
    (ROOT / "results/local_dc/architecture_decision.json").write_text(
        json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()

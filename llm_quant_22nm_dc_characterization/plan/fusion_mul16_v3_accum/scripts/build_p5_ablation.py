#!/usr/bin/env python3
"""Build the P5 evidence table and provisional architecture decision.

P5 is intentionally a report-only step: it consumes the common 1 GHz DC
table and synthetic gate, and does not introduce another timing point or
change the v2 product-pipe baseline.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def fnum(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "", "NA") else None
    except ValueError:
        return None


def main() -> None:
    dc = {row["group_id"]: row for row in rows(ROOT / "results/local_dc/v3_area_1ghz.csv")}
    comparison = {row["accum_style"]: row for row in rows(ROOT / "results/local_dc/v3_architecture_comparison.csv")}
    gates = {row["accum_style"]: row for row in rows(ROOT / "results/synthetic_numeric_gate.csv")}
    cfg = json.loads((ROOT / "config/decision_gates.json").read_text(encoding="utf-8"))
    refs = cfg["v2_area_references_um2"]

    baseline_rows = [
        ("v2_accum_full_bf16_baseline", refs["accum_full_bf16"], "V2_BF16_ACCUM_ONLY", "v2 reference; reproduction checked against v3 accumulator-only"),
        ("v2_cluster_full7_baseline", refs["cluster_full_bf16_full7"], "V2_SHARED_FULL7_FTZ", "v2 reference; reproduction checked against v3 full cluster"),
    ]
    out: list[dict[str, object]] = []
    for case, area, ref, note in baseline_rows:
        measured = fnum(dc["V3_ACC_FULL_BF16" if "accum" in case else "V3_CLUSTER_FULL_BF16_FULL7"]["mapped_cell_area_um2"])
        out.append({
            "p5_case": case,
            "kind": "v2_baseline",
            "style": "full_bf16",
            "group_id": ref,
            "area_1ghz_um2": area,
            "measured_v3_area_um2": measured,
            "delta_vs_v2_pct": (measured / area - 1.0) * 100.0 if measured is not None else None,
            "timing_met_1ghz": "NA",
            "synthetic_gate_pass": "NA",
            "eligible": 0,
            "note": note,
        })

    for style, group in (
        ("full_bf16", "V3_CLUSTER_FULL_BF16_FULL7"),
        ("bf16_tree_fp32_recurrent", "V3_CLUSTER_TREE_FP32_REC_FULL7"),
        ("bf16_block64_fp32_checkpoint", "V3_CLUSTER_BLOCK64_FP32_CKPT_FULL7"),
    ):
        row = comparison[style]
        dc_row = dc[group]
        gate = gates[style]
        timing = int(float(row["timing_met_1ghz"]))
        gate_pass = int(float(gate["synthetic_gate_pass"]))
        out.append({
            "p5_case": f"v3_{style}_full_cluster",
            "kind": "v3_candidate",
            "style": style,
            "group_id": group,
            "area_1ghz_um2": fnum(dc_row["mapped_cell_area_um2"]),
            "measured_v3_area_um2": fnum(dc_row["mapped_cell_area_um2"]),
            "delta_vs_v2_pct": None,
            "timing_met_1ghz": timing,
            "synthetic_gate_pass": gate_pass,
            "eligible": int(timing and gate_pass),
            "note": "target-model accuracy remains OPEN",
        })

    out_dir = ROOT / "results/local_dc"
    with (out_dir / "p5_ablation.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)

    candidates = [row for row in out if row["kind"] == "v3_candidate" and row["eligible"] == 1]
    selected = min(candidates, key=lambda row: float(row["area_1ghz_um2"])) if candidates else None
    decision = {
        "stage": "P5",
        "status": "PROVISIONAL_SYNTHETIC_SELECTION" if selected else "NO_ELIGIBLE_STYLE",
        "selected_style": selected["style"] if selected else None,
        "selected_group": selected["group_id"] if selected else None,
        "selection_rule": "minimum full-cluster mapped-cell area among 1 GHz timing-closed and synthetic-gate-passing candidates",
        "baseline_tolerance_pct": cfg["baseline_reproduction_tolerance_pct"],
        "target_model_accuracy": "OPEN",
        "rows": out,
    }
    (out_dir / "p5_ablation_decision.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()

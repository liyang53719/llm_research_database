#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def number(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def integer(value: object) -> int | None:
    value_f = number(value)
    return None if value_f is None else int(value_f)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default="results/mixed_group_summary.csv")
    parser.add_argument(
        "--comparisons", default="config/architecture_comparisons.csv"
    )
    parser.add_argument(
        "--output", default="results/mixed_architecture_comparison.csv"
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    summary = {
        row["group_id"]: row for row in read_csv((root / args.summary).resolve())
    }
    comparisons = read_csv((root / args.comparisons).resolve())
    output_rows: list[dict[str, object]] = []

    for comparison in comparisons:
        candidate = summary.get(comparison["candidate_group"])
        reference_ids = comparison["reference_groups"].split(";")
        references = [summary.get(group_id) for group_id in reference_ids]

        if candidate is None or any(row is None for row in references):
            output_rows.append(
                {
                    "candidate_group": comparison["candidate_group"],
                    "reference_groups": comparison["reference_groups"],
                    "area_basis": "",
                    "comparison_status": "missing_group",
                }
            )
            continue

        typed_references = [row for row in references if row is not None]
        for area_key in ("area_1ghz_um2", "best_feasible_area_um2"):
            candidate_area = number(candidate.get(area_key))
            reference_areas = [
                number(row.get(area_key)) for row in typed_references
            ]
            reference_sum = (
                sum(value for value in reference_areas if value is not None)
                if all(value is not None for value in reference_areas)
                else None
            )
            ratio = (
                candidate_area / reference_sum
                if candidate_area is not None
                and reference_sum not in (None, 0.0)
                else None
            )
            timing_ok = integer(candidate.get("timing_met_1ghz"))
            reference_timing = [
                integer(row.get("timing_met_1ghz")) for row in typed_references
            ]
            throughput_match = comparison["throughput_match"].lower()
            if throughput_match == "false":
                status = "not_throughput_equivalent"
            elif throughput_match != "true":
                status = "partial_throughput_match"
            elif candidate_area is None or reference_sum is None:
                status = "missing_area"
            elif area_key == "area_1ghz_um2" and timing_ok != 1:
                status = "candidate_1ghz_timing_fail"
            elif area_key == "area_1ghz_um2" and any(value != 1 for value in reference_timing):
                status = "reference_1ghz_timing_fail"
            else:
                status = "comparable"

            output_rows.append(
                {
                    "candidate_group": comparison["candidate_group"],
                    "reference_groups": comparison["reference_groups"],
                    "area_basis": area_key,
                    "candidate_area_um2": candidate_area,
                    "reference_area_sum_um2": reference_sum,
                    "area_delta_um2": (
                        candidate_area - reference_sum
                        if candidate_area is not None and reference_sum is not None
                        else None
                    ),
                    "area_ratio": ratio,
                    "area_saving_pct": (
                        (1.0 - ratio) * 100.0 if ratio is not None else None
                    ),
                    "throughput_contract": comparison["throughput_contract"],
                    "throughput_match": comparison["throughput_match"],
                    "candidate_timing_met_1ghz": timing_ok,
                    "reference_timing_met_1ghz": ";".join(
                        "" if value is None else str(value) for value in reference_timing
                    ),
                    "candidate_accumulator_contract": candidate.get(
                        "accumulator_contract", ""
                    ),
                    "comparison_status": status,
                }
            )

    output = (root / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"Wrote {len(output_rows)} rows to {output}")


if __name__ == "__main__":
    main()

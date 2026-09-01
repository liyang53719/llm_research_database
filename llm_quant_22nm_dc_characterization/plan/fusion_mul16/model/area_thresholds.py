from __future__ import annotations

import csv
from pathlib import Path


MEASURED = {
    "w4a8_one_lane": 242.788002,
    "w8a8_one_lane_proxy": 154.92750325,
    "fp8_one_lane": 245.700000,
    "bf16_one_lane": 628.901004,
    "old_shared_native": 2027.389016,
}


def build_rows() -> list[dict[str, float | str]]:
    scenarios = [
        (
            "Fusion16 matched: 8x W4A8 + 16x FP8",
            8 * MEASURED["w4a8_one_lane"] + 16 * MEASURED["fp8_one_lane"],
        ),
        (
            "Fusion16 matched: 8x W4A8 + 16x FP8 + 4x BF16",
            8 * MEASURED["w4a8_one_lane"]
            + 16 * MEASURED["fp8_one_lane"]
            + 4 * MEASURED["bf16_one_lane"],
        ),
        (
            "Conservative lane4: 8x W4A8 + 4x FP8 + 4x BF16",
            8 * MEASURED["w4a8_one_lane"]
            + 4 * MEASURED["fp8_one_lane"]
            + 4 * MEASURED["bf16_one_lane"],
        ),
        (
            "Fusion16 matched: 4x W8A8 + 16x FP8 + 4x BF16",
            4 * MEASURED["w8a8_one_lane_proxy"]
            + 16 * MEASURED["fp8_one_lane"]
            + 4 * MEASURED["bf16_one_lane"],
        ),
    ]
    rows = []
    for name, area in scenarios:
        rows.append(
            {
                "matched_separate_reference": name,
                "reference_area_um2": area,
                "fusion16_must_be_below_um2": area,
                "old_shared_native_area_um2": MEASURED["old_shared_native"],
                "old_shared_native_ratio_to_reference": MEASURED["old_shared_native"] / area,
            }
        )
    return rows


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "results" / "area_thresholds.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(out)

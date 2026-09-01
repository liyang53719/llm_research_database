from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def make_row(name: str, int_area: float, fp_area: float) -> dict:
    return {
        "pair": name,
        "int_area_per_mac_um2": int_area,
        "float_area_per_mac_um2": fp_area,
        "separate_full_throughput_area_um2": int_area + fp_area,
        "hybrid_lower_bound_um2": fp_area,
        "maximum_hybrid_overhead_before_losing_to_two_full_arrays_um2": int_area,
        "maximum_hybrid_overhead_fraction_of_float": int_area / fp_area,
        "separate_float_tile_ratio_break_even_if_hybrid_equals_float":
            max(0.0, 1.0 - int_area / fp_area),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--anchors", default="config/current_22nm_anchors.json")
    parser.add_argument("--output-dir", default="results")
    args = parser.parse_args()
    cfg = json.loads(Path(args.anchors).read_text(encoding="utf-8"))
    a = cfg["areas_um2"]
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    w4a8_pe = a["ARRAY_W4A8_16X16"] / 256.0
    w8a8_pe = a["ARRAY_W8A8_16X16"] / 256.0
    bf16_pe_fail = a["ARRAY_BF16_16X16_1GHZ_FAIL"] / 256.0

    rows = [
        make_row("W4A8 + FP8 E4M3", w4a8_pe, a["FP8_E4M3_SCALAR"]),
        make_row("W8A8 + FP8 E4M3", w8a8_pe, a["FP8_E4M3_SCALAR"]),
        make_row("W4A8 + BF16 (1GHz fail)", w4a8_pe, bf16_pe_fail),
        make_row("W8A8 + BF16 (1GHz fail)", w8a8_pe, bf16_pe_fail),
    ]
    with (out / "hybrid_break_even.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    sweep = []
    for row in rows:
        ai = row["int_area_per_mac_um2"]
        af = row["float_area_per_mac_um2"]
        for ratio in [0.0625, 0.125, 0.25, 0.5, 0.75, 1.0]:
            separate = ai + ratio * af
            for overhead in [0.0, 0.05, 0.10, 0.20, 0.30, 0.50]:
                hybrid = af * (1 + overhead)
                sweep.append(
                    {
                        "pair": row["pair"],
                        "float_tile_ratio": ratio,
                        "hybrid_overhead_fraction_over_float": overhead,
                        "separate_area_um2": separate,
                        "hybrid_area_um2": hybrid,
                        "hybrid_minus_separate_um2": hybrid - separate,
                        "winner": "hybrid" if hybrid < separate else "separate",
                    }
                )
    with (out / "hybrid_ratio_sweep.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(sweep[0]))
        writer.writeheader()
        writer.writerows(sweep)

    summary = {
        "w4a8_array_area_per_pe_um2": w4a8_pe,
        "w8a8_array_area_per_pe_um2": w8a8_pe,
        "bf16_array_area_per_pe_1ghz_fail_um2": bf16_pe_fail,
        "w4a8_pe_area_per_mac_cycle_um2": a["INT_PE_W4A8_L4"] / 4.0,
        "w8a8_pe_area_per_mac_cycle_um2": a["INT_PE_W8A8_L4"] / 4.0,
        "w4a16_integer_pe_area_per_mac_cycle_um2": a["INT_PE_W4A16_L2"] / 2.0,
    }
    (out / "area_dse_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

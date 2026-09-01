from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from numeric_formats import (
    OperandFormat,
    conversion_coverage,
    converted_mixed_dot,
    encode_operand,
    native_mixed_dot,
)


def dot_error_experiment(
    seed: int = 7,
    vectors: int = 400,
    length: int = 128,
) -> list[dict]:
    rng = np.random.default_rng(seed)
    cases = [
        ("I4xFP8", OperandFormat.INT4, OperandFormat.FP8_E4M3FN, OperandFormat.FP8_E4M3FN),
        ("I8xFP8", OperandFormat.INT8, OperandFormat.FP8_E4M3FN, OperandFormat.FP8_E4M3FN),
        ("I4xBF16", OperandFormat.INT4, OperandFormat.BF16, OperandFormat.BF16),
        ("I8xBF16", OperandFormat.INT8, OperandFormat.BF16, OperandFormat.BF16),
    ]
    rows = []
    for name, lhs_fmt, rhs_fmt, target_fmt in cases:
        abs_errors = []
        rel_errors = []
        exact = 0
        for _ in range(vectors):
            if lhs_fmt == OperandFormat.INT4:
                lhs_values = rng.integers(-8, 8, size=length)
            else:
                lhs_values = rng.integers(-128, 128, size=length)
            rhs_values = rng.normal(0.0, 3.0, size=length)
            lhs_raw = [encode_operand(float(x), lhs_fmt) for x in lhs_values]
            rhs_raw = [encode_operand(float(x), rhs_fmt) for x in rhs_values]
            native = float(native_mixed_dot(lhs_raw, rhs_raw, lhs_fmt, rhs_fmt))
            converted = float(
                converted_mixed_dot(lhs_raw, rhs_raw, lhs_fmt, rhs_fmt, target_fmt)
            )
            error = converted - native
            abs_errors.append(abs(error))
            rel_errors.append(abs(error) / max(abs(native), 1e-6))
            exact += int(error == 0.0)
        rows.append(
            {
                "case": name,
                "vectors": vectors,
                "dot_length": length,
                "exact_dot_fraction": exact / vectors,
                "mean_abs_error": float(np.mean(abs_errors)),
                "p99_abs_error": float(np.quantile(abs_errors, 0.99)),
                "mean_relative_error": float(np.mean(rel_errors)),
                "p99_relative_error": float(np.quantile(rel_errors, 0.99)),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="results")
    args = parser.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    coverage = [
        conversion_coverage(OperandFormat.INT4, OperandFormat.FP8_E4M3FN).__dict__,
        conversion_coverage(OperandFormat.INT8, OperandFormat.FP8_E4M3FN).__dict__,
        conversion_coverage(OperandFormat.INT4, OperandFormat.BF16).__dict__,
        conversion_coverage(OperandFormat.INT8, OperandFormat.BF16).__dict__,
    ]
    dot_rows = dot_error_experiment()

    for name, rows in [
        ("conversion_coverage.csv", coverage),
        ("dot_error_experiment.csv", dot_rows),
    ]:
        with (out / name).open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    (out / "numeric_summary.json").write_text(
        json.dumps({"conversion": coverage, "dot_errors": dot_rows}, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

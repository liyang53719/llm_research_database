from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from fusion_mul16_v2_model import (
    bf16_add,
    bf16_to_float,
    float_to_bf16,
)


def quantize_bf16_array(values: np.ndarray) -> np.ndarray:
    bits = values.astype(np.float32).view(np.uint32)
    lsb = (bits >> 16) & 1
    rounded = bits + np.uint32(0x7FFF) + lsb
    bf = (rounded >> 16).astype(np.uint16)
    exp = (bf >> 7) & 0xFF
    bf = np.where(exp == 0, bf & np.uint16(0x8000), bf).astype(np.uint16)
    return bf


def accumulate_bf16_dot(a_bf: np.ndarray, b_bf: np.ndarray) -> int:
    products_f32 = (
        (a_bf.astype(np.uint32) << 16).view(np.float32)
        * (b_bf.astype(np.uint32) << 16).view(np.float32)
    ).astype(np.float32)
    products = quantize_bf16_array(products_f32)
    acc = 0
    for start in range(0, products.size, 4):
        p = list(map(int, products[start:start + 4]))
        p += [0] * (4 - len(p))
        s01 = bf16_add(p[0], p[1])
        s23 = bf16_add(p[2], p[3])
        block = bf16_add(s01, s23)
        acc = bf16_add(acc, block)
    return acc


def run_case(rng: np.random.Generator, input_kind: str, length: int, samples: int) -> dict:
    refs = np.empty(samples, dtype=np.float64)
    outs = np.empty(samples, dtype=np.float64)
    for sample in range(samples):
        a = rng.normal(0.0, 1.0, length).astype(np.float32)
        b = rng.normal(0.0, 1.0, length).astype(np.float32)
        a_bf = quantize_bf16_array(a)
        b_bf = quantize_bf16_array(b)
        if input_kind == "fp8_proxy":
            # E4M3-like precision proxy: retain BF16 exponent but keep three fraction bits.
            a_bf = (a_bf & np.uint16(0xFFF0)).astype(np.uint16)
            b_bf = (b_bf & np.uint16(0xFFF0)).astype(np.uint16)
        a_f = (a_bf.astype(np.uint32) << 16).view(np.float32)
        b_f = (b_bf.astype(np.uint32) << 16).view(np.float32)
        refs[sample] = np.dot(a_f.astype(np.float64), b_f.astype(np.float64))
        outs[sample] = float(bf16_to_float(accumulate_bf16_dot(a_bf, b_bf)))

    error = outs - refs
    ref_rms = float(np.sqrt(np.mean(refs * refs)))
    nrmse = float(np.sqrt(np.mean(error * error)) / max(ref_rms, 1e-30))
    threshold = max(ref_rms * 0.1, 1e-6)
    rel = np.abs(error[np.abs(refs) > threshold] / refs[np.abs(refs) > threshold])
    return {
        "input_kind": input_kind,
        "dot_length": length,
        "samples": samples,
        "reference_rms": ref_rms,
        "nrmse": nrmse,
        "median_relative_error_filtered": float(np.median(rel)) if rel.size else None,
        "p95_relative_error_filtered": float(np.quantile(rel, 0.95)) if rel.size else None,
        "p99_relative_error_filtered": float(np.quantile(rel, 0.99)) if rel.size else None,
        "max_abs_error": float(np.max(np.abs(error))),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/bf16_accum_error.csv")
    args = parser.parse_args()
    rng = np.random.default_rng(20260902)
    rows = []
    for kind in ("fp8_proxy", "bf16"):
        for length, samples in ((16, 1000), (64, 800), (128, 600), (256, 400), (1024, 160)):
            rows.append(run_case(rng, kind, length, samples))
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()

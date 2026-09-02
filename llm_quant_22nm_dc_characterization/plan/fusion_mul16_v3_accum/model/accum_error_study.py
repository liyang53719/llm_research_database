from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from accum_v3_model import bf16_array_to_float, quantize_bf16_array


def bf16_add_vec(a_bits: np.ndarray, b_bits: np.ndarray) -> np.ndarray:
    a = bf16_array_to_float(np.asarray(a_bits, dtype=np.uint16))
    b = bf16_array_to_float(np.asarray(b_bits, dtype=np.uint16))
    return quantize_bf16_array(np.add(a, b, dtype=np.float32))


def tree4_vec(items: np.ndarray) -> np.ndarray:
    """items: [samples, 4] BF16 raw values."""
    s01 = bf16_add_vec(items[:, 0], items[:, 1])
    s23 = bf16_add_vec(items[:, 2], items[:, 3])
    return bf16_add_vec(s01, s23)


def make_inputs(
    rng: np.random.Generator,
    input_kind: str,
    distribution: str,
    samples: int,
    length: int,
) -> tuple[np.ndarray, np.ndarray, int]:
    shape = (samples, length)
    if distribution == 'gaussian':
        a = rng.normal(0.0, 1.0, shape).astype(np.float32)
        b = rng.normal(0.0, 1.0, shape).astype(np.float32)
    elif distribution == 'positive':
        a = np.abs(rng.normal(0.0, 1.0, shape)).astype(np.float32)
        b = np.abs(rng.normal(0.0, 1.0, shape)).astype(np.float32)
    elif distribution == 'outlier':
        a = rng.normal(0.0, 1.0, shape).astype(np.float32)
        b = rng.normal(0.0, 1.0, shape).astype(np.float32)
        stride = max(16, length // 8)
        a[:, ::stride] *= np.float32(16.0)
        b[:, ::stride] *= np.float32(8.0)
    else:
        raise ValueError(distribution)

    a_bf = quantize_bf16_array(a)
    b_bf = quantize_bf16_array(b)
    if input_kind == 'fp8_proxy':
        a_bf = (a_bf & np.uint16(0xFFF0)).astype(np.uint16)
        b_bf = (b_bf & np.uint16(0xFFF0)).astype(np.uint16)
        items_per_cycle = 4
    elif input_kind == 'bf16':
        items_per_cycle = 1
    else:
        raise ValueError(input_kind)
    return a_bf, b_bf, items_per_cycle


def evaluate_three_styles(
    product_bits: np.ndarray,
    *,
    items_per_cycle: int,
    block_products: int = 64,
) -> dict[str, np.ndarray]:
    samples, length = product_bits.shape
    if block_products % items_per_cycle:
        raise ValueError('block size must divide by items_per_cycle')

    full_bf16 = np.zeros(samples, dtype=np.uint16)
    fp32_rec = np.zeros(samples, dtype=np.float32)
    block_partial = np.zeros(samples, dtype=np.uint16)
    checkpoint = np.zeros(samples, dtype=np.float32)
    block_count = 0

    for start in range(0, length, items_per_cycle):
        chunk = product_bits[:, start:start + items_per_cycle]
        padded = np.zeros((samples, 4), dtype=np.uint16)
        padded[:, :chunk.shape[1]] = chunk
        lane_sum = tree4_vec(padded)

        full_bf16 = bf16_add_vec(full_bf16, lane_sum)
        fp32_rec = np.add(fp32_rec, bf16_array_to_float(lane_sum), dtype=np.float32)

        block_partial = bf16_add_vec(block_partial, lane_sum)
        block_count += chunk.shape[1]
        if block_count == block_products:
            checkpoint = np.add(
                checkpoint, bf16_array_to_float(block_partial), dtype=np.float32
            )
            block_partial.fill(0)
            block_count = 0
        elif block_count > block_products:
            raise AssertionError('block boundary crossed')

    if block_count:
        checkpoint = np.add(
            checkpoint, bf16_array_to_float(block_partial), dtype=np.float32
        )

    return {
        'full_bf16': bf16_array_to_float(full_bf16).astype(np.float64),
        'bf16_tree_fp32_recurrent': fp32_rec.astype(np.float64),
        'bf16_block64_fp32_checkpoint': checkpoint.astype(np.float64),
    }


def summarize(refs: np.ndarray, outs: np.ndarray) -> dict[str, float | int | None]:
    error = outs - refs
    ref_rms = float(np.sqrt(np.mean(refs * refs)))
    rmse = float(np.sqrt(np.mean(error * error)))
    threshold = max(ref_rms * 0.1, 1e-6)
    mask = np.abs(refs) > threshold
    rel = np.abs(error[mask] / refs[mask])
    return {
        'reference_rms': ref_rms,
        'rmse': rmse,
        'nrmse': rmse / max(ref_rms, 1e-30),
        'relative_samples': int(rel.size),
        'median_relative_error_filtered': float(np.median(rel)) if rel.size else None,
        'p95_relative_error_filtered': float(np.quantile(rel, 0.95)) if rel.size else None,
        'p99_relative_error_filtered': float(np.quantile(rel, 0.99)) if rel.size else None,
        'max_abs_error': float(np.max(np.abs(error))),
    }


def run_case(
    rng: np.random.Generator,
    input_kind: str,
    distribution: str,
    length: int,
    samples: int,
) -> list[dict]:
    a_bits, b_bits, items_per_cycle = make_inputs(
        rng, input_kind, distribution, samples, length
    )
    a = bf16_array_to_float(a_bits).astype(np.float64)
    b = bf16_array_to_float(b_bits).astype(np.float64)
    exact_products = a * b
    refs = np.sum(exact_products, axis=1, dtype=np.float64)
    cancellation = np.sum(np.abs(exact_products), axis=1, dtype=np.float64) / np.maximum(
        np.abs(refs), 1e-30
    )

    products_f32 = np.multiply(
        bf16_array_to_float(a_bits), bf16_array_to_float(b_bits), dtype=np.float32
    )
    product_bits = quantize_bf16_array(products_f32)
    outputs = evaluate_three_styles(
        product_bits,
        items_per_cycle=items_per_cycle,
        block_products=64,
    )

    rows = []
    for style, outs in outputs.items():
        row = {
            'input_kind': input_kind,
            'distribution': distribution,
            'dot_length': length,
            'samples': samples,
            'items_per_cycle': items_per_cycle,
            'accum_style': style,
            'block_products': 64 if style == 'bf16_block64_fp32_checkpoint' else None,
            'median_cancellation_ratio': float(np.median(cancellation)),
            'p99_cancellation_ratio': float(np.quantile(cancellation, 0.99)),
        }
        row.update(summarize(refs, outs))
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='results/accum_error_comparison.csv')
    parser.add_argument('--seed', type=int, default=20260902)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    rows = []
    sample_plan = {128: 1600, 1024: 600, 4096: 240}
    for kind in ('fp8_proxy', 'bf16'):
        for distribution in ('gaussian', 'positive', 'outlier'):
            for length, samples in sample_plan.items():
                rows.extend(run_case(rng, kind, distribution, length, samples))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f'wrote {len(rows)} rows to {output}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'model'))

from accum_v3_model import (  # noqa: E402
    AccumStyle,
    accumulate,
    product_bits_from_quantized_inputs,
    quantize_bf16_array,
)


def f32_hex(value: float) -> str:
    return f'{struct.unpack("<I", struct.pack("<f", float(np.float32(value))))[0]:08x}'


def pack_lane_items(lane_chunks: list[np.ndarray]) -> int:
    word = 0
    for lane in range(4):
        chunk = list(map(int, lane_chunks[lane]))
        chunk += [0] * (4 - len(chunk))
        for item in range(4):
            word |= (chunk[item] & 0xFFFF) << ((lane * 4 + item) * 16)
    return word


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', default=str(ROOT / 'results/vcs_vectors'))
    parser.add_argument('--seed', type=int, default=20260902)
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    cases = []
    case_id = 0
    for items_per_cycle in (1, 2, 4):
        
        k_values = [64, 128, 1024, 4096]
        k_values.append({1: 70, 2: 70, 4: 68}[items_per_cycle])
        for k in k_values:
            lane_products = []
            for lane in range(4):
                a = rng.normal(0.0, 1.0, k).astype(np.float32)
                b = rng.normal(0.0, 1.0, k).astype(np.float32)
                if lane == 3 and k >= 128:
                    a[::128] *= np.float32(16.0)
                    b[::128] *= np.float32(8.0)
                a_bits = quantize_bf16_array(a)
                b_bits = quantize_bf16_array(b)
                lane_products.append(product_bits_from_quantized_inputs(a_bits, b_bits))

            vector_path = out / f'case_{case_id:02d}_i{items_per_cycle}_k{k}.hex'
            cycles = (k + items_per_cycle - 1) // items_per_cycle
            with vector_path.open('w', encoding='ascii') as f:
                for cycle in range(cycles):
                    chunks = []
                    for lane in range(4):
                        start = cycle * items_per_cycle
                        chunks.append(lane_products[lane][start:start + items_per_cycle])
                    f.write(f'{pack_lane_items(chunks):064x}\n')

            full = []
            fp32 = []
            block = []
            for lane in range(4):
                products = list(map(int, lane_products[lane]))
                full_value = accumulate(
                    AccumStyle.FULL_BF16,
                    products,
                    items_per_cycle=items_per_cycle,
                )
                fp32_value = accumulate(
                    AccumStyle.BF16_TREE_FP32_RECURRENT,
                    products,
                    items_per_cycle=items_per_cycle,
                )
                block_value = accumulate(
                    AccumStyle.BF16_BLOCK64_FP32_CHECKPOINT,
                    products,
                    items_per_cycle=items_per_cycle,
                    block_products=64,
                )
                full.append(f'{(struct.unpack("<I", struct.pack("<f", float(full_value)))[0] >> 16):04x}')
                fp32.append(f32_hex(fp32_value))
                block.append(f32_hex(block_value))

            cases.append({
                'case_id': case_id,
                'items_per_cycle': items_per_cycle,
                'products_per_lane': k,
                'cycles': cycles,
                'needs_flush': int(k % 64 != 0),
                'vector_file': vector_path.name,
                **{f'full_bf16_lane{lane}': full[lane] for lane in range(4)},
                **{f'fp32_recurrent_lane{lane}': fp32[lane] for lane in range(4)},
                **{f'block64_checkpoint_lane{lane}': block[lane] for lane in range(4)},
            })
            case_id += 1

    manifest = out / 'manifest.csv'
    with manifest.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(cases[0]))
        writer.writeheader()
        writer.writerows(cases)
    print(f'wrote {len(cases)} VCS cases to {out}')


if __name__ == '__main__':
    main()

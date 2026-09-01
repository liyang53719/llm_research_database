#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from model.fusion_mul16_model import FusionMode, FusionMul16Model


def f32_bits(value: np.float32) -> int:
    return struct.unpack("<I", struct.pack("<f", float(value)))[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/rtl_vectors.jsonl")
    parser.add_argument("--per-mode", type=int, default=256)
    parser.add_argument("--seed", type=int, default=53719)
    args = parser.parse_args()
    root = ROOT
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    model = FusionMul16Model()

    rows = []
    for mode in FusionMode:
        count = {
            FusionMode.I4_I4: 16,
            FusionMode.I4_I8: 8,
            FusionMode.I8_I8: 4,
            FusionMode.I16_I16: 1,
            FusionMode.FP8_FP8: 16,
            FusionMode.BF16_BF16: 4,
            FusionMode.I4_FP8: 16,
            FusionMode.I8_FP8: 8,
            FusionMode.I4_BF16: 8,
            FusionMode.I8_BF16: 4,
        }[mode]
        for vector_id in range(args.per_mode):
            if mode == FusionMode.I4_I4:
                lhs = [rng.randrange(16) for _ in range(count)]
                rhs = [rng.randrange(16) for _ in range(count)]
            elif mode == FusionMode.I4_I8:
                lhs = [rng.randrange(16) for _ in range(count)]
                rhs = [rng.randrange(256) for _ in range(count)]
            elif mode == FusionMode.I8_I8:
                lhs = [rng.randrange(256) for _ in range(count)]
                rhs = [rng.randrange(256) for _ in range(count)]
            elif mode == FusionMode.I16_I16:
                lhs = [rng.randrange(65536)]
                rhs = [rng.randrange(65536)]
            elif mode == FusionMode.FP8_FP8:
                lhs = [rng.randrange(256) for _ in range(count)]
                rhs = [rng.randrange(256) for _ in range(count)]
            elif mode == FusionMode.BF16_BF16:
                lhs = [rng.randrange(65536) for _ in range(count)]
                rhs = [rng.randrange(65536) for _ in range(count)]
            elif mode == FusionMode.I4_FP8:
                lhs = [rng.randrange(16) for _ in range(count)]
                rhs = [rng.randrange(256) for _ in range(count)]
            elif mode == FusionMode.I8_FP8:
                lhs = [rng.randrange(256) for _ in range(count)]
                rhs = [rng.randrange(256) for _ in range(count)]
            elif mode == FusionMode.I4_BF16:
                lhs = [rng.randrange(16) for _ in range(count)]
                rhs = [rng.randrange(65536) for _ in range(count)]
            else:
                lhs = [rng.randrange(256) for _ in range(count)]
                rhs = [rng.randrange(65536) for _ in range(count)]

            result = model.run(mode, lhs, rhs)
            if mode.value <= FusionMode.I16_I16.value:
                expected = {"int_products": list(result.products)}
            else:
                expected = {"fp32_product_bits": [f32_bits(x) for x in result.products]}
            rows.append({
                "mode": mode.name,
                "mode_value": int(mode),
                "vector_id": vector_id,
                "lhs": lhs + [0] * (16 - len(lhs)),
                "rhs": rhs + [0] * (16 - len(rhs)),
                "product_count": result.products_per_cycle,
                "brick_count": result.brick_count,
                **expected,
            })

    with output.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, separators=(",", ":")) + "\n")
    print(f"Wrote {len(rows)} vectors to {output}")


if __name__ == "__main__":
    main()

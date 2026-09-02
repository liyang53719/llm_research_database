#!/usr/bin/env python3
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from model.fusion_mul16_v2_model import FusionMul16V2Model, PRODUCTS_PER_CYCLE, V2Mode, twos


def operand(rng: random.Random, mode: V2Mode, lhs: bool) -> int:
    if mode == V2Mode.I4_I8:
        return rng.randrange(16 if lhs else 256)
    if mode == V2Mode.I8_I8:
        return rng.randrange(256)
    if mode == V2Mode.FP8_FP8:
        return rng.randrange(256)
    if mode == V2Mode.BF16_BF16:
        return rng.randrange(65536)
    if mode == V2Mode.I4_FP8:
        return rng.randrange(16 if lhs else 256)
    if mode == V2Mode.I4_BF16:
        return rng.randrange(16 if lhs else 65536)
    if mode == V2Mode.I8_BF16:
        return rng.randrange(256 if lhs else 65536)
    raise ValueError(mode)


def pack(values: list[int], width: int) -> int:
    result = 0
    for index, value in enumerate(values):
        result |= (value & ((1 << width) - 1)) << (index * width)
    return result


def widths(mode: V2Mode) -> tuple[int, int]:
    return {
        V2Mode.I4_I8: (4, 8),
        V2Mode.I8_I8: (8, 8),
        V2Mode.FP8_FP8: (8, 8),
        V2Mode.BF16_BF16: (16, 16),
        V2Mode.I4_FP8: (4, 8),
        V2Mode.I4_BF16: (4, 16),
        V2Mode.I8_BF16: (8, 16),
    }[mode]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', default='results/vcs_vectors')
    parser.add_argument('--per-mode', type=int, default=512)
    args = parser.parse_args()
    out = ROOT / args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(20260902)
    model = FusionMul16V2Model()

    for mode in V2Mode:
        n = PRODUCTS_PER_CYCLE[mode]
        lhs_width, rhs_width = widths(mode)
        path = out / f'{int(mode)}_{mode.name}.vec'
        with path.open('w', encoding='ascii') as stream:
            for _ in range(args.per_mode):
                lhs = [operand(rng, mode, True) for _ in range(n)]
                rhs = [operand(rng, mode, False) for _ in range(n)]
                result = model.run_cycle(mode, lhs, rhs)
                lhs_packed = pack(lhs, lhs_width)
                rhs_packed = pack(rhs, rhs_width)
                ints = [twos(value, 18) for value in result.int_lane_sums]
                fps = [value for lane in result.bf16_lane_items for value in lane]
                tokens = [f'{lhs_packed:032x}', f'{rhs_packed:032x}']
                tokens += [f'{value:05x}' for value in ints]
                tokens += [f'{value:04x}' for value in fps]
                stream.write(' '.join(tokens) + '\n')
        print(path)


if __name__ == '__main__':
    main()

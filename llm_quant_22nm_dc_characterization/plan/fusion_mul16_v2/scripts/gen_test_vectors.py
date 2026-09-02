#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from model.fusion_mul16_v2_model import FusionMul16V2Model, PRODUCTS_PER_CYCLE, V2Mode


def random_operand(rng: random.Random, mode: V2Mode, lhs: bool) -> int:
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='results/rtl_vectors_v2.jsonl')
    parser.add_argument('--per-mode', type=int, default=512)
    args = parser.parse_args()
    rng = random.Random(20260902)
    model = FusionMul16V2Model()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    count=0
    with path.open('w',encoding='utf-8') as f:
        for mode in V2Mode:
            n=PRODUCTS_PER_CYCLE[mode]
            for _ in range(args.per_mode):
                lhs=[random_operand(rng,mode,True) for _ in range(n)]
                rhs=[random_operand(rng,mode,False) for _ in range(n)]
                result=model.run_cycle(mode,lhs,rhs)
                row={'mode':mode.name,'lhs':lhs,'rhs':rhs,
                     'int_lane_sums':list(result.int_lane_sums),
                     'bf16_lane_items':[list(x) for x in result.bf16_lane_items],
                     'brick_products':list(result.brick_products)}
                f.write(json.dumps(row,separators=(',',':'))+'\n'); count+=1
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    (path.with_suffix(path.suffix+'.sha256')).write_text(f'{digest}  {path.name}\n')
    print(f'Wrote {count} vectors, SHA256={digest}')

if __name__=='__main__': main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import itertools
import random
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from model.fusion_mul16_model import FusionMode, FusionMul16Model, PRODUCTS_PER_CYCLE


PAIR_COUNTS = {
    FusionMode.I4_I4: 256,
    FusionMode.I4_I8: 4096,
    FusionMode.I8_I8: 65536,
    FusionMode.I16_I16: 100000,
    FusionMode.FP8_FP8: 65536,
    FusionMode.I4_FP8: 4096,
    FusionMode.I8_FP8: 65536,
    FusionMode.BF16_BF16: 100000,
    FusionMode.I4_BF16: 50000,
    FusionMode.I8_BF16: 50000,
}


def f32_bits(value: np.float32) -> int:
    return struct.unpack("<I", struct.pack("<f", float(value)))[0]


def exhaustive(stop_a: int, stop_b: int):
    return itertools.product(range(stop_a), range(stop_b))


def stratified(total: int, a_values: list[int], b_values: list[int],
               a_limit: int, b_limit: int, rng: random.Random):
    emitted = 0
    for pair in itertools.product(a_values, b_values):
        if emitted >= total:
            return
        yield pair
        emitted += 1
    while emitted < total:
        yield rng.randrange(a_limit), rng.randrange(b_limit)
        emitted += 1


def pair_source(mode: FusionMode, rng: random.Random):
    if mode == FusionMode.I4_I4:
        return exhaustive(16, 16)
    if mode == FusionMode.I4_I8:
        return exhaustive(16, 256)
    if mode == FusionMode.I8_I8:
        return exhaustive(256, 256)
    if mode == FusionMode.FP8_FP8:
        return exhaustive(256, 256)
    if mode == FusionMode.I4_FP8:
        return exhaustive(16, 256)
    if mode == FusionMode.I8_FP8:
        return exhaustive(256, 256)
    if mode == FusionMode.I16_I16:
        edge = [0x0000, 0x0001, 0x0002, 0x7fff, 0x8000, 0x8001, 0xfffe, 0xffff]
        return stratified(PAIR_COUNTS[mode], edge, edge, 65536, 65536, rng)
    bf16_special = [
        0x0000, 0x8000, 0x0001, 0x007f, 0x0080, 0x3f80, 0xbf80,
        0x7f7f, 0xff7f, 0x7f80, 0xff80, 0x7fc0, 0x7fff, 0xffc1,
    ]
    if mode == FusionMode.BF16_BF16:
        return stratified(PAIR_COUNTS[mode], bf16_special, bf16_special,
                          65536, 65536, rng)
    int_values = list(range(16 if mode == FusionMode.I4_BF16 else 256))
    return stratified(PAIR_COUNTS[mode], int_values, bf16_special,
                      len(int_values), 65536, rng)


def write_vectors(mode: FusionMode, path: Path, rng: random.Random) -> int:
    model = FusionMul16Model()
    ppc = PRODUCTS_PER_CYCLE[mode]
    source = iter(pair_source(mode, rng))
    pairs_left = PAIR_COUNTS[mode]
    vectors = 0
    with path.open("w", encoding="ascii") as handle:
        while pairs_left:
            batch = [next(source) for _ in range(ppc)]
            lhs = [pair[0] for pair in batch]
            rhs = [pair[1] for pair in batch]
            result = model.run(mode, lhs, rhs)
            if mode <= FusionMode.I16_I16:
                expected = [int(value) & ((1 << 33) - 1) for value in result.products]
            else:
                expected = [f32_bits(value) for value in result.products]
            lhs += [0] * (16 - ppc)
            rhs += [0] * (16 - ppc)
            expected += [0] * (16 - ppc)
            fields = [str(int(mode)), f"{(1 << ppc) - 1:04x}", str(ppc)]
            fields += [f"{value & 0xffff:04x}" for value in lhs]
            fields += [f"{value & 0xffff:04x}" for value in rhs]
            fields += [f"{value:09x}" for value in expected]
            handle.write(" ".join(fields) + "\n")
            vectors += 1
            pairs_left -= ppc
    return vectors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=53719)
    parser.add_argument("--cpus", default="8-23")
    args = parser.parse_args()
    if args.cpus != "8-23":
        raise SystemExit("This checkout requires --cpus 8-23")

    build = ROOT / "build_sim" / "product_crosscheck"
    build.mkdir(parents=True, exist_ok=True)
    sim = build / "fusion_mul16_product_core.simv"
    compile_log = build / "compile.log"
    vcs = shutil.which("vcs")
    if not vcs:
        raise SystemExit("vcs was not found on PATH")
    compile_cmd = [
        "taskset", "-c", args.cpus,
        vcs,
        "-full64", "-sverilog", "-top", "fusion_mul16_product_core_tb",
        "+define+FUSION_USE_DW",
        str(ROOT / "tests/dw_mult_uns_sim_stub.sv"),
        "-o", str(sim),
        str(ROOT / "rtl/fusion_mul16_pkg.sv"),
        str(ROOT / "rtl/mul4x4_brick.sv"),
        str(ROOT / "rtl/fusion_mul16_product_core.sv"),
        str(ROOT / "tb/fusion_mul16_product_core_tb.sv"),
    ]
    proc = subprocess.run(compile_cmd, cwd=build, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    compile_log.write_text(proc.stdout, encoding="utf-8")
    if proc.returncode:
        raise SystemExit(f"VCS compile failed; see {compile_log}")

    rows = []
    rng = random.Random(args.seed)
    result_re = re.compile(r"RESULT vectors=(\d+) checks=(\d+) fails=(\d+)")
    for mode in FusionMode:
        vector_path = build / f"{mode.name}.vectors"
        vectors = write_vectors(mode, vector_path, rng)
        run = subprocess.run(
            ["taskset", "-c", args.cpus, str(sim), "-no_save", f"+vectors={vector_path}"],
            cwd=build, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        (build / f"{mode.name}.log").write_text(run.stdout, encoding="utf-8")
        match = result_re.search(run.stdout)
        if not match:
            raise SystemExit(f"No result line for {mode.name}; see simulation log")
        got_vectors, checks, failures = map(int, match.groups())
        rows.append({
            "mode": mode.name,
            "pair_count": PAIR_COUNTS[mode],
            "vector_count": got_vectors,
            "rtl_checks": checks,
            "mismatches": failures,
            "simulator": "VCS W-2024.09",
            "seed": args.seed,
        })
        print(f"{mode.name}: pairs={PAIR_COUNTS[mode]} vectors={vectors} "
              f"checks={checks} mismatches={failures}", flush=True)
        if run.returncode or got_vectors != vectors or failures:
            raise SystemExit(f"RTL crosscheck failed for {mode.name}")

    output = ROOT / "results/local_dc/numeric_rtl_crosscheck.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()

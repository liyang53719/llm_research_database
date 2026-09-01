#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--build-dir", default="build_dc")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    build = root / args.build_dir
    build.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((root / "config/characterization.json").read_text(encoding="utf-8"))
    with (root / "config/dc_experiments.csv").open(encoding="utf-8-sig") as f:
        groups = list(csv.DictReader(f))

    rtl_order = [
        "fusion_mul16_pkg.sv",
        "mul4x4_brick.sv",
        "fusion_mul16_product_core.sv",
        "fusion_mul16_int_accum.sv",
        "fusion_mul16_fp32_accum_dw.sv",
        "fusion_mul16_cluster_dw.sv",
        "fusion_mul16_cluster_dw_pipe.sv",
        "fusion_mul16_proof_top.sv",
        "mul4x4_array16_proof.sv",
        "fusion_mul16_int_accum_proof_top.sv",
        "fusion_mul16_fp_accum_proof_top.sv",
        "fusion_mul16_int_only_pipe_top.sv",
        "fusion_mul16_fp8_only_pipe_top.sv",
        "fusion_mul16_bf16_only_pipe_top.sv",
        "fusion_mul16_separate_reference_dw.sv",
        "fusion_mul16_separate_reference_pipe_dw.sv",
        "fusion_mul16_dual_cluster_dw.sv",
        "fusion_mul16_dual_cluster_pipe_dw.sv"
    ]
    rtl_files = [str((root / "rtl" / name).resolve()) for name in rtl_order]
    missing = [path for path in rtl_files if not Path(path).exists()]
    if missing:
        raise SystemExit("Missing RTL:\n" + "\n".join(missing))
    digest = hashlib.sha256()
    for path in rtl_files:
        rel = Path(path).relative_to(root).as_posix()
        digest.update(rel.encode("utf-8") + b"\0")
        digest.update(Path(path).read_bytes())
    rtl_bundle_sha256 = digest.hexdigest()

    runs: list[dict] = []
    for group in groups:
        for period in cfg["clock_periods_ns"]:
            tag = str(period).replace(".", "p")
            run_id = f'{group["group_id"]}__T{tag}ns'
            run_dir = build / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "rtl_files.list").write_text("\n".join(rtl_files) + "\n", encoding="utf-8")
            meta = {
                **group,
                "run_id": run_id,
                "run_dir": str(run_dir.resolve()),
                "clock_period_ns": period,
                "clock_mhz": 1000.0 / period,
                "define_fusion_use_dw": 1,
                "rtl_bundle_sha256": rtl_bundle_sha256,
            }
            (run_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
            runs.append(meta)

    with (build / "runs.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(runs[0]))
        writer.writeheader()
        writer.writerows(runs)
    print(f"Generated {len(groups)} groups / {len(runs)} runs in {build}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def parse_kv(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir")
    parser.add_argument("--output")
    args = parser.parse_args()
    run_dir = Path(args.run_dir)
    root = run_dir.resolve().parents[1]
    summary = parse_kv(run_dir / "summary.kv")
    source_operator_files = []
    source_offenders = []
    dw_fp_mult_mentions = []
    for path in sorted((root / "rtl").glob("*.sv")):
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        text = re.sub(r"//.*", "", text)
        if re.search(r"\s\*\s", text):
            source_operator_files.append(path.name)
            if path.name != "mul4x4_brick.sv":
                source_offenders.append(path.name)
        if "DW_fp_mult" in text:
            dw_fp_mult_mentions.append(path.name)
    report_text = ""
    for name in ["report_resources_pre.rpt", "report_resources_post.rpt",
                 "report_reference_pre.rpt", "report_reference_post.rpt"]:
        path = run_dir / "reports" / name
        if path.exists():
            report_text += path.read_text(encoding="utf-8", errors="ignore")
    checks = {
        "brick_instance_count_precompile": int(float(summary.get("brick_instance_count_precompile", -1))),
        "dw_mult_instance_count_precompile": int(float(summary.get("dw_mult_instance_count_precompile", -1))),
        "blackbox_count": int(float(summary.get("blackbox_count", -1))),
        "mapped_cell_area_um2": float(summary.get("mapped_cell_area_um2", 0)),
        "source_multiply_operator_files": source_operator_files,
        "source_additional_multiplier_files": source_offenders,
        "source_dw_fp_mult_files": dw_fp_mult_mentions,
        "report_dw_fp_mult_mentions": report_text.count("DW_fp_mult"),
    }
    checks["additional_multiplier_operations"] = (
        len(source_offenders) + len(dw_fp_mult_mentions)
        + checks["report_dw_fp_mult_mentions"]
    )
    checks["pass"] = (
        checks["brick_instance_count_precompile"] == 16
        and checks["dw_mult_instance_count_precompile"] == 16
        and checks["blackbox_count"] == 0
        and checks["mapped_cell_area_um2"] > 0
        and checks["source_multiply_operator_files"] == ["mul4x4_brick.sv"]
        and checks["additional_multiplier_operations"] == 0
    )
    output = json.dumps(checks, indent=2)
    print(output)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    if not checks["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

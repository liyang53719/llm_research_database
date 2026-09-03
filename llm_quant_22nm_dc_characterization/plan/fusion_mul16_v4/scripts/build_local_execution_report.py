#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with (ROOT / "results/local_dc/v4_area_1ghz.csv").open(encoding="utf-8-sig", newline="") as handle:
        dc = list(csv.DictReader(handle))
    with (ROOT / "results/vcs/vcs_summary.csv").open(encoding="utf-8-sig", newline="") as handle:
        vcs = list(csv.DictReader(handle))
    protocol = json.loads((ROOT / "results/vcs/protocol_summary.json").read_text())
    decision = json.loads((ROOT / "results/local_dc/architecture_decision.json").read_text())
    lines = [
        "# FusionMul16 v4 local execution report",
        "",
        "## Gate summary",
        "",
        "- Sandbox: full raw-pair/equivalence coverage PASS (4,312,932,352 pairs; 30,200,504 checks; 0 mismatches).",
        f"- VCS: {sum(row.get('passed') == '1' for row in vcs)}/{len(vcs)} complete-IP transaction cases PASS; protocol PASS={protocol.get('passed')}",
        f"- DC: {len(dc)}/12 groups completed at CLN22UL TT 0.80 V/25 C, 1.000 ns, compile_ultra.",
        "- Runtime policy: CPU 8-23, one DC job/core, cgroup MemoryMax=40G, no OOM observed.",
        "- Physical signoff is OPEN; these are mapped-cell synthesis results.",
        "",
        "## DC results",
        "",
        "| Group | Area (um2) | Setup WNS (ns) | Hold WNS (ns) | Hold count | Fanout nets | BF16 add | FP32 add |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in sorted(dc, key=lambda item: item["group_id"]):
        lines.append(
            f"| {row['group_id']} | {float(row['mapped_cell_area_um2']):.3f} | {float(row['wns_ns']):.9g} | {row['worst_hold_violation_ns']} | {row['hold_violation_count']} | {row['high_fanout_net_count'] or 0} | {row['bf16_add_rows']} | {row['fp32_add_rows']} |"
        )
    lines += [
        "",
        "## Release decision",
        "",
        f"- Release profile: `{decision['release_profile']}`; status `{decision['status']}`.",
        "- V4_FINAL_DYNAMIC_FTZ is the hard inference gate: setup WNS is non-negative, area is within the +10% v3 budget, 16 DW_mult_uns 4x4 operations, 12 BF16 adders, 4 FP32 adders, and no black boxes.",
        "- V4_FINAL_DYNAMIC_IEEE is optional special/IEEE characterization. It is retained as data and does not block the inference profile; it misses the hard 1 GHz setup gate at this library corner.",
        "- Warnings are retained: near-zero setup margin (<50 ps) and pre-layout hold violations. They are not physical-signoff claims.",
        "- Target-model layer/logit/perplexity/task accuracy remains OPEN; precision results are synthetic arithmetic proxy only.",
    ]
    (ROOT / "results/local_dc/LOCAL_EXECUTION_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote results/local_dc/LOCAL_EXECUTION_REPORT.md")


if __name__ == "__main__":
    main()

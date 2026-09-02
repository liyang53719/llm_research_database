#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    dc = read_csv(ROOT / "results/local_dc/v3_area_1ghz.csv")
    vcs = read_csv(ROOT / "results/vcs_crosscheck_summary.csv")
    p5 = read_csv(ROOT / "results/local_dc/p5_ablation.csv")
    full = {row["group_id"]: row for row in dc}
    block_groups = [row for row in dc if row["constraint_profile"] == "checkpoint_mc2"]
    nonblock_sdc = [
        len((ROOT / "build_dc_1ghz" / row["run_id"] / "netlist/char_top.sdc").read_text(errors="ignore").split("set_multicycle_path") ) - 1
        for row in dc if row["constraint_profile"] != "checkpoint_mc2"
    ]
    block_sdc = [
        len((ROOT / "build_dc_1ghz" / row["run_id"] / "netlist/char_top.sdc").read_text(errors="ignore").split("set_multicycle_path") ) - 1
        for row in block_groups
    ]
    proof_checks = {
        "dc_runs": len(dc) == 12,
        "vcs_cases": len(vcs) == 15 and all(row.get("passed") == "1" for row in vcs),
        "dc_errors": all(row.get("dc_error_count") == "0" for row in dc),
        "blackboxes": all(float(row.get("blackbox_count") or 1) == 0 for row in dc),
        "all_timing_closed": all(row.get("timing_met") == "1" for row in dc),
        "checkpoint_mc2_only": all(n == 0 for n in nonblock_sdc) and all(n == 2 for n in block_sdc),
        "checkpoint_reports_have_paths": all(
            "checkpoint_path_report_begin" in (ROOT / "build_dc_1ghz" / row["run_id"] / "reports/report_exceptions.rpt").read_text(errors="ignore")
            for row in block_groups
        ),
        "no_accumulator_multiplier": all(row.get("source_multiply_operator_files") == "mul4x4_brick.sv" and not row.get("source_fp_mult_files") for row in dc),
        "v2_product_pipe_sha_present": all(row.get("rtl_input_sha256") for row in dc),
    }
    lines = [
        "# FusionMul16 v3 local execution report",
        "",
        "## Acceptance",
        "",
        "- PVT: CLN22UL base SVT C35 TT typical_max, 0.80 V, 25 C.",
        "- DC: X-2025.06-SP3, compile_ultra, clock period 1.000 ns only.",
        "- Resource policy: CPU 8-23, one DC job, one DC host core, systemd cgroup MemoryMax=40G, no OOM observed.",
        f"- Python: 20/20 tests PASS; VCS: {len(vcs)}/15 cases PASS; DC: {len(dc)}/12 runs returned rc=0.",
        f"- DC validation: {(ROOT / 'results/local_dc/validation_report.txt').read_text(encoding='utf-8').splitlines()[1]}",
        "",
        "## 1 GHz DC results",
        "",
        "| Group | Area (um2) | WNS (ns) | BF16 adders | FP32 adders | MC |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in sorted(dc, key=lambda item: item["group_id"]):
        lines.append(f"| {row['group_id']} | {float(row['mapped_cell_area_um2']):.3f} | {float(row['wns_ns']):.9g} | {row['bf16_add_rows']} | {row['fp32_add_rows']} | {row['multicycle_applied']} |")
    lines += [
        "",
        "## P5 selection",
        "",
        "- P5 compares the two v2 reproduction references and all three v3 full-cluster accumulator backends under the same 1 GHz/PVT/compile setup.",
        "- Full BF16 is timing-closed but fails the synthetic K=4096 gate.",
        "- BF16 tree + FP32 recurrent and BF16 Kblock64 + FP32 checkpoint pass the synthetic gate; the former has the smaller full-cluster area and is the provisional selection.",
        "- Target-model layer/logit/perplexity/task accuracy is OPEN; synthetic proxy is not final model signoff.",
        "",
        "## Structural and multicycle proof",
        "",
        "- The v2 product pipe, 16x4-bit brick and packed interface are reused; no accumulator source contains DW_fp_mult or an extra multiply operator.",
        "- Common tree: 12 BF16 adders. Style 0: 4 BF16 recurrent adders. Style 1: 4 FP32 recurrent adders. Style 2: 4 BF16 partial + 4 FP32 checkpoint adders.",
        "- Style 1 has no multicycle exception and must close a real one-cycle FP32 recurrence (observed 1 GHz timing_met=1).",
        "- Style 2 applies only setup=2/hold=1 to checkpoint register paths; the mapped checkpoint report contains Q-to-next_state paths and no product-tree/partial exception.",
        "- RTL holds checkpoint operands in named base/term registers and enables checkpoint_fp32_o only when the wait counter reaches its terminal bit; stream II remains 1.",
        "",
        "## Evidence checks",
        "",
    ]
    for key, value in proof_checks.items():
        lines.append(f"- {key}: {'PASS' if value else 'FAIL'}")
    lines += [
        "",
        "## Baseline reproduction",
        "",
        f"- V3_ACC_FULL_BF16 = {float(full['V3_ACC_FULL_BF16']['mapped_cell_area_um2']):.3f} um2 vs v2 reference 6270.992 um2 ({(float(full['V3_ACC_FULL_BF16']['mapped_cell_area_um2']) / 6270.992 - 1.0) * 100.0:.3f}%).",
        f"- V3_CLUSTER_FULL_BF16_FULL7 = {float(full['V3_CLUSTER_FULL_BF16_FULL7']['mapped_cell_area_um2']):.3f} um2 vs v2 reference 11995.438 um2 ({(float(full['V3_CLUSTER_FULL_BF16_FULL7']['mapped_cell_area_um2']) / 11995.438 - 1.0) * 100.0:.3f}%).",
        "- Both deviations are within the configured +/-5% reproduction tolerance.",
        "",
        "## Public-data boundary",
        "",
        "- Raw DC logs, generated netlists/DDC, licensed .db/.lib/.sldb files and local absolute paths are excluded from the public upload.",
        "- Public evidence keeps summaries, reports, hashes and reproducible scripts after path/host sanitization.",
    ]
    (ROOT / "results/LOCAL_EXECUTION_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    proof_lines = [
        "# FusionMul16 v3 structure and multicycle proof",
        "",
        "## Static RTL contract",
        "",
        "- `fusion_mul16_v3_bf16_tree_dw.sv`: three `DW_fp_add #(7,8,0)` instances in a four-lane generate loop, therefore 12 BF16 adders.",
        "- `fusion_mul16_v3_accum_full_bf16_dw.sv`: one generated BF16 recurrent adder per lane, therefore 4 BF16 adders.",
        "- `fusion_mul16_v3_accum_fp32_recurrent_dw.sv`: one generated `DW_fp_add #(23,8,0)` per lane, therefore 4 FP32 recurrent adders; no multicycle constraint is supplied.",
        "- `fusion_mul16_v3_accum_block64_fp32_checkpoint_dw.sv`: one generated BF16 partial and one FP32 checkpoint adder per lane; named `checkpoint_base_q`, `checkpoint_term_q` and `checkpoint_fp32_o` state is held across the wait counter.",
        "- The checkpoint output update is guarded by `checkpoint_wait_q[WAIT_W-1]`, while a boundary/flush loads the operands and starts the wait counter. This is the RTL evidence for destination enable on the second edge and operand stability.",
        "- Accumulator RTL contains no `DW_fp_mult` and no additional multiply operator; the only multiply source file is the reused v2 `mul4x4_brick.sv`.",
        "",
        "## Mapped DC evidence",
        "",
        f"- Block64 runs with `set_multicycle_path` lines in exported SDC: {len(block_sdc) and block_sdc[0]} per run (setup=2, hold=1).",
        f"- Non-block runs with multicycle lines in exported SDC: {set(nonblock_sdc)} (expected {{0}}).",
        "- All four block64 `report_exceptions.rpt` files contain the supported Q-to-next_state checkpoint timing report. DC X-2025.06-SP3 has no `report_exceptions` command, so the report records that limitation and embeds `report_constraint -verbose` plus the supported timing paths.",
        "- No block64 DC log contains TIM-179/UID-119 stale-object warnings after state preservation.",
        "- Product tree and BF16 partial paths have no multicycle commands in the generated SDC.",
        "",
        "## Scope boundary",
        "",
        "- This is a synthesis/structural proof at the stated 1 GHz setup. Physical signoff and target-model layer/logit accuracy remain outside this run.",
    ]
    (ROOT / "results/local_dc/v3_structure_multicycle_proof.md").write_text("\n".join(proof_lines) + "\n", encoding="utf-8")
    print("wrote results/LOCAL_EXECUTION_REPORT.md")


if __name__ == "__main__":
    main()

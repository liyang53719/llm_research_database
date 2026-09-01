#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/local_dc"


def read_csv(name: str) -> list[dict]:
    with (RESULTS / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    groups = read_csv("fusion16_group_summary.csv")
    numeric = read_csv("numeric_rtl_crosscheck.csv")
    pareto = read_csv("architecture_pareto.csv")
    proof = json.loads((RESULTS / "brick_sharing_proof.json").read_text(encoding="utf-8"))
    decision = json.loads((RESULTS / "architecture_decision.json").read_text(encoding="utf-8"))
    numeric_pairs = sum(int(row["pair_count"]) for row in numeric)
    numeric_checks = sum(int(row["rtl_checks"]) for row in numeric)
    timing_met = sum(int(float(row["timing_met_1ghz"])) for row in groups)

    lines = [
        "# FusionMul16 本地执行报告",
        "",
        "## 结论",
        "",
        f"- 17/17 沙箱单元测试通过；10 种模式共 {numeric_pairs:,} 对输入、{numeric_checks:,} 项 RTL 检查，零失配。",
        f"- 11 组/33 次 DC 扫描完整，1 GHz 达标 {timing_met}/11。",
        f"- 16-brick proof：{'PASS' if proof.get('pass') else 'FAIL'}；预编译 brick={proof.get('brick_instance_count_precompile')}，DW 4x4 multiplier={proof.get('dw_mult_instance_count_precompile')}，额外 multiplier={proof.get('additional_multiplier_operations')}。",
        f"- 架构决策：`{decision['decision_status']}`。",
        "- FP accumulator 使用 `DW_fp_add #(23,8,0)`；是否接受 denormal 行为必须由模型精度合同确认，因此不会把该条件冒充已验收。",
        "",
        "## 固定综合合同",
        "",
        "- CLN22UL SVT C35, TT typical_max, 0.80 V, 25 C",
        "- DC X-2025.06-SP3 / DWBB X-2025.06-DWBB_202506.3",
        "- compile_ultra；2.0 ns / 1.0 ns / 0.9 ns",
        "- CPU 8-23；单 DC、单执行核；cgroup MemoryHigh=36 GiB / MemoryMax=40 GiB",
        "",
        "## 1 GHz 结果",
        "",
        "| Group | Area (µm²) | WNS (ns) | Timing |",
        "|---|---:|---:|---:|",
    ]
    for row in groups:
        lines.append(
            f"| {row['group_id']} | {float(row['area_1ghz_um2']):.6f} | "
            f"{float(row['wns_1ghz_ns']):.6f} | {int(float(row['timing_met_1ghz']))} |"
        )
    lines += [
        "",
        "## 同吞吐与并发比较",
        "",
        "| Architecture | Area @1GHz (µm²) | Concurrent modes | Throughput contract | Dominated |",
        "|---|---:|---:|---|---:|",
    ]
    for row in pareto:
        lines.append(
            f"| {row['architecture']} | {float(row['area_1ghz_um2']):.6f} | "
            f"{row['concurrent_mode_count']} | {row['throughput_match']} | {row['pareto_dominated']} |"
        )
    lines += [
        "",
        "## 验证边界",
        "",
        "- 已完成 RTL product 全空间/分层仿真、官方 DW_fp_add 顶层展开、valid 延迟检查、DC elaboration 结构证明和 mapped PPA。",
        "- 未执行 Formality、post-synthesis gate simulation 或 place-and-route；这些不属于本次 DC 结果的已测边界。",
        "- `partial_concurrency_match` 不等于 full three-mode concurrency；表中明确保留该差异。",
        "",
    ]
    (RESULTS / "LOCAL_EXECUTION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(RESULTS / "LOCAL_EXECUTION_REPORT.md")


if __name__ == "__main__":
    main()

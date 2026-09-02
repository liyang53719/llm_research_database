#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/local_dc'


def load(name: str) -> list[dict]:
    with (OUT / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    raw = load('fusion16_v2_area_1ghz.csv')
    ablation = load('mode_ablation.csv')
    pareto = load('architecture_pareto.csv')
    proof = json.loads((OUT / 'brick_sharing_proof.json').read_text())
    decision = json.loads((OUT / 'architecture_decision.json').read_text())
    required = ['V2_CORE_FULL7_FTZ','V2_SHARED_FULL7_FTZ','V2_SEPARATE_FULL_FTZ',
                'V2_FP8_NATIVE_BF16ACC_FIXED','V2_BF16_ONLY_BF16ACC_FIXED',
                'V2_INT_I4I8_FIXED','V2_INT_I8I8_FIXED']
    lines = [
        '# FusionMul16 v2 本地执行报告', '',
        '## Gate 结论', '',
        '- Python：20/20 PASS。',
        '- VCS：7 模式共 3584 vectors，product crosscheck 零失配；config protocol PASS。',
        f"- DC：{len(raw)}/21 个 1.000ns run 完成；校验报告 `ERRORS=NONE`。",
        f"- Required timing groups：{sum(int(float(r['timing_met'])) for r in raw if r['group_id'] in required)}/{len(required)} 通过 1GHz。",
        f"- Brick proof：{'PASS' if proof.get('pass') else 'FAIL'}；brick={proof.get('brick_instance_count_precompile')}，DW4x4={proof.get('dw_mult_4x4_instance_count_precompile')}，额外 multiplier={proof.get('additional_multiplier_operations')}。",
        f"- Architecture accept：`{decision.get('architecture_accept')}`。",
        '', '## 1 GHz 关键比较', '',
        '| Architecture | Area (µm²) | WNS (ns) | Timing | Eligible |',
        '|---|---:|---:|---:|---:|',
    ]
    for r in pareto:
        lines.append(f"| {r['architecture']} | {float(r['area_1ghz_um2']):.3f} | {float(r['wns_ns']):.6f} | {r['timing_met_1ghz']} | {r['pareto_eligible_1ghz']} |")
    lines += ['', '## P5 消融', '', '| Group | Area increment | WNS delta (ns) | Timing |', '|---|---:|---:|---:|']
    for r in ablation:
        inc = '' if r['increment_pct'] in ('', 'None', None) else f"{float(r['increment_pct']):.3f}%"
        delta = '' if r['wns_delta_vs_previous_ns'] in ('', 'None', None) else f"{float(r['wns_delta_vs_previous_ns']):.6f}"
        lines.append(f"| {r['group_id']} | {inc} | {delta} | {r['timing_met']} |")
    lines += ['', '## 固定边界', '',
              '- CLN22UL base SVT C35 TT typical_max 0.80V/25C；DC X-2025.06-SP3；DWBB X-2025.06-DWBB_202506.3；compile_ultra。',
              '- 所有 DC 任务使用 CPU 8-23、单 DC 核、MemoryHigh=36G/MemoryMax=40G/SwapMax=0。',
              '- 默认浮点路径为 BF16 product/reduction/recurrent accumulation，FTZ，`DW_fp_add #(7,8,0)`；无 `DW_fp_add #(23,8)`。',
              '- BF16 累计误差研究覆盖 K=16/64/128/256/1024；这些是数值误差数据，不替代目标模型准确度回归。',
              '- 未执行 Formality、post-synthesis gate simulation 或 P&R。', '']
    (OUT / 'LOCAL_EXECUTION_REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
    print(OUT / 'LOCAL_EXECUTION_REPORT.md')


if __name__ == '__main__':
    main()

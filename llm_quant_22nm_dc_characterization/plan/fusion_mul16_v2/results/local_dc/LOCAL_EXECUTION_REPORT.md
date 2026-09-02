# FusionMul16 v2 本地执行报告

## Gate 结论

- Python：20/20 PASS。
- VCS：7 模式共 3584 vectors，product crosscheck 零失配；config protocol PASS。
- DC：21/21 个 1.000ns run 完成；校验报告 `ERRORS=NONE`。
- Required timing groups：7/7 通过 1GHz。
- Brick proof：PASS；brick=16，DW4x4=16，额外 multiplier=0。
- Architecture accept：`True`。

## 1 GHz 关键比较

| Architecture | Area (µm²) | WNS (ns) | Timing | Eligible |
|---|---:|---:|---:|---:|
| V2_SHARED_FULL7_FTZ | 11995.438 | 0.000027 | 1 | 1 |
| V2_SEPARATE_FULL_FTZ | 14214.291 | 0.000005 | 1 | 1 |
| V1_SHARED_FULL_REFERENCE | 23201.815 | -0.100014 | 0 | 0 |
| V1_SEPARATE_FULL_REFERENCE | 27912.885 | -0.008636 | 0 | 0 |

## P5 消融

| Group | Area increment | WNS delta (ns) | Timing |
|---|---:|---:|---:|
| V2_CORE_BASE4_FTZ |  |  | 1.0 |
| V2_CORE_PLUS_I4FP8_FTZ | 1.106% | -0.000017 | 1.0 |
| V2_CORE_PLUS_I4BF16_FTZ | 9.038% | -0.000016 | 1.0 |
| V2_CORE_FULL7_FTZ | 0.213% | -0.000102 | 1.0 |
| V2_CORE_FULL7_SPECIAL | 4.443% | -0.000034 | 1.0 |

## 固定边界

- CLN22UL base SVT C35 TT typical_max 0.80V/25C；DC X-2025.06-SP3；DWBB X-2025.06-DWBB_202506.3；compile_ultra。
- 所有 DC 任务使用 CPU 8-23、单 DC 核、MemoryHigh=36G/MemoryMax=40G/SwapMax=0。
- 默认浮点路径为 BF16 product/reduction/recurrent accumulation，FTZ，`DW_fp_add #(7,8,0)`；无 `DW_fp_add #(23,8)`。
- BF16 累计误差研究覆盖 K=16/64/128/256/1024；这些是数值误差数据，不替代目标模型准确度回归。
- 未执行 Formality、post-synthesis gate simulation 或 P&R。

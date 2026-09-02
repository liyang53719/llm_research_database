# 本地 22 nm DC 验收

## 固定条件

```text
clock period  = 1.000 ns only
library       = CLN22UL base SVT C35
PVT           = TT typical_max, 0.80 V, 25 C
DC            = X-2025.06-SP3
DWBB          = X-2025.06-DWBB_202506.3
compile       = compile_ultra
```

不得增加 2.0/0.9 ns sweep，不得为某一种方案单独放宽周期。

## 12 个 run

```text
3 accumulator-only
3 full seven-mode cluster
3 fixed FP8 cluster
3 fixed BF16 cluster
```

每类均覆盖三种 accumulator style。

## 硬数据门槛

```text
12 / 12 summaries present
mapped_cell_area_um2 > 0
blackbox_count = 0
clock_period_ns = 1.0
library/PVT/compile/hash consistent
report_area/report_qor/report_timing/report_resources/report_exceptions present
15 / 15 VCS accumulator sequences pass
```

## 时序门槛

Style 0 和 Style 1 使用单周期约束。

Style 2 的 FP32 checkpoint path使用已实现的两周期协议：

```text
setup multicycle = 2
hold multicycle  = 1
```

必须证明：

```text
constraint pattern matched non-zero source/destination registers
report_exceptions 中存在目标 path
checkpoint operands 保持稳定
checkpoint destination 只在第二周期使能
没有对 product tree/BF16 partial path施加 multicycle
```

## Baseline reproduction

以下两项相对 v2 commit `041e6fc...` 允许 ±5%：

```text
V3_ACC_FULL_BF16            vs V2_BF16_ACCUM_ONLY 6270.992 µm²
V3_CLUSTER_FULL_BF16_FULL7  vs V2_SHARED_FULL7_FTZ 11995.438 µm²
```

超过范围必须审计 wrapper、output observability、hierarchy、library setup 和 DC 版本。

## 架构选择

候选必须：

```text
VCS pass
1 GHz timing_met
synthetic gate pass
```

然后在方案 2/3 中选择 full-cluster mapped-cell area 较小者。Full BF16 只有在目标模型精度回归通过时才能重新进入最终候选。

最终结果必须同时报告：

```text
area
WNS
latency
II
output precision
number of BF16 adders
number of FP32 adders
checkpoint frequency
multicycle exceptions
```

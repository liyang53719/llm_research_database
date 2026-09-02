# FusionMul16 v3：三种浮点累加后端对照

## 目标

在 FusionMul16 v2 的同一 product pipe、同一七种模式和同一 BF16 product 格式之后，只替换累加后端，对比：

1. `FULL_BF16`：BF16 pair/lane reduction + BF16 recurrent accumulation；
2. `BF16_TREE_FP32_RECURRENT`：BF16 pair/lane reduction + 4×FP32 recurrent accumulation；
3. `BF16_BLOCK64_FP32_CHECKPOINT`：BF16 pair/lane reduction + BF16 Kblock=64 partial sum + 4×FP32 checkpoint accumulation。

所有方案保留：

```text
FusionMul16 v2 16×4-bit brick product pipe
128-bit packed lhs/rhs interface
七种 INT/FP/mixed mode
FTZ/RNE product-to-BF16 contract
stream initiation interval II=1
```

## 本地验证已完成

```text
20 / 20 Python tests PASS
54 rows deterministic numerical study
15 / 15 accumulator VCS cases PASS
12 / 12 one-GHz DC runs PASS
7 SystemVerilog source files structurally checked
```

沙箱没有 VCS、DC、DesignWare 和 CLN22UL `.db`；本地执行使用官方 DesignWare 模型和 CLN22UL base SVT C35 TT typical_max 0.80 V 25 C。

本地 DC 门禁结果：`results/local_dc/validation_report.txt` 为 `ERRORS NONE`。所有 12 组均为 `compile_ultra`、1.000 ns、blackbox=0、DC error=0，且没有删除 timing-fail 点。

资源约束：DC 顺序单任务，`taskset -c 8-23`，`DC_MAX_CORES=1`，systemd `MemoryMax=40G`，执行期间未观察到 OOM。

## 第一轮数值结论

高精度参考使用已经量化后的输入，以 float64 对相同输入做 dot product。乘积仍按 v2 规则舍入成 BF16，因此本对照只改变 reduction/recurrent accumulation。

### Gaussian，FP8-like 输入

| K | 方案 | NRMSE | 过滤后 P99 相对误差 |
|---:|---|---:|---:|
| 128 | Full BF16 | 0.693% | 4.720% |
| 128 | BF16 tree + FP32 recurrent | 0.226% | 2.720% |
| 128 | Kblock64 + FP32 checkpoint | 0.550% | 5.654% |
| 1024 | Full BF16 | 2.050% | 16.596% |
| 1024 | BF16 tree + FP32 recurrent | 0.252% | 2.841% |
| 1024 | Kblock64 + FP32 checkpoint | 0.575% | 6.869% |
| 4096 | Full BF16 | 4.325% | 38.534% |
| 4096 | BF16 tree + FP32 recurrent | 0.235% | 3.179% |
| 4096 | Kblock64 + FP32 checkpoint | 0.579% | 7.258% |

### Gaussian，BF16 输入

| K | 方案 | NRMSE | 过滤后 P99 相对误差 |
|---:|---|---:|---:|
| 128 | Full BF16 | 1.286% | 8.013% |
| 128 | BF16 tree + FP32 recurrent | 0.168% | 1.871% |
| 128 | Kblock64 + FP32 checkpoint | 0.952% | 8.325% |
| 1024 | Full BF16 | 3.326% | 17.920% |
| 1024 | BF16 tree + FP32 recurrent | 0.163% | 1.740% |
| 1024 | Kblock64 + FP32 checkpoint | 0.942% | 10.071% |
| 4096 | Full BF16 | 7.521% | 38.752% |
| 4096 | BF16 tree + FP32 recurrent | 0.180% | 2.065% |
| 4096 | Kblock64 + FP32 checkpoint | 1.049% | 13.995% |

K=4096 时，FP32 recurrent 相对 Full BF16 将 NRMSE 降低约 94.6%–97.6%；Kblock64 将 NRMSE 降低约 86%。

这些是 synthetic proxy，不是目标模型准确率。最终必须补目标 checkpoint 的 layer output、logit、困惑度和任务回归。

## 三种硬件结构

### 1. Full BF16

```text
12 × BF16 pair/lane add
 4 × BF16 recurrent add
```

总计 16 个 BF16 adder。预计面积最低，但长 K 误差尾部最大。

### 2. BF16 tree + FP32 recurrent

```text
12 × BF16 pair/lane add
 4 × FP32 recurrent add
```

不恢复 v1 的 16 路 FP32 product expansion，只提高四个长期 accumulator。数值最好，但每周期存在 FP32 recurrence，1 GHz 时序风险最高。

### 3. BF16 Kblock64 + FP32 checkpoint

```text
12 × BF16 pair/lane add
 4 × BF16 block-partial recurrent add
 4 × FP32 checkpoint add
counter + checkpoint control
```

FP32 checkpoint 每 64 products/lane 更新一次。FP8 mode 为每 16 个输入周期一次，BF16 mode 为每 64 个输入周期一次。RTL 将 checkpoint operands 保持两周期，并提供匹配的 setup=2/hold=1 multicycle constraint。流式输入 II 仍为 1。

## 本地 1 GHz DC 结果

| Full-cluster 后端 | 面积 (um²) | WNS (ns) | BF16 add | FP32 add | synthetic K=4096 |
|---|---:|---:|---:|---:|---|
| Full BF16 | 11781.133 | +0.0000192523 | 16 | 0 | FAIL |
| BF16 tree + FP32 recurrent | 14043.211 | +0.00000798702 | 12 | 4 | PASS |
| BF16 Kblock64 + FP32 checkpoint | 14869.491 | +0.00000268221 | 16 | 4 | PASS |

P5 按“1 GHz timing closed 且 synthetic gate pass 的 full-cluster 面积最小”选择 `BF16 tree + FP32 recurrent`，见 `results/local_dc/p5_ablation_decision.json`。目标模型 layer/logit、困惑度和任务准确度仍为 `OPEN`，不能由 synthetic proxy 代替。

## 预期决策逻辑

```text
数据完整性：12/12 DC，blackbox=0，15/15 VCS
       ↓
1 GHz timing gate
       ↓
synthetic K=4096 gate
       ↓
在通过者中取 mapped-cell area 最小者
       ↓
目标模型准确度最终签核
```

Synthetic gate 当前结果：

```text
Full BF16                         FAIL
BF16 tree + FP32 recurrent        PASS
BF16 Kblock64 + FP32 checkpoint   PASS
```

因此本地 DC 的核心问题已经收敛为：方案 2 与方案 3 哪一个在 1 GHz 下有更好的面积/时序 Pareto。

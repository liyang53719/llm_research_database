# 本地 Agent 交接：INT / FP 混合阵列

## 固定环境

```text
library_set_id = cln22ul_sc6p5mcpp140z_base_svt_c35_r3p0_tt_0p80v_25c
PVT            = TT typical_max, 0.80 V, 25 C
DC             = X-2025.06-SP3
DWBB           = X-2025.06-DWBB_202506.3
compile        = compile_ultra
periods        = 2.0 ns, 1.0 ns, 0.9 ns
```

## 任务

对 `config/mixed_experiment_groups.csv` 的 21 个设计组执行 63 次综合，回答：

1. INT4/INT8×FP8、INT4/INT8×BF16 的真实 22 nm area/timing；
2. converter-based、dual-domain 和 shared-product 的面积差；
3. 在匹配 MAC/cycle 后，hybrid 是否优于 `INT array + right-sized FP tile`。

`ALLFP32_*` 已删除，不再浪费 DC 运行。

## 先计算真实浮点峰值比例 r

```text
r = required_FP_peak_MAC_per_cycle / INT_main_array_peak_MAC_per_cycle
required_FP_peak = max_i(FP_MACs_in_window_i / allowed_time_i)
```

必须从目标模型的 operator/window trace 计算，不能使用 1/8、1/4、1/2 作为经验结论。可继续用这些点做 sweep，但要标记为 scenario。

## 必须补的本地验证

1. 用本地 DW databook 核对 `DW_fp_i2flt`、`DW_fp_mac`、`DW_fp_add` 参数顺序和状态位。
2. 对 `hybrid_shared_mul_dual_acc`：exhaustive INT4/INT8，FP8 finite code 分层抽样，以及 BF16 normal/subnormal/zero/Inf/NaN 定向测试。
3. 统一输出 INT/FP MAC/cycle、是否可并发、accumulator 格式和 mode-switch 粒度。
4. `ARRAY4_*` 必须同时输出全部 INT/FP signature，防止 DC 删除未观察模块。
5. BF16/shared-FP32-accumulator 路径不能在 1 GHz 闭合时，增加明确流水组，不得直接放宽周期后与整数 1 GHz 面积排名。

## 输出

```text
results/mixed_area_raw.csv
results/mixed_group_summary.csv
results/mixed_architecture_comparison.csv
results/validation_report.txt
results/numeric_rtl_crosscheck.csv
```

## 验收

```text
63 行完整
mapped_cell_area_um2 > 0
blackbox_count = 0
同一 library_setup SHA / RTL bundle SHA
三个周期全部保留
1 GHz area 与 best-feasible area 分列
匹配吞吐后再计算 area ratio
timing-fail 和非单调点不删除
```

# 本地 Agent 交接：FusionMul16 22 nm 综合、仿真与结构证明

## 1. 任务目标

完成以下判断：

1. RTL 是否真的只使用 16 个 4×4 multiplier brick；
2. bit-slice fusion 后，INT4/INT8/INT16、FP8、BF16 和 mixed product 是否数值正确；
3. 一个 shared FusionMul16、两个 shared cluster、三套 separate cluster 的 1 GHz 面积/时序如何；
4. 在匹配 mode throughput 与并发能力后，FusionMul16 是否进入面积 Pareto 前沿。

## 2. 固定环境

沿用 commit `2f9f8313b89c6a2c217a90d04e611151c8f721a6` 的比较合同：

```text
library_set_id = cln22ul_sc6p5mcpp140z_base_svt_c35_r3p0_tt_0p80v_25c
PVT            = TT typical_max, 0.80 V, 25 C
DC             = X-2025.06-SP3
DWBB           = X-2025.06-DWBB_202506.3
compile        = compile_ultra
periods        = 2.0 ns, 1.0 ns, 0.9 ns
```

不得改变 library、PVT、I/O transition、output load、clock uncertainty 或 compile mode 后继续使用同一个 comparison group。

## 3. 执行顺序

### Gate A：沙箱结果复现

```bash
python3 extract_source_bundle.py
python3 scripts/run_sandbox_validation.py
```

要求 17 个单元测试全部通过，生成：

```text
results/sandbox_validation.json
results/rtl_vectors.jsonl
results/area_thresholds.csv
build_dc/runs.csv
```

### Gate B：RTL 编译和仿真

使用本地 VCS、Verilator 或其他支持 SystemVerilog unpacked array port 的 simulator。

最低验证：

```text
INT4×INT4        全部 256 对
INT4×INT8        全部 4096 对
INT8×INT8        全部 65536 对
INT16×INT16      边界 + >=100000 随机
FP8×FP8          全部 65536 raw-code 对
INT4×FP8         全部 4096 对
INT8×FP8         全部 65536 对
BF16×BF16        directed + stratified >=100000 对
INT4/INT8×BF16   directed + stratified >=50000 对
```

必须覆盖 `+0/-0`、normal、subnormal、Inf、NaN、最大有限数、最小非零数和全部符号组合。任何 mismatch 都是 hard fail。

### Gate C：16-brick 结构证明

先运行 `BRICK16_BARE_PROOF` 与 `FUSION16_CORE_PROOF`。Proof run 必须开启：

```text
FUSION_USE_DW
KEEP_BRICKS=1
```

执行：

```bash
python3 scripts/prove_brick_sharing.py \
  build_dc/FUSION16_CORE_PROOF__T1p0ns \
  --output results/local_dc/brick_sharing_proof.json
```

硬验收：

```text
brick_instance_count_precompile      = 16
dw_mult_instance_count_precompile    = 16
blackbox_count                       = 0
额外 8×8 / 16×16 / FP multiplier     = 0
```

除 16 个 `DW_mult_uns a_width=4 b_width=4` 外，不允许出现其他 multiplier operation。FP 路径只允许 add、shift、normalize、compare 和 accumulator 逻辑。

### Gate D：PPA 综合

```bash
python3 scripts/gen_dc_runs.py
python3 scripts/run_dc.py --lib-setup ../config/library_setup.local.tcl --jobs 1
python3 scripts/collect_dc_results.py
python3 scripts/validate_dc_results.py
```

计划：`11 groups × 3 periods = 33 DC runs`。

## 4. 设计组

| Group | 用途 |
|---|---|
| BRICK16_BARE_PROOF | 16 个裸 4×4 brick 面积 |
| FUSION16_CORE_PROOF | 证明没有隐藏 multiplier |
| FUSION16_CORE_PPA | decode + fusion network 面积 |
| FUSION16_INT_ACC_ONLY | 四个整数 accumulator 面积 |
| FUSION16_FP_ACC_ONLY | 四个 FP dot/FP32 accumulator 面积 |
| FUSION16_INT_ONLY_PIPE | dedicated integer cluster |
| FUSION16_FP8_ONLY_PIPE | dedicated FP8 dot4 cluster |
| FUSION16_BF16_ONLY_PIPE | dedicated BF16 cluster |
| FUSION16_SHARED_FULL_PIPE | 单 shared cluster |
| FUSION16_SEPARATE_FULL_PIPE | 三套 dedicated cluster，可并发 |
| FUSION16_DUAL_SHARED_PIPE | 两个 shared cluster，可运行两个模式 |

## 5. 公平比较

必须同时记录 INT/FP8/BF16 products per cycle、dot outputs per cycle、模式并发数、mode switch 粒度、INT accumulator width、FP accumulator format 和 pipeline latency。

FusionMul16 峰值合同：

```text
INT4×INT8   8 products/cycle
INT8×INT8   4 products/cycle
FP8×FP8    16 products/cycle，4个dot4输出
BF16×BF16   4 products/cycle
```

Separate matched reference 必须达到相同峰值。若 comparison 允许并发，Shared 单 cluster 不等价，必须使用 dual shared 或标记 `partial_throughput_match`。

## 6. 交付

```text
results/local_dc/fusion16_area_raw.csv
results/local_dc/fusion16_group_summary.csv
results/local_dc/validation_report.txt
results/local_dc/brick_sharing_proof.json
results/local_dc/numeric_rtl_crosscheck.csv
results/local_dc/architecture_pareto.csv
```

## 7. 决策门槛

Shared FusionMul16 进入候选需同时满足：

1. 1 GHz 过时序；
2. proof run 只有 16 个 4×4 DW multiplier；
3. 所有数值测试零失败；
4. 同吞吐 exclusive-mode 面积小于 separate；
5. 若产品要求 INT+FP 并发，dual shared 面积小于 matched separate；
6. FP accumulator 精度满足模型要求；
7. routing/mode mux 没有使 16-brick core 丧失预期吞吐。
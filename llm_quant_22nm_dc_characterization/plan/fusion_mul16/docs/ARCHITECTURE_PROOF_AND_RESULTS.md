# FusionMul16 微架构、DC 证明与结果格式

## 1. Brick 与 Fusion Lane

```text
16 × unsigned 4×4 brick
  ├─ Lane 0: brick 0..3
  ├─ Lane 1: brick 4..7
  ├─ Lane 2: brick 8..11
  └─ Lane 3: brick 12..15
```

每 lane 的四个 brick 可以解释为 4 个独立 4×4 product、2 个 4×8 product 或 1 个 8×8 product。四个 lane 再跨 lane 融合，可形成一个 16×16 product。

### Integer partial products

```text
4×8:
P = a4*b[3:0] + (a4*b[7:4] << 4)

8×8:
P = a_lo*b_lo
  + ((a_lo*b_hi + a_hi*b_lo) << 4)
  + (a_hi*b_hi << 8)

16×16:
P = Σ brick[a_nibble][b_nibble] << 4*(a_index+b_index)
```

Signed integer 先计算 magnitude，最后统一施加 sign。

## 2. FP8/BF16 Product

FP8 E4M3 significand 是 4 bit（含 hidden bit），每个 product 使用一个 brick。BF16 significand 是 8 bit（含 hidden bit），每个 product 使用四个 brick。

浮点 product 由以下字段重构：

```text
product_sign
raw_significand_product
scale_exp_a + scale_exp_b
zero / Inf / NaN flags
```

`fusion_mul16_product_core` 将结果转换为 FP32 product；`fusion_mul16_fp32_accum_dw` 以四个 lane 组织 dot reduction，并使用 FP32 accumulation。

## 3. Dot Accumulator

| 模式 | 每 lane 输入 product 数 | Cluster product/cycle | dot output/cycle |
|---|---:|---:|---:|
| INT4×INT4 | 4 | 16 | 4 |
| INT4×INT8 | 2 | 8 | 4 |
| INT8×INT8 | 1 | 4 | 4 |
| FP8×FP8 | 4 | 16 | 4 |
| BF16×BF16 | 1 | 4 | 4 |
| INT4×FP8 | 4 | 16 | 4 |
| INT8×FP8 | 2 | 8 | 4 |
| INT4×BF16 | 2 | 8 | 4 |
| INT8×BF16 | 1 | 4 | 4 |

INT16×INT16 使用全部 16 brick，只输出 lane0。

## 4. 流水

```text
Stage 0  decode + brick multiply + partial product fusion
Stage 1  register product vector
Stage 2  FP pair add / integer lane sum
Stage 3  FP lane reduction
Stage 4  FP32 accumulator
```

整数路径比浮点路径短，`int_valid_o` 与 `fp_valid_o` 独立。

## 5. 为什么源码只有一个乘法符号仍不够

综合可以复制运算、合并不同模式或在 hierarchy flatten 后失去源码边界。因此必须同时保留源码证明、elaboration 证明和 mapped report。

Proof run 使用 `FUSION_USE_DW`，令每个 brick 显式实例化 `DW_mult_uns #(4,4)`，并设置：

```tcl
set_dont_touch [get_cells -hierarchical -filter "ref_name == mul4x4_brick"]
set_ungroup    [get_cells -hierarchical -filter "ref_name == mul4x4_brick"] false
```

预期：

```text
brick_instance_count_precompile   = 16
dw_mult_instance_count_precompile = 16
blackbox_count                    = 0
```

检查 `report_resources_pre/post.rpt` 与 `report_reference_pre/post.rpt`。允许 16 个 4×4 `DW_mult_uns`；禁止额外 8×8、16×16、`DW_fp_mult` 或其他 multiplier operation。FP 路径只允许 `DW_fp_add`、shift、normalize、compare 和 accumulator。

PPA run 可以 flatten 和门级重构，但必须与 proof RTL functional-equivalent。建议使用 Formality；没有 Formality 时，至少执行 exhaustive/directed RTL 仿真与 post-synthesis gate simulation。

## 6. 面积拆解

```text
BRICK16_BARE_PROOF          纯 brick + register
FUSION16_CORE_PPA           + decode/fusion/FP product conversion
FUSION16_INT_ACC_ONLY       integer accumulator
FUSION16_FP_ACC_ONLY        FP dot reduction + FP32 accumulator
FUSION16_SHARED_FULL_PIPE   shared 完整簇
FUSION16_SEPARATE_FULL_PIPE three dedicated 簇
FUSION16_DUAL_SHARED_PIPE   two shared 簇
```

面积不一定严格线性相加，拆解仅用于定位主导项。

## 7. 结果格式

`fusion16_area_raw.csv` 至少包括：

```text
run_id, group_id, top_module, category
clock_period_ns, clock_mhz, library_set_id
mapped_cell_area_um2, leaf_cell_count, blackbox_count
brick_instance_count_precompile
dw_mult_instance_count_precompile
report_dw_mult_4x4_rows, report_other_multiplier_rows
wns_ns, critical_delay_ns, achieved_fmax_mhz, timing_met
tool_version, status, report_dir
```

`architecture_pareto.csv` 至少包括：

```text
architecture, area_1ghz_um2
int4xint8_products_per_cycle
int8xint8_products_per_cycle
fp8_products_per_cycle
bf16_products_per_cycle
dot_outputs_per_cycle
concurrent_mode_count
int_latency_cycles, fp_latency_cycles
accumulator_contract, throughput_match
reference_architecture, area_ratio, area_saving_pct
pareto_dominated
```

## 8. 仍需本地评估

- BF16 subnormal 与 rounding 策略；
- FP8 E4M3FN 特殊编码；
- FP32 accumulator 是否应改成 BF16/FP16/block-float；
- unpacked array port 对 DC QoR 的影响；
- 输入 decode 与 mode mux 是否需要前置流水；
- 两个 shared cluster 是否优于三套 separate cluster。
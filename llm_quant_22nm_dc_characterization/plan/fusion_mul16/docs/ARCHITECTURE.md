# FusionMul16 微架构

## 1. Brick 与 Fusion Lane

```text
16 × unsigned 4×4 brick
  ├─ Lane 0: brick 0..3
  ├─ Lane 1: brick 4..7
  ├─ Lane 2: brick 8..11
  └─ Lane 3: brick 12..15
```

每 lane 的四个 brick 可以解释为：

```text
4 个独立 4×4 product
2 个 4×8 product
1 个 8×8 product
```

四个 lane 再跨 lane 融合，可形成一个 16×16 product。

## 2. Integer Partial Products

### 4×8

```text
P = a4*b[3:0] + (a4*b[7:4] << 4)
```

### 8×8

```text
P = a_lo*b_lo
  + ((a_lo*b_hi + a_hi*b_lo) << 4)
  + (a_hi*b_hi << 8)
```

### 16×16

```text
P = Σ brick[a_nibble][b_nibble] << 4*(a_index+b_index)
```

Signed integer 先计算 magnitude，最后统一施加 sign。

## 3. FP8/BF16 Product

FP8 E4M3：

```text
significand = 4 bit，包括 hidden bit
每 product = 1 brick
```

BF16：

```text
significand = 8 bit，包括 hidden bit
每 product = 4 bricks
```

浮点 product 由以下字段重构：

```text
product_sign
raw_significand_product
scale_exp_a + scale_exp_b
zero / Inf / NaN flags
```

`fusion_mul16_product_core` 将结果转换为 FP32 product。`fusion_mul16_fp32_accum_dw` 以四个 lane 组织 dot reduction，并使用 FP32 accumulation。

## 4. Dot Accumulator

| 模式 | 每 lane 输入 product 数 | Cluster product/cycle | Cluster dot output/cycle |
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

## 5. 流水

`fusion_mul16_cluster_dw_pipe`：

```text
Stage 0  decode + brick multiply + partial product fusion
Stage 1  register product vector
Stage 2  FP pair add / integer lane sum
Stage 3  FP lane reduction
Stage 4  FP32 accumulator
```

整数路径比浮点路径短，`int_valid_o` 与 `fp_valid_o` 独立。

## 6. 需要本地重新评估的部分

- BF16 subnormal 和 rounding 策略；
- FP8 E4M3FN 特殊编码；
- FP32 accumulator 是否应改成 BF16/FP16/block-float；
- unpacked array port 对 DC QoR 的影响；
- 输入 decode 与 mode mux 是否需要前置流水；
- 两个 shared cluster 是否优于三套 separate cluster。

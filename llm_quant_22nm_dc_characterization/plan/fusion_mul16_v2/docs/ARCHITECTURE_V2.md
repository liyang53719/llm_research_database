# FusionMul16 v2 微架构

## 数据通路

```text
Tile config
  └─ mode_q + onehot_q + rnd_q
      │  config must precede data
      v
S0 packed 128b unpack / operand routing
      v
S1 16 × 4×4 brick operands registered
      v
S2 16 × 4×4 product registered
      v
S3 narrow integer/FP product fusion (raw width <=16b)
      v
S4 raw16 → BF16 RNE/FTZ pack
      v
A0 BF16 pair adds
      v
A1 BF16 lane reduction
      v
A2 BF16 recurrent accumulator
```

整数路径在 S3 后进入 4 个 INT48 accumulator；浮点路径继续到 S4/A0/A1/A2。两条路径 II 均为 1。

## P0：mode 移出关键路径

mode 不再作为每周期裸数据输入参与 product-stage case。配置通过 `cfg_valid/cfg_ready` 在 pipeline 空闲时写入：

```text
mode_q
mode_onehot_q
rnd_q
```

同周期 config beat 优先于 data beat，防止旧模式错误接收数据。一个 transaction 内 mode 保持不变。

## P1：packed interface 与删除 INT16 direct

接口固定：

```systemverilog
logic [127:0] lhs_packed_i;
logic [127:0] rhs_packed_i;
```

它覆盖最大物理需求：16×FP8 或 8×BF16。删除原 `logic [15:0] lhs_i[0:15]`，避免 512-bit 双输入和大量无用 bit decode。

INT16 不占用硬件模式。软件/微码使用四个 INT8 unsigned magnitude partial products：

```text
a0*b0
+a0*b1<<8
+a1*b0<<8
+a1*b1<<16
```

在四次 issue 中写同一个更宽 accumulator。

## P2：BF16 accumulation

FP product 不再展开和寄存为 FP32。每个 raw product 先归一化/舍入为 BF16，然后执行：

```text
pair BF16 add
lane BF16 add
recurrent BF16 add
```

共 16 个 `DW_fp_add #(7,8,0)`，禁止出现 `DW_fp_add #(23,8,0)`。

## P3/P4：额外流水和窄 normalizer

FP path 在 product fusion 后增加 raw-product register，再使用独立 S4 完成 16-bit LZD/normalize/BF16 pack。最大 raw significand 只有 16 bit：

```text
FP8×FP8       8 bit
I4×FP8        8 bit
BF16×BF16    16 bit
I4×BF16      12 bit
I8×BF16      16 bit
```

不需要 generic 32-bit normalizer。

## P5：模式裁剪

默认删除：

```text
I4×I4：W4A4 不进入产品模式
I16×I16：低利用率且要求宽输入/宽 fusion tree
I8×FP8：源值无法无损映射到 E4M3，且硬件转换昂贵
```

I4×FP8、I4×BF16、I8×BF16 与 special-value support 通过编译参数独立开关，用 1 GHz 消融综合决定是否默认启用。

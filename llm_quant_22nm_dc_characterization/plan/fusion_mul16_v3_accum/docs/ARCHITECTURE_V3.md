# FusionMul16 v3 累加微架构

## 共享前端

三种方案使用完全相同的 v2 前端：

```text
cfg/mode register
→ 128-bit packed operand routing
→ 16×4×4 shared multiplier brick
→ narrow product fusion
→ raw16 to BF16 RNE/FTZ
→ bf16_lane_item[4][4]
```

本轮不改乘法 brick、模式映射、product latency 或输入位宽，防止把 product pipe 改动误算为 accumulator 收益。

## 公共 BF16 tree

`fusion_mul16_v3_bf16_tree_dw.sv` 每 lane 执行：

```text
A0: p0+p1, p2+p3 in BF16
A1: pair01+pair23 in BF16
```

四 lane 共 12 个 `DW_fp_add #(7,8,0)`，两级流水，II=1。

## Style 0：Full BF16

第三阶段：

```text
A2: bf16_acc[lane] + lane_sum_bf16
```

四个 BF16 recurrent add。输出 BF16，同时提供零扩 fraction 的 FP32 view。

## Style 1：FP32 recurrent

第三阶段：

```text
BF16 lane sum → exact FP32 widening
A2: fp32_acc[lane] + lane_sum_fp32
```

四个 `DW_fp_add #(23,8,0)`，每个有效周期更新。II=1 必须由真实 1 GHz recurrence path 证明。

## Style 2：Kblock64 checkpoint

每 lane：

```text
BF16 tree output
→ BF16 partial recurrent accumulator
→ product counter
→ every 64 products capture partial term
→ FP32 checkpoint accumulator
```

`items_per_lane`：

```text
FP8×FP8, I4×FP8  = 4
I4×BF16           = 2
BF16×BF16,I8×BF16 = 1
```

checkpoint 间隔：

```text
FP8 / I4FP8       16 cycles
I4BF16            32 cycles
BF16 / I8BF16     64 cycles
```

FP32 checkpoint operands在 block boundary 被捕获并保持两周期。结果寄存器只在第二周期使能，使用：

```tcl
set_multicycle_path 2 -setup
set_multicycle_path 1 -hold
```

这不是伪造时序豁免：RTL 的 destination enable 与 operand stability 明确实现了两周期语义。

## clear / flush 合同

- `clear_i` 是独立 control bubble；不得与第一个 valid beat 同拍。
- block64 尾块若不足 64 products，product tree drain 后以独立 `flush_i` beat 提交。
- `flush_i` 与 `valid_i` 同拍、checkpoint busy 或 tree 未 drain 都置 `protocol_error_o`。
- 主流 LLM K 通常可按 64 padding；即便如此仍保留 tail flush 以支持测试和非标准 shape。

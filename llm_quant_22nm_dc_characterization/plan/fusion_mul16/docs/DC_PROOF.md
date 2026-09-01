# DC 结构证明与 PPA 规则

## 1. 为什么源码中只有一个 `*` 还不够

HLS/RTL 综合可以：

- 复制运算满足时序；
- 合并不同模式的运算；
- 将表达式重写成不同位宽 datapath；
- 在 hierarchy flatten 后失去源码实例边界。

所以必须同时保留源码证明、elaboration 证明和 mapped netlist 报告。

## 2. Proof Run

`mul4x4_brick.sv` 在 `FUSION_USE_DW` 下实例化：

```systemverilog
DW_mult_uns #(4,4)
```

`fusion_mul16_product_core` 只实例化一个 16 次 generate loop。

Proof run 设置：

```tcl
set_dont_touch [get_cells -hierarchical -filter "ref_name == mul4x4_brick"]
set_ungroup    [get_cells -hierarchical -filter "ref_name == mul4x4_brick"] false
```

DC summary 必须记录：

```text
brick_instance_count_precompile
dw_mult_instance_count_precompile
```

预期均为 16。

## 3. 额外乘法器检查

检查：

```text
report_resources_pre.rpt
report_resources_post.rpt
report_reference_pre.rpt
report_reference_post.rpt
```

允许：

```text
16 × DW_mult_uns, a_width=4, b_width=4
```

禁止：

```text
额外 DW_mult_uns 8×8
额外 DW_mult_uns 16×16
DW_fp_mult
其他 mult operation
```

FP 路径只允许 `DW_fp_add` 和 normalization/shift/compare 逻辑。

## 4. PPA Run

PPA run 允许 flatten 和门级重构。PPA 结果不要求保留 16 个可见 brick instance，但必须与 proof RTL functional-equivalent。

建议执行 Formality：

```text
Proof hierarchy RTL
        vs
PPA flattened netlist
```

若不具备 Formality，至少完成 exhaustive/directed simulation plus post-synthesis gate simulation。

## 5. 面积拆解

利用以下组做归因：

```text
BRICK16_BARE_PROOF          纯 brick + register
FUSION16_CORE_PPA           + decode/fusion/FP product conversion
FUSION16_INT_ACC_ONLY       integer accumulator
FUSION16_FP_ACC_ONLY        FP dot reduction + FP32 accumulator
FUSION16_SHARED_FULL_PIPE   shared 完整簇
FUSION16_SEPARATE_FULL_PIPE three dedicated 簇
```

面积不一定严格线性相加；拆解仅用于定位主导项。

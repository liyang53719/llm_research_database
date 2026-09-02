# 为什么 v1 FP8-only 比 BF16-only 总面积大

## 原始事实

v1 timing-closed 500 MHz：

```text
FP8-only  = 8741.460 µm²
BF16-only = 4296.747 µm²
```

看总面积似乎 FP8 更大，但吞吐合同不同：

```text
FP8-only : 16 products/cycle，4 lanes × dot4 reduction
BF16-only:  4 products/cycle，4 lanes × scalar accumulation
```

归一化：

```text
FP8  = 8741.460 / 16 = 546.341 µm²/product-cycle
BF16 = 4296.747 / 4  = 1074.187 µm²/product-cycle
```

FP8 的单位 product 面积约低 49.1%。总面积更大来自四倍 product rate 和额外 reduction tree，而不是 FP8 significand multiplier 比 BF16 大。

## 是否应该所有 FP8 都转 BF16

FP8 E4M3 significand 是 4 bit，一个 product 使用 1 个 4×4 brick；BF16 significand 是 8 bit，一个 product使用 4个brick。

因此 16-brick cluster：

```text
native FP8          16 products/cycle
FP8 widened to BF16  4 products/cycle
BF16 native          4 products/cycle
INT8×INT8            4 products/cycle
```

全部转 BF16 可以使浮点 product 数与 INT8×INT8 相同，但代价是 FP8 峰值降低 4×。若工作负载不需要 FP8 的 16 products/cycle，这可能是面积更小的产品选项；若希望保留 FP8 吞吐，应使用 native 4-bit FP8 significand product，再将 product 舍入到 BF16 做 reduction/accumulation。

v2 同时提供两个实测候选：

```text
V2_FP8_NATIVE_BF16ACC_FIXED
V2_FP8_WIDEN_BF16ACC_FIXED
```

用相同 1 GHz 条件直接比较面积、吞吐和 WNS。

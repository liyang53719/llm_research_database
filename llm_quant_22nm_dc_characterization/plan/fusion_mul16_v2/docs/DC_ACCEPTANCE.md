# 1 GHz DC 验收

## 运行数

```text
21 groups
1 period/group
clock period = 1.000 ns
21 total DC runs
```

## 结构门槛

```text
BRICK16_BARE_PROOF:
  bricks = 16
  DW_mult_uns 4×4 = 16
  other multiplier = 0

CORE/SHARED FULL7:
  precompile bricks = 16
  precompile DW mult = 16
  post-report other multiplier = 0
  FP32 DW_fp_add rows = 0
  BF16 DW_fp_add rows expected
```

## 时序门槛

以下全部 WNS≥0：

```text
V2_CORE_FULL7_FTZ
V2_SHARED_FULL7_FTZ
V2_SEPARATE_FULL_FTZ
V2_INT_I4I8_FIXED
V2_INT_I8I8_FIXED
V2_FP8_NATIVE_BF16ACC_FIXED
V2_BF16_ONLY_BF16ACC_FIXED
```

## 面积门槛

```text
V2_SHARED_FULL7_FTZ area < V2_SEPARATE_FULL_FTZ area
```

额外报告：

```text
v2 shared vs v1 shared = 1 - A_v2 / 23201.815
v2 separate vs v1 separate = 1 - A_v2 / 27912.885
native FP8 vs widen-to-BF16 area and throughput
each mode increment in core/shared ablation chain
```

## 判定

只有结构、数值、时序和面积四类门槛同时通过，`architecture_accept=true`。

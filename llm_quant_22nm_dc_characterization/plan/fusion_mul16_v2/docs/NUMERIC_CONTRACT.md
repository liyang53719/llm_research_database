# v2 数值合同

## Product

- I4×I8、I8×I8：整数 product exact；INT48 accumulation。
- FP8×FP8：E4M3FN significand exact product，经 RNE 舍入为 BF16。
- BF16×BF16：8×8 significand exact product，经 RNE 舍入为 BF16。
- I4×FP8、I4×BF16、I8×BF16：整数 magnitude 与浮点 significand exact product，经 RNE 舍入为 BF16。

## Accumulation

浮点 reduction 和 recurrent accumulation 均为 BF16：

```text
pair01 = BF16_ADD(p0,p1)
pair23 = BF16_ADD(p2,p3)
lane   = BF16_ADD(pair01,pair23)
acc    = BF16_ADD(acc,lane)
```

## 低面积默认

```text
BF16 subnormal output: FTZ
DW_fp_add ieee_compliance: 0
FP8 E4M3FN: finite values + NaN encoding, no Inf
```

`SUPPORT_SPECIALS=1` 是面积消融组，不是默认产品配置。

## 误差研究

随机高斯 study 仅用于识别 BF16 recurrent accumulation 风险，不能替代模型准确度：

```text
FP8-like K=128  NRMSE 0.758%
FP8-like K=1024 NRMSE 1.990%
BF16     K=128  NRMSE 0.736%
BF16     K=1024 NRMSE 1.761%
```

需要目标模型逐层和任务级回归后才能冻结。

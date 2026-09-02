# 三种累加策略的数值比较

## 参考口径

1. 先将输入量化为 BF16；FP8-like 场景进一步保留 3 个 fraction bit。
2. reference 对同一量化输入执行 float64 dot。
3. product 按 v2 合同舍入为 BF16。
4. 只改变 reduction/recurrent accumulation。

因此误差不包含“原始 FP32 tensor 到 BF16/FP8”的前端量化差异，主要反映 product BF16 舍入、BF16 tree 和 recurrent accumulation。

## 实际吞吐分组

v3 修正为符合硬件模式的每 lane product 数：

```text
FP8-like : 4 products/lane/cycle
BF16     : 1 product/lane/cycle
```

BF16 模式不会再被错误地按 dot4 recurrence 估算。

## K=4096 Gaussian

| Input | Accumulator | NRMSE | P99 relative |
|---|---|---:|---:|
| FP8-like | Full BF16 | 4.325% | 38.534% |
| FP8-like | BF16 tree + FP32 recurrent | 0.235% | 3.179% |
| FP8-like | Kblock64 checkpoint | 0.579% | 7.258% |
| BF16 | Full BF16 | 7.521% | 38.752% |
| BF16 | BF16 tree + FP32 recurrent | 0.180% | 2.065% |
| BF16 | Kblock64 checkpoint | 1.049% | 13.995% |

## 解释

- FP32 recurrent 消除了长期 BF16 accumulator 的 swamping；剩余误差主要来自 product-to-BF16 和 BF16 pair/lane tree。
- Kblock64 仍在每个 block 内进行 BF16 recurrent accumulation，所以误差高于 FP32 recurrent，但误差不再随完整 K 长度持续扩散。
- 正值分布下 Full BF16 的 K=4096 NRMSE 可达 34%–59%，是大 accumulator 吞掉小增量的典型表现；两个 FP32 checkpoint 方案显著改善。
- Gaussian P99 受正负抵消影响，比 NRMSE 更敏感。Kblock64 在短 K 的 P99 不保证逐样本单调改善，因此选择不能只看一个 percentile。

## Synthetic gate

K=4096：

```text
gaussian : NRMSE <= 1.25%, P99 <= 15%
positive : NRMSE <= 1.0%
outlier  : NRMSE <= 1.5%
```

结果：

```text
Full BF16                         FAIL
BF16 tree + FP32 recurrent        PASS
BF16 block64 + FP32 checkpoint    PASS
```

该门槛只用于架构 DSE，不代替目标模型签核。

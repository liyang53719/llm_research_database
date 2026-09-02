# P5 模式面积消融

## 为什么要消融

v1 1 GHz 面积分解：

```text
16 bare 4×4 bricks       222.859 µm²
product core            8665.748 µm²
FP accumulator-only    15371.811 µm²
shared full            23201.815 µm²
```

brick 只占 shared total 约 0.96%。面积主要来自 decode/fusion/normalization 和 FP accumulation。因此不能只优化 multiplier brick。

## 核心消融链

```text
V2_CORE_BASE4_FTZ
  modes = I4I8 + I8I8 + FP8FP8 + BF16BF16

V2_CORE_PLUS_I4FP8_FTZ
V2_CORE_PLUS_I4BF16_FTZ
V2_CORE_FULL7_FTZ       (+I8BF16)
V2_CORE_FULL7_SPECIAL   (+NaN/Inf)
```

## 完整 cluster 消融链

```text
V2_SHARED_BASE4_FTZ
V2_SHARED_PLUS_I4FP8_FTZ
V2_SHARED_PLUS_I4BF16_FTZ
V2_SHARED_FULL7_FTZ
V2_SHARED_FULL7_SPECIAL
```

## 砍模式规则

任一模式满足以下任一条件，默认关闭：

```text
area increment > 10%
WNS degradation > 50 ps
leaf cell increment > 15%
输入/软件转换已有更低成本替代
目标模型没有该模式的真实算子需求
```

预期重点：

- I4×FP8：产品硬件简单，但会使16-lane FP8路径全活跃；需看其增量是否主要来自 mode routing。
- I4×BF16：需要 8 products/cycle，可能增加输入选择和 fusion 网络。
- I8×BF16：没有额外 brick，但可能引入最宽 mixed routing。
- Special values：若训练/推理数据保证 finite，可默认关闭。

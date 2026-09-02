# VCS 累加后端验收

## 范围

本轮 VCS 不重复 v2 已完成的 product-pipe 穷举；它直接向三种 accumulator 输入同一组 `bf16_lane_item[4][4]`，补齐 v2 尚未完成的完整 reduction/recurrent accumulation RTL 回归。

## 用例

```text
items_per_lane = 1,2,4
K products/lane = 64,128,1024,4096
另加每种 items_per_lane 一个非64整倍数 tail-flush case
总计 15 cases
```

四个 lane 使用不同随机序列，其中一个 lane 注入周期性 outlier。

## 验收

```text
15 / 15 cases PASS
Full BF16 final raw bits exact
FP32 recurrent final raw bits exact
Block64 checkpoint final raw bits exact
protocol_error_o never asserted
所有 tail case观察到 flush_done_o
连续 valid beat 无丢失，II=1
```

reference由 `model/accum_v3_model.py` 生成，VCS 结果保存在：

```text
results/vcs_crosscheck_summary.csv
```

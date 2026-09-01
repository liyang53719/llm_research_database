# 架构比较规则

## 三类候选

1. `separate`：独立 INT 和 FP 算术，两边可并发；
2. `dual_domain`：动态模式 MUX，但算术仍独立；
3. `convert_fp` / `shared_native`：分别代表先转换复用 FP MAC，以及真正共享 magnitude/significand multiplier 并保留双累加域。

## 1/8、1/4、1/2 的正确解释

这些是 DSE sweep 的 scenario，不是模型测量值。定义：

```text
r = required_FP_peak / INT_main_peak
A_separate = A_INT + r*A_FP
A_hybrid = (1+h)*A_FP
r_break_even = 1+h-A_INT/A_FP
```

`h=0` 只是最乐观下界。当前下界门槛为 W4A8+FP8 73.2%、W8A8+FP8 61.0%、W4A8+BF16 79.8%、W8A8+BF16 70.5%。真实 `r` 需要由模型算子 trace、允许时延窗口和调度并发性求出。

## 数值结论

- INT4→FP8：精确；
- INT8→FP8：仅 80/256 代码精确，最大整数转换误差 4；
- INT4/INT8→BF16：精确。

## 公平面积比较

```text
A_separate = A_INT(required throughput) + A_FP(required throughput)
A_hybrid   = A_hybrid(matched throughput)
```

不得用 4-MAC/cycle 的 INT PE 和 1-MAC/cycle 的 FP PE 按“一个实例”直接排名。

## 删除项

`ALLFP32_*` 六组已删除；不再综合“全部输入先转 FP32 再进入 FP32 MAC”的明显非候选架构。

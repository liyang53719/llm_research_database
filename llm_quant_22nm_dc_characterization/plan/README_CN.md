# INT / FP 混合乘法器阵列 DSE

## 当前结论

- `W4A16` 的本地面积是 **INT4×INT16**，不是 `INT4×BF16`。
- 同一 Llama-3.1-8B MXFP 数据中，W4A16 与 W4A8 的准确度恢复率中位数约为 98.135% 与 98.190%，没有看到 A16 的稳定优势。
- 当前 1 GHz PE 的面积/MAC-cycle：W4A8 INT 100.28 µm²、W8A8 INT 154.93 µm²、W4A16 integer 210.71 µm²、FP8 E4M3 same-format 678.31 µm²；BF16 same-format 为 1373.92 µm²且未闭合 1 GHz。
- INT4 全部代码可精确转换到 E4M3；INT8 只有 80/256 可精确转换到 E4M3；INT4/INT8 均可精确转换到 BF16。

因此当前优先架构为：

```text
W4×A8 INT main array
+ W8×A8 sensitive-layer mode
+ right-sized FP8 tile
+ smaller/pipelined BF16 fallback tile
```

## 1/8、1/4、1/2 从哪里来

它们不是模型统计结果，而是原始 DSE 中用于扫参数的三个示例浮点峰值比例。严格定义：

```text
r = required_FP_peak_MAC_per_cycle / main_INT_array_peak_MAC_per_cycle
```

若独立架构按需求缩放浮点 Tile：

```text
A_separate = A_INT + r*A_FP
```

若全功能 hybrid 阵列覆盖整个主阵列，并令它相对纯 FP 单元的额外开销为 h：

```text
A_hybrid = (1+h)*A_FP
```

hybrid 的 break-even 条件为：

```text
r > 1 + h - A_INT/A_FP
```

取最乐观的 `h=0`，当前面积下界给出：

| 组合 | r 的 break-even 下限 |
|---|---:|
| W4A8 + FP8 | 73.2% |
| W8A8 + FP8 | 61.0% |
| W4A8 + BF16 | 79.8% |
| W8A8 + BF16 | 70.5% |

因此 1/8、1/4、1/2 只是低于上述门槛的示例点。真实 `r` 必须从模型/运行时 trace 计算：

```text
required_FP_peak = max_i(FP_MACs_in_window_i / allowed_time_i)
r = required_FP_peak / INT_main_peak
```

这里的 `r` 是峰值吞吐比，不等于浮点算子占总 MAC 比例，也不等于运行时间比例。

## 已删除 All-FP32 upper-bound

`ALLFP32_*` 六组已经从计划、工作簿和本地 DC 队列删除。FP32 累加仍保留在 `shared_native` 候选中，因为它是浮点累加合同，不是“所有输入都先转 FP32 再用 FP32 MAC”的架构。

## 沙箱完成内容

- E4M3/BF16 位级参考模型；
- INT4/INT8→FP8/BF16 精确覆盖验证；
- mixed dot 数值误差实验；
- separate、dual-domain、converter、shared-product RTL 候选；
- 21 个设计组、3 个周期，共 63 个本地 DC 点；
- area break-even 模型与结果格式。

## 边界

沙箱没有 22 nm `.db`、DC/DW 或 HDL simulator，因此 RTL 只完成源代码生成、Python 数值验证、Python 编译和静态结构检查。真正 PPA、DW 接口兼容性、subnormal/NaN 行为和流水时序由本地 Agent 完成。

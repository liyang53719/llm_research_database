# FusionMul16：16×4-bit Brick 可拼接 INT/FP 乘法阵列

## 1. 目标

实现并验证一套真正以 **16 个物理/逻辑 4×4 unsigned multiplier brick** 为唯一乘法资源的混合计算簇。所有模式只能消费这 16 个 brick 的输出，后级允许增加 partial-product fusion、符号、指数、归一化和累加逻辑，但禁止再推导第二套 8×8、16×16 或浮点乘法器。

目标模式：

| 模式 | 每个逻辑 product 使用的 4×4 brick | 每周期 product 数 |
|---|---:|---:|
| INT4×INT4 | 1 | 16 |
| INT4×INT8 | 2 | 8 |
| INT8×INT8 | 4 | 4 |
| INT16×INT16 | 16 | 1 |
| FP8 E4M3×FP8 E4M3 | 1 | 16 |
| BF16×BF16 | 4 | 4 |
| INT4×FP8 | 1 | 16 |
| INT8×FP8 | 2 | 8 |
| INT4×BF16 | 2 | 8 |
| INT8×BF16 | 4 | 4 |

FP4 不单独建立乘法模式，进入该簇前先转为 FP8 表示。

## 2. 与旧 shared_native 的区别

旧 `hybrid_shared_mul_dual_acc` 确实只有一个 8×8 multiplier operation，但它只能提供 **1 common product/cycle**。FusionMul16 改为 16 个 4×4 brick，通过 partial product 拼接改变吞吐：

```text
旧 shared_native：1 × 8×8 product/cycle
FusionMul16：
  16 × 4×4 product/cycle
   8 × 4×8 product/cycle
   4 × 8×8 product/cycle
   1 × 16×16 product/cycle
```

FP8 E4M3 的有效数为 4 bit，因此 product core 可以并行生成 16 个 FP8 product；BF16 有效数为 8 bit，因此可以生成 4 个 BF16 product。

## 3. 如何证明“真的共享”

证明分成四层：

1. `rtl/mul4x4_brick.sv` 是唯一包含乘法操作的文件；
2. `fusion_mul16_product_core.sv` 只有一个 `for (g=0; g<16)` 的 brick 实例阵列；
3. DC proof run 定义 `FUSION_USE_DW`，每个 brick 显式实例化一个 `DW_mult_uns #(4,4)`；
4. proof run 必须满足：

```text
brick_instance_count_precompile = 16
dw_mult_instance_count_precompile = 16
additional_multiplier_operations = 0
blackbox_count = 0
```

PPA run 可以 flatten，但 proof run 必须保留 brick hierarchy。两者使用同一 RTL 和相同功能测试。

## 4. 已在沙箱完成

- Python 位精确模型；
- INT4×INT4、INT4×INT8、INT8×INT8 穷举；
- INT16 边界与 5000 组随机；
- FP8×FP8、INT4×FP8、INT8×FP8 全空间验证；
- BF16 normal/subnormal/zero/Inf/NaN 分层验证；
- RTL 静态结构检查；
- 10 种模式、16-brick 使用数和产品吞吐检查；
- 11 个本地 DC 设计组、3 个公共周期，共 33 次综合计划；
- 2560 组跨模式 RTL 测试向量生成器。

沙箱没有 SystemVerilog compiler、CLN22UL `.db`、Design Compiler 和 DesignWare runtime，因此未宣称 RTL 已完成语法/仿真/DC 签核。

## 5. 当前面积门槛

使用已实测的 1 GHz 单元面积：

```text
W4A8 one-lane  = 242.788002 µm²
FP8 one-lane   = 245.700000 µm²
BF16 one-lane  = 628.901004 µm²
```

FusionMul16 匹配其模式峰值时，对应 separate reference：

| 匹配吞吐 | Separate 面积门槛 |
|---|---:|
| 8×W4A8 + 16×FP8 | 5873.504 µm² |
| 8×W4A8 + 16×FP8 + 4×BF16 | 8389.108 µm² |
| 保守 8×W4A8 + 4×FP8 + 4×BF16 | 5440.708 µm² |

这些只是面积筛选门槛，最终必须用本地相同吞吐、相同 accumulator、相同流水级的 RTL 综合结果比较。

## 6. 建议的物理组织

```text
FusionMul16 cluster
  ├─ 16 × 4×4 unsigned brick
  ├─ 4 × fusion lane，每 lane 4 bricks
  ├─ 4 × INT accumulator
  ├─ 4 × FP dot-product reduction
  └─ 4 × FP32 accumulator
```

FP8 模式下，每 fusion lane 形成一个 `dot4`，整个 cluster 每周期完成 16 个 product、输出 4 个 dot partial sum。BF16 模式下，每 lane 的 4 个 brick 组成一个 8×8 significand product。

## 7. 运行

```bash
cd llm_quant_22nm_dc_characterization/plan/fusion_mul16
python3 SOURCE_BUNDLE.py
python3 scripts/run_sandbox_validation.py
python3 scripts/gen_test_vectors.py
python3 scripts/gen_dc_runs.py
python3 scripts/run_dc.py --lib-setup ../config/library_setup.local.tcl --jobs 1
python3 scripts/collect_dc_results.py
python3 scripts/validate_dc_results.py
```

DC 并行数不得超过本地 license token 数。
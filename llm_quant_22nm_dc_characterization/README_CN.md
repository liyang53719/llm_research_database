# 22 nm DC / DesignWare 量化计算面积表征包

## 1. 结论：需要多少组数据

不能用单一工艺缩放系数把论文中的 45 nm、28 nm 或 FPGA 面积换成 22 nm“真实面积”。需要在同一套 22 nm `.db`、同一 operating condition、相同 I/O 约束和相同 compile mode 下重新综合。

本包定义两档：

| 档位 | 唯一设计组 | 公共时序点 | DC 运行数 | 作用 |
|---|---:|---:|---:|---|
| L1 最低可用 | 28 | 3 | 84 | 更新当前表格中的标准 INT/FP 格式、主要 W4A8/W8A8 PE 和基本 KV/量化逻辑 |
| L2 完整数据库 | 58 | 3 | 174 | 覆盖完整 W/A 网格、累加器敏感度、4 类阵列缩放和 KV/量化逻辑 |

另建议选择 6 个 anchor group 在第二套 Vt 或 PVT library 下复跑 3 个时序点，共 18 次，用于判断 library-set 敏感度；这 18 次不应和主比较组混在一起平均。

### L2 的 58 组构成

```text
20 组  整数 scalar MAC
        W∈{2,3,4,6,8,16}, A∈{4,8,16}
        + W5A5、W4A6 两个当前表格/候选专用点

 6 组  DesignWare floating MAC
        FP4 E2M1、FP6 E3M2、FP8 E4M3、FP8 E5M2、BF16、FP16

 6 组  accumulator width anchors
        W4A4、W4A8、W8A8 × N={16,256}
        N=64 已包含在 scalar MAC 中

 6 组  deployable PE
        dedicated W4A4/W4A8/W8A8/W4A16
        reconfig W4A4/W4A8/W8A8
        reconfig + scale/requant

12 组  registered systolic array
        W4A4、W4A8、W8A8、BF16 × {4×4,8×8,16×16}

 8 组  quantization / KV dequant logic
```

K/V 位宽不会改变主矩阵乘 MAC 阵列的乘法器面积，但会改变 KV cache 容量、attention 读取带宽、dequant logic 和 mode mux；因此它们单独记录。

## 2. “真实面积”的边界

DC `report_area` 给出的是 mapped standard-cell area：

```text
包含：组合单元、寄存器、buffer/inverter 等标准单元
不包含：SRAM macro、最终 floorplan utilization、CTS、routing blockage、wire area
```

因此结果列应命名为 `mapped_cell_area_um2`，不能直接叫 `final_die_area_um2`。

若要得到最终 core area，还需要：

```text
memory compiler 的 SRAM macro 面积
P&R 后的 utilization / whitespace
CTS 和 hold fixing
routing congestion
power grid / spare cell / DFT
```

## 3. 使用步骤

```bash
cd llm_quant_22nm_dc_characterization

cp config/library_setup.example.tcl config/library_setup.local.tcl
# 编辑 22nm .db 路径、operating condition、load/transition 和 compile mode

# 先做 8 组 smoke test；默认仍生成三个公共时序点
python3 scripts/gen_runs.py --tier L1 --smoke
scripts/run_capped.sh
python3 scripts/collect_results.py
python3 scripts/validate_results.py --tier L1 --smoke

# 最低可用：28组、84次
rm -rf build
python3 scripts/gen_runs.py --tier L1
scripts/run_capped.sh
python3 scripts/collect_results.py
python3 scripts/validate_results.py --tier L1

# 完整数据库：58组、174次
rm -rf build
python3 scripts/gen_runs.py --tier L2
scripts/run_capped.sh
python3 scripts/collect_results.py
python3 scripts/validate_results.py --tier L2
```

并行数不能超过本地 DC/DW license token 数。面积对比必须使用同一组公共 clock periods；某个 aggressive 点 timing fail 仍然保留，以形成 area/timing 曲线。

默认公共时序点：

```text
2.00 ns
1.00 ns (1 GHz target)
0.90 ns
```

它们只是初始 sweep，不是目标硬件边界。如果所有 anchor 全部通过或全部失败，统一修改 `config/characterization.json`，不要针对每个精度单独使用不同 clock period。

## 4. 回填数据库

```bash
python3 scripts/merge_to_sqlite.py \
  --base-db /path/to/llm_quantization_multidim_evidence.sqlite
```

输出：

```text
results/area_22nm_raw.csv
results/area_22nm_group_summary.csv
results/llm_quantization_with_22nm.sqlite
```

将 `area_22nm_raw.csv` 返回给上游后，可以写入 Excel 的 `13_22nm_Raw_Results`，并按 `scheme_to_group_map.csv` 更新方案矩阵。

## 5. 必须保持不变的比较合同

```text
target_library / link_library
operating condition
VT family
clock periods
input transition
output load
clock uncertainty
compile mode
hierarchy policy
RTL commit
DW version
```

改变其中任一项，都应产生新的 `library_set_id` 或 comparison group，不能与旧结果直接平均。

## 6. 不能直接替换的论文面积

DialectFP4、MANT、BitMoD、P3 和部分 QoQ/COMET 数字包含论文特有微架构。没有其完整 RTL 时，本包只能建立：

```text
DIRECT_KERNEL
DIRECT_COMPOSITE
SURROGATE_COMPOSITE
LOGIC_ONLY
PARTIAL
```

等映射，不能声称复现论文面积。原论文数据应保留，22 nm 本地数据作为独立 comparison group。


## 7. DesignWare 参考

本包的直接实例化接口以 Synopsys 官方示例为准：

```text
DesignWare Building Blocks:
https://www.synopsys.com/dw/buildingblock.php

DW02_mult example:
https://www.synopsys.com/dw/doc.php/doc/dwf/examples/DW02_mult_inst.v

DW_fp_mac example:
https://www.synopsys.com/dw/doc.php/doc/dwf/examples/DW_fp_mac_inst.v
```

实际本地版本的参数、状态位和 license 以已安装 DesignWare databook 为准。

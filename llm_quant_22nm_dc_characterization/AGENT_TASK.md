# 本地 Agent 执行合同

## 目标

用本地 22 nm standard-cell `.db`、Synopsys Design Compiler 和 DesignWare Foundation Library，生成可审计的 mapped-cell-area 数据，并回填量化多维数据库。

## 禁止事项

1. 不得用 `(22/45)^2` 或其他节点比例缩放论文面积。
2. 不得把 FPGA LUT/DSP 资源换算成 μm²。
3. 不得把不同 PVT、Vt、clock period 或 compile mode 的结果混成一个 comparison group。
4. 不得把 DC cell area 命名成 post-route core area。
5. 不得删除 timing-fail 点；它们是 area/timing 曲线的一部分。
6. 不得为某个精度单独放松 clock 约束后再宣称面积更小。

## 执行顺序

### Gate A：Library 与 DW 可用性

- `dc_shell` 能读取全部 22 nm `.db`；
- `dw_foundation.sldb` 可链接；
- `FP_MAC_BF16_E8M7` 的 `report_resources` 中出现 DW floating-point component；
- 无 unresolved reference / black box；
- `check_design` 无 fatal；
- `mapped_cell_area_um2 > 0`。

### Gate B：8 组 smoke test

运行：

```bash
python3 scripts/gen_runs.py --tier L1 --smoke
scripts/run_capped.sh
python3 scripts/collect_results.py
python3 scripts/validate_results.py --tier L1 --smoke
```

检查：

- 所有 summary.kv、report_area.rpt、report_qor.rpt 存在；
- relaxed period 至少一个点 timing met；
- W8A8 scalar 面积通常高于 W4A4；
- 16×16 array 面积高于 4×4；
- 若不满足，先检查常量传播、端口未使用、DW 未映射或时序约束错误。

### Gate C：L1 84 次

完成后生成：

```text
results/area_22nm_raw.csv
results/area_22nm_group_summary.csv
results/validation_report.txt
```

L1 验收：

- 28 个 group，每组 3 个 period；
- 84 行数据；
- blackbox_count = 0；
- 每个 group 至少有一个 timing-met 点，或明确记录需要扩展 relaxed period；
- 所有运行使用同一个 library_set_id。

### Gate D：L2 174 次

L2 验收：

- 58 个 group；
- 174 行数据；
- 相同 group 的 area 随 clock 收紧通常不下降；若下降需检查 DC 优化拓扑并保留报告；
- array `area / PE_count` 从 4×4 到 16×16 应趋于稳定；
- 任何非单调现象保留，不手工修数。

## 交付

返回整个 `results/` 目录，以及：

```text
config/library_setup.local.tcl
build/runs.csv
任意失败 run 的 dc_stdout.log
22nm std-cell library 名称和版本
DC/DW 版本
RTL 包 SHA-256
```

不要提交或外传 proprietary `.db`、`.lib`、DW 库文件。

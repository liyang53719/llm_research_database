# 本地 Agent 任务：FusionMul16 v4 最终 IP 验收

## 目标

对已冻结的 FusionMul16 v4 完成：

```text
完整 IP VCS
协议/延时 VCS
CLN22UL 1 GHz DC
brick/add resource proof
面积/时序/DRC 报告
```

不允许再替换 product pipe 或 accumulator 算术合同。

## 固定基线

```text
v2 product commit  041e6fc472422d57166f3489d3f62794c67fdea8
v3 accum commit     fd43c01dc9ab9fd364c5c1e4c6d99f64970ac130
v3 area reference   14043.211 µm²
```

环境：

```text
CLN22UL base SVT C35
TT typical_max
0.80 V
25°C
DC X-2025.06-SP3
DWBB X-2025.06-DWBB_202506.3
compile_ultra
clock 1.000 ns only
```

## Gate A：源代码与沙箱证据

```bash
PYTHONPATH=model python3 scripts/run_sandbox_validation.py
```

必须得到：

```text
full_input_domain_report.status = PASS
raw_pair_space_covered = 4312932352
literal_or_equivalence_checks >= 30200504
mismatches = 0
precision_sweep_report.status = PASS
unit tests = PASS
static RTL check = PASS
```

## Gate B：完整 IP VCS

```bash
PYTHONPATH=model python3 scripts/gen_vcs_vectors.py
python3 scripts/run_vcs.py --vcs vcs --dw-sim /path/to/DW/sim_ver
python3 scripts/run_vcs_protocol.py --vcs vcs --dw-sim /path/to/DW/sim_ver
```

必须满足：

```text
28/28 transaction cases PASS
7/7 modes covered
integer result latency = 4 registered stages
floating result latency = 7 registered stages
clear_done latency = 7 registered stages
II=1 continuous issue PASS
protocol directed test PASS
```

另对 `SUPPORT_SPECIALS=1, IEEE_COMPLIANCE=1` 增加 ±0、subnormal、Inf、NaN directed case，并记录 installed DW 的 status bits。

## Gate C：DC

```bash
python3 scripts/gen_dc_runs.py
python3 scripts/run_dc.py \
  --lib-setup /absolute/path/library_setup.local.tcl \
  --jobs 1
python3 scripts/collect_dc_results.py
python3 scripts/validate_dc_results.py
```

必须完成 12/12 个 1.000 ns group。

发布主组：

```text
V4_FINAL_DYNAMIC_FTZ
```

硬门槛：

```text
setup WNS >= 0
mapped_cell_area_um2 > 0
blackbox_count = 0
16 × 4×4 DW_mult_uns
0 additional multiplier
12 BF16 DW_fp_add
4 FP32 DW_fp_add
area <= 15447.532 µm²
```

`V4_FINAL_DYNAMIC_IEEE` 是特殊值/IEEE 成本数据，不阻塞低面积 inference profile，除非产品要求其作为默认配置。

## Gate D：报告不能隐藏的问题

必须解析并报告：

```text
setup WNS/TNS
hold WNS/TNS/count
high-fanout net count
max transition violations
max capacitance violations
unconstrained endpoints
check_design warnings
critical path startpoint/endpoint
combinational/sequential/total cell area
```

即使 `setup WNS >= 0`，小于 50 ps 的 margin 也必须标为 warning。DC mapped-cell closure 不能写成 physical signoff。

## 交付物

```text
results/vcs/vcs_summary.csv
results/vcs/protocol_summary.json
results/local_dc/v4_area_1ghz.csv
results/local_dc/validation_report.txt
results/local_dc/architecture_decision.json
results/local_dc/structure_proof.json
build_dc_1ghz/*/reports/
build_dc_1ghz/*/summary.kv
```

禁止上传 proprietary `.db/.lib/.sldb`、DDC、未脱敏绝对路径和主机名。

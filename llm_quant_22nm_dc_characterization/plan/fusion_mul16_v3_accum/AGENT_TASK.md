# 本地 Agent 任务：FusionMul16 v3 Accumulator DSE

## 目标

在不修改 FusionMul16 v2 product pipe 的前提下，对比三种累加后端：

```text
0 Full BF16
1 BF16 tree + 4×FP32 recurrent
2 BF16 Kblock64 partial + 4×FP32 checkpoint
```

## 基线

```text
Repository  liyang53719/llm_research_database
v2 commit  041e6fc472422d57166f3489d3f62794c67fdea8
v3 path    llm_quant_22nm_dc_characterization/plan/fusion_mul16_v3_accum
```

## 执行顺序

```bash
cd llm_quant_22nm_dc_characterization/plan/fusion_mul16_v3_accum

PYTHONPATH=model python3 scripts/run_sandbox_validation.py

# 完整 accumulator RTL；15 cases
python3 scripts/gen_vcs_vectors.py
python3 scripts/run_vcs_crosscheck.py --vcs vcs

# v2-root 指向 sibling fusion_mul16_v2
python3 scripts/gen_dc_runs.py \
  --v2-root ../fusion_mul16_v2 \
  --build-dir build_dc_1ghz

python3 scripts/run_dc.py \
  --build-dir build_dc_1ghz \
  --lib-setup ../config/library_setup.local.tcl \
  --jobs 1

python3 scripts/collect_dc_results.py \
  --build-dir build_dc_1ghz

python3 scripts/validate_dc_results.py
python3 scripts/build_architecture_decision.py
```

`--jobs` 不得超过 DC/DW license token 数。

## 必须返回

```text
results/vcs_crosscheck_summary.csv
results/local_dc/v3_area_1ghz.csv
results/local_dc/validation_report.txt
results/local_dc/v3_architecture_comparison.csv
results/local_dc/v3_architecture_decision.json
build_dc_1ghz/*/reports/
build_dc_1ghz/*/summary.kv
```

## 不允许

1. 修改 v2 product pipe 后仍声称只比较 accumulator。
2. 给 FP32 recurrent 添加 multicycle；它是每周期 recurrence，必须真实 1-cycle 闭合。
3. 将 block64 multicycle扩展到 BF16 tree或partial accumulator。
4. 删除 timing-fail 点。
5. 使用不同 clock period、library、PVT 或 compile mode比较面积。
6. 只验证 product pipe，不运行 15 个完整 accumulator VCS case。
7. 将 synthetic proxy 写成目标模型准确度。

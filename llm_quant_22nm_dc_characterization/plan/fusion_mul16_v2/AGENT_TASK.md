# 本地 Agent 交接：FusionMul16 v2 1 GHz Closure

## 固定环境

```text
CLN22UL base SVT C35
TT typical_max, 0.80 V, 25 °C
DC X-2025.06-SP3
DWBB X-2025.06-DWBB_202506.3
compile_ultra
clock period = 1.000 ns only
```

## 执行

```bash
python3 extract_source_bundle.py
python3 scripts/run_sandbox_validation.py
python3 scripts/gen_test_vectors.py --per-mode 512 --output results/rtl_vectors_v2.jsonl
python3 scripts/gen_vcs_vectors.py --per-mode 512
python3 scripts/run_vcs_crosscheck.py --per-mode 512
python3 scripts/gen_dc_runs.py
python3 scripts/run_dc.py --lib-setup ../config/library_setup.local.tcl --jobs 1
python3 scripts/collect_dc_results.py
python3 scripts/validate_dc_results.py
```

## 验收

- 20/20 Python tests PASS；
- 7 种模式 VCS product crosscheck 零失配；
- config beat 优先于 data beat，inflight 非空时禁止换 mode；
- 21 个 1 GHz DC run 完整；
- mapped area > 0、blackbox=0、DC error=0；
- 16 个 precompile brick、16 个 `DW_mult_uns #(4,4)`、额外 multiplier=0；
- `DW_fp_add #(23,8)` 数量为 0，只允许 BF16 `DW_fp_add #(7,8)`；
- 以下全部 WNS≥0：`V2_CORE_FULL7_FTZ`、`V2_SHARED_FULL7_FTZ`、`V2_SEPARATE_FULL_FTZ`、I4I8、I8I8、FP8-native、BF16-only；
- Shared 与 Separate 均过 1 GHz 后，才比较面积。

## P5 消融

分别报告 Base4、+I4FP8、+I4BF16、+I8BF16、+NaN/Inf 对 area、WNS、leaf cell 和 buffer area 的增量。单项面积增加超过10%或 WNS 恶化超过50 ps，列为默认关闭候选。

## 数值边界

默认浮点路径为 BF16 product/reduction/recurrent accumulation，subnormal output FTZ，`ieee_compliance=0`。必须用目标模型验证 K=64/128/256/1024 的累计误差；若失败，优先尝试 BF16 block partial sum + 共享高精度 checkpoint reduction，不恢复每个 product 的 FP32 展开与16个FP32加法器。

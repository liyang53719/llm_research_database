# FusionMul16 v2：1 GHz 定向优化

本目录基于 commit `e6d376784b3697f23a68127348460f8d203c9351`，针对 FusionMul16 v1 的 1 GHz 关键路径和面积主体重构。

主要变化：

- mode 改为 tile/config 状态，预译码并在数据进入前锁存；
- 输入改为两条 128-bit packed bus；
- 删除 W4A4、直接 INT16×INT16、INT8×FP8；INT16 由四次 INT8 partial product 时间累加；
- FP product 直接归一化到 BF16，不再产生 16×32-bit FP32 product register；
- 16 个 FP32 adder 改为 16 个 BF16 `DW_fp_add #(7,8,0)`；
- FP product path 增加流水，II=1；
- generic 32-bit normalizer 改为固定最大 16-bit normalizer；
- 使用 21 个仅 1.0 ns 的 DC 组做模式消融和 Shared/Separate 比较。

默认支持七种模式：I4×I8、I8×I8、FP8×FP8、BF16×BF16、I4×FP8、I4×BF16、I8×BF16。

沙箱结果：20/20 tests PASS；3584 个向量；向量 SHA-256 `2e83dec633b8b68125f80bcd93408caa7513e0ecdc7c77f4eefbfbcf16497a69`。

完整源码、测试、脚本和文档位于校验分片包。先执行：

```bash
python3 extract_source_bundle.py
python3 scripts/run_sandbox_validation.py
python3 scripts/gen_vcs_vectors.py --per-mode 512
python3 scripts/run_vcs_crosscheck.py --per-mode 512
python3 scripts/gen_dc_runs.py
python3 scripts/run_dc.py --lib-setup ../config/library_setup.local.tcl --jobs 1
python3 scripts/collect_dc_results.py
python3 scripts/validate_dc_results.py
```

DC 只运行 1.000 ns。`V2_SHARED_FULL7_FTZ` 与 `V2_SEPARATE_FULL_FTZ` 必须同时过时序，且 Shared 面积更小，才允许 `architecture_accept=true`。

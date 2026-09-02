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

沙箱结果：20/20 tests PASS；3584 个向量；bundle v2 SHA-256 `caf9a13d4bb2e1f58da214276eccf32e1c21cbfbb51788f82f4b25fafb144b65`。

完整源码、测试、脚本和文档位于校验分片包。先执行：

```bash
python3 extract_source_bundle.py
python3 scripts/run_vcs_crosscheck.py --per-mode 512
python3 scripts/gen_dc_runs.py
bash scripts/run_local_capped.sh /path/to/library_setup.local.tcl
python3 scripts/collect_dc_results.py
python3 scripts/validate_dc_results.py
```

本机执行约束固定为 CPU 8-23、单 DC run、最多两个 DC 执行核，并通过 cgroup 设置 `MemoryHigh=36G`、`MemoryMax=40G`、`MemorySwapMax=0`。DC 只运行 1.000 ns。

本次本地实测：20/20 Python tests PASS；3584 VCS product vectors 与 config protocol PASS；21/21 DC runs 完成且 `ERRORS=NONE`。Shared full 面积 11995.438 µm²、WNS +0.000069 ns；Separate full 面积 14214.291 µm²、WNS +0.000019 ns；`architecture_accept=true`。

完整结果见 `results/local_dc/LOCAL_EXECUTION_REPORT.md`，脱敏 DC 证据见 `evidence/runs/`。

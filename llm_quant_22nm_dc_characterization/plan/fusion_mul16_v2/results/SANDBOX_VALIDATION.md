# FusionMul16 v2 沙箱验证

```text
test_bf16_and_mixed_directed ... ok
test_fp8_products_exhaustive_to_bf16 ... ok
test_fp8_widen_to_bf16_is_exact ... ok
test_i4_fp8_exhaustive_to_bf16 ... ok
test_raw_normalizer_is_16_bit ... ok
test_i4_i8_exhaustive ... ok
test_i8_i8_exhaustive ... ok
test_int16_temporal_reference ... ok
test_removed_modes ... ok
test_configuration_precedes_data ... ok
test_fp_ii_one ... ok
test_integer_ii_one ... ok
test_bf16_not_fp32_accumulator ... ok
test_config_beat_has_priority_over_data ... ok
test_dc_is_1ghz_only ... ok
test_exactly_one_brick_generate_loop ... ok
test_mode_set_is_trimmed ... ok
test_module_delimiters ... ok
test_multiply_exists_only_in_brick ... ok
test_packed_interface_and_no_wide_fp_product ... ok

Ran 20 tests in 3.4 s
OK
```

## 汇总

- 单元测试：20/20 PASS
- 支持模式：7
- 生成 RTL 向量：3584
- 向量 SHA-256：`2e83dec633b8b68125f80bcd93408caa7513e0ecdc7c77f4eefbfbcf16497a69`
- DC 实验：21 个，仅 1.0 ns
- 乘法表达式：仅 `mul4x4_brick.sv`
- FP accumulator：仅 `DW_fp_add #(7,8,0)`
- FP32 adder：源码检查为 0
- 输入：2×128-bit packed bus
- 删除模式：I4I4、I16I16、I8FP8

## BF16 recurrent accumulation 随机研究

相对 FP64 reference：

| 输入代理 | K | NRMSE | 过滤后 p99 相对误差 |
|---|---:|---:|---:|
| FP8-like | 128 | 0.758% | 5.48% |
| FP8-like | 1024 | 1.990% | 9.30% |
| BF16 | 128 | 0.736% | 4.57% |
| BF16 | 1024 | 1.761% | 11.07% |

这些不是目标模型准确度结论。若目标模型回归失败，优先测试 BF16 block partial sum + 共享高精度 checkpoint reduction，不恢复每 product FP32 展开和 16 个 FP32 adder。

## 尚未完成

- 本地 VCS 语法与跨模式向量仿真；
- 本地 DesignWare 参数/状态位核对；
- CLN22UL 1 GHz DC 综合；
- Formality、门级仿真和 P&R；
- 目标模型准确度。

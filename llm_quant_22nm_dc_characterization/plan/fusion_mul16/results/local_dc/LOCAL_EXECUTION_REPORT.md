# FusionMul16 本地执行报告

## 结论

- 17/17 沙箱单元测试通过；10 种模式共 505,056 对输入、851,468 项 RTL 检查，零失配。
- 11 组/33 次 DC 扫描完整，1 GHz 达标 4/11。
- 16-brick proof：PASS；预编译 brick=16，DW 4x4 multiplier=16，额外 multiplier=0。
- 架构决策：`rejected_by_measured_core_gate`。
- FP accumulator 使用 `DW_fp_add #(23,8,0)`；是否接受 denormal 行为必须由模型精度合同确认，因此不会把该条件冒充已验收。

## 固定综合合同

- CLN22UL SVT C35, TT typical_max, 0.80 V, 25 C
- DC X-2025.06-SP3 / DWBB X-2025.06-DWBB_202506.3
- compile_ultra；2.0 ns / 1.0 ns / 0.9 ns
- CPU 8-23；单 DC、单执行核；cgroup MemoryHigh=36 GiB / MemoryMax=40 GiB

## 1 GHz 结果

| Group | Area (µm²) | WNS (ns) | Timing |
|---|---:|---:|---:|
| BRICK16_BARE_PROOF | 222.859000 | 0.776135 | 1 |
| FUSION16_BF16_ONLY_PIPE | 7202.104000 | 0.000034 | 1 |
| FUSION16_CORE_PPA | 8665.748000 | -0.012230 | 0 |
| FUSION16_CORE_PROOF | 4991.623000 | -1.381810 | 0 |
| FUSION16_DUAL_SHARED_PIPE | 45222.359000 | -0.129555 | 0 |
| FUSION16_FP8_ONLY_PIPE | 14936.922000 | -0.036111 | 0 |
| FUSION16_FP_ACC_ONLY | 15371.811000 | -0.169111 | 0 |
| FUSION16_INT_ACC_ONLY | 2198.742000 | 0.000525 | 1 |
| FUSION16_INT_ONLY_PIPE | 4131.218000 | 0.000040 | 1 |
| FUSION16_SEPARATE_FULL_PIPE | 27912.885000 | -0.008636 | 0 |
| FUSION16_SHARED_FULL_PIPE | 23201.815000 | -0.100014 | 0 |

## 同吞吐与并发比较

| Architecture | Area @1GHz (µm²) | Concurrent modes | Throughput contract | Dominated |
|---|---:|---:|---|---:|
| FUSION16_SHARED_FULL_PIPE | 23201.815000 | 1 | exclusive_mode_match | 0 |
| FUSION16_DUAL_SHARED_PIPE | 45222.359000 | 2 | partial_concurrency_match | 0 |
| FUSION16_SEPARATE_FULL_PIPE | 27912.885000 | 3 | full_concurrency_reference | 1 |
| RIGHT_SIZED_DEDICATED_SUM | 26270.244000 | 3 | full_concurrency_component_sum | 0 |

## 验证边界

- 已完成 RTL product 全空间/分层仿真、官方 DW_fp_add 顶层展开、valid 延迟检查、DC elaboration 结构证明和 mapped PPA。
- 未执行 Formality、post-synthesis gate simulation 或 place-and-route；这些不属于本次 DC 结果的已测边界。
- `partial_concurrency_match` 不等于 full three-mode concurrency；表中明确保留该差异。

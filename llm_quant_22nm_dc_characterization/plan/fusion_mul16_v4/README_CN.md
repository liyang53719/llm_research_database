# FusionMul16 v4 Final IP

FusionMul16 v4 将两条已经本地表征过的数据通路冻结为一个可交付 IP：

```text
FusionMul16 v2 shared 16×4-bit product pipe
+ v3 BF16 pair/lane tree
+ 4×FP32 recurrent accumulator
```

## 支持模式

```text
0  INT4 × INT8
1  INT8 × INT8
2  FP8 E4M3FN × FP8 E4M3FN
3  BF16 × BF16
4  INT4 × FP8 E4M3FN
5  INT4 × BF16
6  INT8 × BF16
```

直接 INT16×INT16 已删除；需要时由四次 INT8×INT8 partial product 在时间上累加。

## 核心资源合同

```text
16 × unsigned 4×4 multiplier brick
12 × BF16 DW_fp_add for pair/lane reduction
 4 × FP32 DW_fp_add for recurrent accumulation
 4 × signed INT48 recurrent accumulator
```

所有模式共享同一组 16 个 brick；RTL 中没有 `DW_fp_mult`。最终是否保持 16 个 mapped multiplier operation，由本地 DC proof gate 再确认。

## 接口与时序

```text
Input payload       128-bit lhs + 128-bit rhs
Integer latency     4 registered stages
Floating latency    7 registered stages
Clear completion    7 registered stages
Initiation interval 1
Rounding            RNE only
```

动态模式由 config channel 在 tile 之前锁存。配置后和每个 `last_i` 后，下一事务前必须发一个独立 `clear_i` beat。`clear_i` 不与数据同拍；数据可在 clear 后一拍开始，无需等待 `clear_done_o`。

详细端口、packing 和输出时序见：

```text
docs/IP_SPEC.md
docs/PORTS.csv
docs/MODE_TABLE.csv
docs/LATENCY.md
docs/NUMERIC_CONTRACT.md
```

## 验证结果

```text
Scalar raw-pair space covered     4,312,932,352
Executed literal/equivalence checks 30,200,504
Product mismatches                0
Long-K precision rows             100
Precision proxy gate              PASS
Python/unit/structure tests       19/19 PASS
Full-IP VCS cases                 28/28 PASS
Protocol VCS                      PASS
1GHz DC groups                    12/12 PASS
```

BF16×BF16 的 2^32 raw pair 没有伪装成逐对暴力循环。它通过完整的 sign/significand-product/scale-sum 等价类证明覆盖所有 raw pair。

K=4096 synthetic arithmetic proxy 的最差结果：

```text
max NRMSE among five FP/mixed modes     0.212%
max filtered P99 among five modes       2.677%
```

这些是算术微基准，不是目标模型准确率。目标模型的逐层、logit、perplexity 和任务回归仍需单独完成。

`V4_FINAL_DYNAMIC_FTZ` 已通过 release gate：映射面积 14277.900 µm²，setup WNS +0.0000177026 ns，16 个 4×4 `DW_mult_uns`、12 个 BF16 add、4 个 FP32 add、blackbox=0。相对 v3 选定版本 14043.211 µm²，面积增加约 1.67%，低于 +10% 预算。

`V4_FINAL_DYNAMIC_IEEE` 作为可选特殊值/IEEE profile 保留；该 profile 在同一 1 GHz 角落 setup 未闭合（WNS -0.0663595 ns），不阻塞 inference FTZ profile。所有近零 setup margin、pre-layout hold 和 high-fanout 警告均保留在 `results/local_dc/validation_report.txt` 和 `results/local_dc/LOCAL_EXECUTION_REPORT.md`。

本地执行固定使用 CPU 8–23、单 DC job/core、MemoryMax=40G，未发生 OOM。发布时会移除绝对路径、hostname、专有库、DDC 和网表。

## 在沙箱中复现

```bash
cd fusion_mul16_v4_final

PYTHONPATH=model python3 scripts/run_full_domain_scan.py
PYTHONPATH=model python3 model/precision_sweep.py --output-dir results
PYTHONPATH=model python3 scripts/gen_vcs_vectors.py
python3 scripts/gen_dc_runs.py
python3 scripts/static_rtl_check.py
PYTHONPATH=model python3 -m unittest discover -s tests -v
```

`run_sandbox_validation.py` 会一次执行全部步骤。

## 本地执行

本地具备 VCS、DC、DW 和 CLN22UL library 后执行：

```bash
python3 scripts/run_vcs.py --vcs vcs --dw-sim /path/to/DW/sim_ver
python3 scripts/run_vcs_protocol.py --vcs vcs --dw-sim /path/to/DW/sim_ver

python3 scripts/gen_dc_runs.py
python3 scripts/run_dc.py \
  --lib-setup /path/to/library_setup.local.tcl \
  --jobs 1
python3 scripts/collect_dc_results.py
python3 scripts/validate_dc_results.py
```

详见 `AGENT_TASK.md` 和 `docs/DC_ACCEPTANCE.md`。

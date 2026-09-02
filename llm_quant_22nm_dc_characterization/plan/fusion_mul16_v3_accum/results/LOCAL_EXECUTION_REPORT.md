# FusionMul16 v3 local execution report

## Acceptance

- PVT: CLN22UL base SVT C35 TT typical_max, 0.80 V, 25 C.
- DC: X-2025.06-SP3, compile_ultra, clock period 1.000 ns only.
- Resource policy: CPU 8-23, one DC job, one DC host core, systemd cgroup MemoryMax=40G, no OOM observed.
- Python: 20/20 tests PASS; VCS: 15/15 cases PASS; DC: 12/12 runs returned rc=0.
- DC validation: NONE

## 1 GHz DC results

| Group | Area (um2) | WNS (ns) | BF16 adders | FP32 adders | MC |
|---|---:|---:|---:|---:|---:|
| V3_ACC_BLOCK64_FP32_CKPT | 9486.022 | 1.04904e-05 | 16 | 4 | 1 |
| V3_ACC_FULL_BF16 | 6118.749 | 1.78814e-05 | 16 | 0 | 0 |
| V3_ACC_TREE_FP32_REC | 8864.674 | 0 | 12 | 4 | 0 |
| V3_BF16_BLOCK64_FP32_CKPT_FIXED | 6513.598 | 2.88486e-05 | 16 | 4 | 1 |
| V3_BF16_FULL_BF16_FIXED | 3290.469 | 3.18885e-05 | 16 | 0 | 0 |
| V3_BF16_TREE_FP32_REC_FIXED | 5658.926 | 7.92742e-06 | 12 | 4 | 0 |
| V3_CLUSTER_BLOCK64_FP32_CKPT_FULL7 | 14869.491 | 2.68221e-06 | 16 | 4 | 1 |
| V3_CLUSTER_FULL_BF16_FULL7 | 11781.133 | 1.92523e-05 | 16 | 0 | 0 |
| V3_CLUSTER_TREE_FP32_REC_FULL7 | 14043.211 | 7.98702e-06 | 12 | 4 | 0 |
| V3_FP8_BLOCK64_FP32_CKPT_FIXED | 11620.336 | 1.0848e-05 | 16 | 4 | 1 |
| V3_FP8_FULL_BF16_FIXED | 8425.235 | 1.20997e-05 | 16 | 0 | 0 |
| V3_FP8_TREE_FP32_REC_FIXED | 10889.060 | 3.52859e-05 | 12 | 4 | 0 |

## P5 selection

- P5 compares the two v2 reproduction references and all three v3 full-cluster accumulator backends under the same 1 GHz/PVT/compile setup.
- Full BF16 is timing-closed but fails the synthetic K=4096 gate.
- BF16 tree + FP32 recurrent and BF16 Kblock64 + FP32 checkpoint pass the synthetic gate; the former has the smaller full-cluster area and is the provisional selection.
- Target-model layer/logit/perplexity/task accuracy is OPEN; synthetic proxy is not final model signoff.

## Structural and multicycle proof

- The v2 product pipe, 16x4-bit brick and packed interface are reused; no accumulator source contains DW_fp_mult or an extra multiply operator.
- Common tree: 12 BF16 adders. Style 0: 4 BF16 recurrent adders. Style 1: 4 FP32 recurrent adders. Style 2: 4 BF16 partial + 4 FP32 checkpoint adders.
- Style 1 has no multicycle exception and must close a real one-cycle FP32 recurrence (observed 1 GHz timing_met=1).
- Style 2 applies only setup=2/hold=1 to checkpoint register paths; the mapped checkpoint report contains Q-to-next_state paths and no product-tree/partial exception.
- RTL holds checkpoint operands in named base/term registers and enables checkpoint_fp32_o only when the wait counter reaches its terminal bit; stream II remains 1.

## Evidence checks

- dc_runs: PASS
- vcs_cases: PASS
- dc_errors: PASS
- blackboxes: PASS
- all_timing_closed: PASS
- checkpoint_mc2_only: PASS
- checkpoint_reports_have_paths: PASS
- no_accumulator_multiplier: PASS
- v2_product_pipe_sha_present: PASS

## Baseline reproduction

- V3_ACC_FULL_BF16 = 6118.749 um2 vs v2 reference 6270.992 um2 (-2.428%).
- V3_CLUSTER_FULL_BF16_FULL7 = 11781.133 um2 vs v2 reference 11995.438 um2 (-1.787%).
- Both deviations are within the configured +/-5% reproduction tolerance.

## Public-data boundary

- Raw DC logs, generated netlists/DDC, licensed .db/.lib/.sldb files and local absolute paths are excluded from the public upload.
- Public evidence keeps summaries, reports, hashes and reproducible scripts after path/host sanitization.

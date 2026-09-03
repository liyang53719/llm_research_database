# FusionMul16 v4 local execution report

## Gate summary

- Sandbox: full raw-pair/equivalence coverage PASS (4,312,932,352 pairs; 30,200,504 checks; 0 mismatches).
- VCS: 28/28 complete-IP transaction cases PASS; protocol PASS=True
- DC: 12/12 groups completed at CLN22UL TT 0.80 V/25 C, 1.000 ns, compile_ultra.
- Runtime policy: CPU 8-23, one DC job/core, cgroup MemoryMax=40G, no OOM observed.
- Physical signoff is OPEN; these are mapped-cell synthesis results.

## DC results

| Group | Area (um2) | Setup WNS (ns) | Hold WNS (ns) | Hold count | Fanout nets | BF16 add | FP32 add |
|---|---:|---:|---:|---:|---:|---:|---:|
| V4_ACCUM_BF16TREE_FP32REC | 8603.049 | 1.43051e-05 | 0.0 | 0.0 | 0 | 12 | 4 |
| V4_BRICK16_PROOF | 309.946 | 0.37207 | 0.0 | 0.0 | 0 | 0 | 0 |
| V4_FINAL_DYNAMIC_FTZ | 14277.900 | 1.77026e-05 | -0.02 | 1.0 | 1.0 | 12 | 4 |
| V4_FINAL_DYNAMIC_IEEE | 16440.515 | -0.0663595 | -0.02 | 1.0 | 1.0 | 12 | 4 |
| V4_FIXED_BF16_BF16 | 6134.037 | 5.00679e-06 | -0.02 | 44.0 | 0 | 12 | 4 |
| V4_FIXED_FP8_FP8 | 11268.712 | 2.43783e-05 | -0.02 | 11.0 | 1.0 | 12 | 4 |
| V4_FIXED_I4_BF16 | 8081.073 | 0 | -0.02 | 27.0 | 1.0 | 12 | 4 |
| V4_FIXED_I4_FP8 | 11035.843 | 9.65595e-06 | -0.02 | 11.0 | 1.0 | 12 | 4 |
| V4_FIXED_I4_I8 | 2235.779 | 0.00146741 | 0.0 | 0.0 | 0 | 0 | 0 |
| V4_FIXED_I8_BF16 | 5980.520 | 2.8193e-05 | -0.02 | 44.0 | 0 | 12 | 4 |
| V4_FIXED_I8_I8 | 2068.612 | 0.000625134 | 0.0 | 0.0 | 0 | 0 | 0 |
| V4_PRODUCT_PIPE_FULL7_FTZ | 4962.867 | 6.90818e-05 | 0.0 | 0.0 | 1.0 | 0 | 0 |

## Release decision

- Release profile: `V4_FINAL_DYNAMIC_FTZ`; status `PASS`.
- V4_FINAL_DYNAMIC_FTZ is the hard inference gate: setup WNS is non-negative, area is within the +10% v3 budget, 16 DW_mult_uns 4x4 operations, 12 BF16 adders, 4 FP32 adders, and no black boxes.
- V4_FINAL_DYNAMIC_IEEE is optional special/IEEE characterization. It is retained as data and does not block the inference profile; it misses the hard 1 GHz setup gate at this library corner.
- Warnings are retained: near-zero setup margin (<50 ps) and pre-layout hold violations. They are not physical-signoff claims.
- Target-model layer/logit/perplexity/task accuracy remains OPEN; precision results are synthetic arithmetic proxy only.

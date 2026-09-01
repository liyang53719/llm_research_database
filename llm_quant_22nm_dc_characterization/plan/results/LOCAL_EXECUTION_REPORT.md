# Local mixed INT/FP execution report

## Acceptance

- Baseline: 21 groups / 63 DC runs; validation ERRORS=NONE.
- Pipeline follow-up: 10 groups / 30 DC runs; validation ERRORS=NONE.
- PVT: CLN22UL SVT C35 TT typical_max, 0.80 V, 25 C.
- Periods: 2.0 ns, 1.0 ns, 0.9 ns; compile_ultra.
- Black boxes: 0 across all 93 runs.
- 1 GHz timing met: baseline 7/21; pipeline follow-up 9/10.
- Numeric RTL: 73,984 exhaustive integer checks and 6,153 directed/stratified FP checks, zero failures.
- Actual DW_fp_i2flt simulation: 544/544 raw-code conversions matched the Python reference.

## Key 1 GHz pipeline results

| Group | Area (um2) | WNS (ns) | Met |
|---|---:|---:|---:|
| PIPE2_CONV_I4_BF16 | 749.931003 | 0.000199854 | 1 |
| PIPE2_CONV_I8_BF16 | 780.871003 | 0.000123322 | 1 |
| PIPE_ARRAY4_DUAL_W4A8_FP8 | 7833.098036 | 0.000017166 | 1 |
| PIPE_ARRAY4_SEP_W4A8_FP8 | 7821.996036 | 0.000009239 | 1 |
| PIPE_CONV_I4_BF16 | 1482.663015 | -0.156852000 | 0 |
| PIPE_CONV_I4_FP8 | 713.258006 | 0.000028014 | 1 |
| PIPE_MIXREF_BF16 | 628.901004 | 0.000584006 | 1 |
| PIPE_MIXREF_FP8 | 245.700000 | 0.000653625 | 1 |
| PIPE_MIXREF_INT_W4A8_L1 | 242.788002 | 0.000032067 | 1 |
| PIPE_SHARED_NATIVE_ALL_DUALACC | 2027.389016 | 0.000180244 | 1 |

## Matched-throughput array conclusion

- One-lane W4A8 INT cell: 242.788002 um2 at 1 GHz.
- Pipelined FP8 cell: 245.700000 um2 at 1 GHz.
- Measured separate 4x4 cell-equivalent: 488.874752 um2.
- Measured exclusive dual 4x4 cell-equivalent: 489.568627 um2.
- Separate cell agrees with component sum within 0.079%.
- Dual cell is 0.142% larger than the simultaneous separate cell while not supporting simultaneous INT+FP.
- Under exclusive-window scheduling, dual break-even requires r > 1.004398.
- Therefore for 0 <= r <= 1, the measured dual cell does not beat a right-sized separate INT+FP tile on area.

## Numeric and architecture boundaries

- INT4->FP8 and INT4/INT8->BF16 conversions are exact for all source codes.
- INT8->FP8 is lossy: 80/256 exact codes, maximum source-value error 4.
- PIPE1 I4->BF16 did not close 1 GHz; PIPE2 registered multiply/add variants for I4 and I8 did close.
- shared-native comparisons remain partial-throughput comparisons, not equivalent to simultaneous separate arithmetic.
- Timing-fail and non-monotonic points remain in raw results.

## Missing external input

No target-model operator/window trace or allowed-time file was provided. The real required FP peak ratio r cannot be measured here. Scenario sweeps remain scenarios, not model conclusions.

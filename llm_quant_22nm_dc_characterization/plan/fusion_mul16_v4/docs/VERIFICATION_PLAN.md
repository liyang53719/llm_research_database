# Verification plan

## Sandbox gates

1. Compile all Python sources.
2. Run 19+ unit/structural tests.
3. Run full scalar input-domain scan: zero mismatch.
4. Run 100 long-K precision cases: synthetic gate pass.
5. Generate 28 full-IP transaction VCS cases.
6. Generate 12 one-GHz DC groups.

## Local VCS gates

- Compile the full IP with the installed DesignWare simulation models.
- Execute all 28 finite transaction cases.
- Check final four-lane accumulator values and exact `last` alignment.
- Check integer registered-stage latency 4, floating latency 7 and clear latency 7.
- Continuous input must maintain II=1.
- `protocol_error_o` and `cfg_error_o` must remain zero in legal tests.
- Add directed illegal protocol tests: data before clear, valid+clear, last without valid, config while busy.
- Add optional IEEE-profile special tests for ±0, BF16 subnormal, ±Inf and NaN.

## Local DC gates

See `DC_ACCEPTANCE.md`. The release decision is based on `V4_FINAL_DYNAMIC_FTZ`; fixed-mode groups are characterization data, not substitutes for the dynamic-area result.

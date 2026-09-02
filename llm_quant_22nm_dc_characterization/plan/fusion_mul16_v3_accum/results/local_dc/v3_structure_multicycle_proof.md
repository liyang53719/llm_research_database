# FusionMul16 v3 structure and multicycle proof

## Static RTL contract

- `fusion_mul16_v3_bf16_tree_dw.sv`: three `DW_fp_add #(7,8,0)` instances in a four-lane generate loop, therefore 12 BF16 adders.
- `fusion_mul16_v3_accum_full_bf16_dw.sv`: one generated BF16 recurrent adder per lane, therefore 4 BF16 adders.
- `fusion_mul16_v3_accum_fp32_recurrent_dw.sv`: one generated `DW_fp_add #(23,8,0)` per lane, therefore 4 FP32 recurrent adders; no multicycle constraint is supplied.
- `fusion_mul16_v3_accum_block64_fp32_checkpoint_dw.sv`: one generated BF16 partial and one FP32 checkpoint adder per lane; named `checkpoint_base_q`, `checkpoint_term_q` and `checkpoint_fp32_o` state is held across the wait counter.
- The checkpoint output update is guarded by `checkpoint_wait_q[WAIT_W-1]`, while a boundary/flush loads the operands and starts the wait counter. This is the RTL evidence for destination enable on the second edge and operand stability.
- Accumulator RTL contains no `DW_fp_mult` and no additional multiply operator; the only multiply source file is the reused v2 `mul4x4_brick.sv`.

## Mapped DC evidence

- Block64 runs with `set_multicycle_path` lines in exported SDC: 2 per run (setup=2, hold=1).
- Non-block runs with multicycle lines in exported SDC: {0} (expected {0}).
- All four block64 `report_exceptions.rpt` files contain the supported Q-to-next_state checkpoint timing report. DC X-2025.06-SP3 has no `report_exceptions` command, so the report records that limitation and embeds `report_constraint -verbose` plus the supported timing paths.
- No block64 DC log contains TIM-179/UID-119 stale-object warnings after state preservation.
- Product tree and BF16 partial paths have no multicycle commands in the generated SDC.

## Scope boundary

- This is a synthesis/structural proof at the stated 1 GHz setup. Physical signoff and target-model layer/logit accuracy remain outside this run.

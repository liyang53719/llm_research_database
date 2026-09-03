# FusionMul16 v4 IP specification

## Purpose

FusionMul16 v4 is a four-lane mixed-precision dot-product cluster. It combines the locked FusionMul16 v2 shared product pipeline with the v3-selected BF16 reduction tree and four FP32 recurrent accumulators.

## Main resources

```text
16 x unsigned 4x4 multiplier brick
4  x integer recurrent accumulator, default INT48
12 x BF16 add in pair/lane reduction tree
4  x FP32 recurrent add
128-bit packed left input
128-bit packed right input
```

No `DW_fp_mult` and no extra 8x8/16x16 multiplier are permitted. Local DC structural proof must report exactly sixteen 4x4 multiplier instances for the dynamic final profile.

## Protocol

1. After reset, a dynamic-mode instance requires configuration.
2. Assert `cfg_valid_i` with a supported mode while `cfg_ready_o=1`.
3. Send one standalone `clear_i` beat before the first data beat after configuration.
4. Data may start on the cycle immediately after the accepted clear beat; the fixed-latency pipeline preserves clear-before-data ordering. Waiting for `clear_done_o` is allowed but not required.
5. Drive data with `valid_i && in_ready_o`; `clear_i` must be zero.
6. Assert `last_i` on the final accepted data beat.
7. Wait for `int_last_o` or `fp_last_o`; output accumulator data on that edge is the completed result.
8. Before another transaction, send a standalone clear. A data beat before clear raises `protocol_error_o` and is not accepted.
9. Reconfiguration is allowed only when `cfg_ready_o=1`, meaning the accepted-event pipeline is empty.

`clear_i` and `valid_i` asserted together are illegal. `last_i` without `valid_i` is illegal.

## Outputs

Integer and floating accumulator banks exist simultaneously, but only the active domain updates for a configured mode. Results remain held until reset, a clear beat, or the next accepted update in that domain.

## Parameters

| Parameter | Default | Meaning |
|---|---:|---|
| `INT_ACC_W` | 48 | Width of each signed integer recurrent accumulator |
| `FIXED_MODE` | -1 | Dynamic mode when -1; otherwise elaboration-time fixed mode 0..6 |
| `SUPPORT_FP8` | 1 | Enable FP8xFP8 routing |
| `SUPPORT_BF16` | 1 | Enable BF16xBF16 routing |
| `SUPPORT_I4_FP8` | 1 | Enable I4xFP8 |
| `SUPPORT_I4_BF16` | 1 | Enable I4xBF16 |
| `SUPPORT_I8_BF16` | 1 | Enable I8xBF16 |
| `SUPPORT_SPECIALS` | 0 | Product-level NaN/Inf handling; release inference profile leaves them illegal |
| `IEEE_COMPLIANCE` | 0 | Passed to DesignWare BF16/FP32 adders |

See `PORTS.csv`, `MODE_TABLE.csv`, `LATENCY.md`, and `NUMERIC_CONTRACT.md` for the normative interface and arithmetic contract.

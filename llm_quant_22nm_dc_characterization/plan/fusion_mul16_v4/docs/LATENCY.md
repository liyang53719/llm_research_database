# FusionMul16 v4 latency and throughput contract

## Definition

A beat is accepted at rising edge `E0` when `valid_i && in_ready_o && !clear_i` is true.
The table counts the accepting register boundary as stage 1. Equivalently, an output becomes visible after the stated edge delta.

| Event | Registered stages | Output edge | II |
|---|---:|---:|---:|
| Integer accumulator update | 4 | `E0 + 3*Tclk` | 1 |
| Floating FP32 accumulator update | 7 | `E0 + 6*Tclk` | 1 |
| Integer `last` | 4 | Same edge as integer update | 1 |
| Floating `last` | 7 | Same edge as floating update | 1 |
| Standalone clear completion | 7 | `E0 + 6*Tclk` | control beat |
| Accepted configuration becomes active | 1 | next cycle | control beat |

The floating path is:

```text
S0 route/unpack
S1 sixteen 4x4 multiplier bricks
S2 partial-product/significand fusion
S3 raw16-to-BF16 RNE/FTZ packing
S4 BF16 pair add
S5 BF16 lane add
S6 FP32 recurrent accumulator update
```

The integer path bypasses S3-S5 and updates its four INT accumulators after the fused integer lane sums.

## Throughput at 1 GHz

| Mode | Products/cycle | Nominal products/s | Lane partials/cycle |
|---|---:|---:|---:|
| I4xI8 | 8 | 8 Gproduct/s | 4 |
| I8xI8 | 4 | 4 Gproduct/s | 4 |
| FP8xFP8 | 16 | 16 Gproduct/s | 4 dot4 |
| BF16xBF16 | 4 | 4 Gproduct/s | 4 |
| I4xFP8 | 16 | 16 Gproduct/s | 4 dot4 |
| I4xBF16 | 8 | 8 Gproduct/s | 4 dot2 |
| I8xBF16 | 4 | 4 Gproduct/s | 4 |

A product is one multiplication. Converting to operations/s by counting multiply and add as two operations is a separate reporting convention.

## Clear/data overlap

A standalone clear accepted at `E0` and a data beat accepted at `E0+Tclk` remain ordered through both integer and floating pipelines. The accumulator sees clear one cycle before the following update. Therefore the source may issue data on the cycle immediately after clear; `clear_done_o` is a completion/observability pulse and a conservative reconfiguration barrier, not a requirement for starting data.

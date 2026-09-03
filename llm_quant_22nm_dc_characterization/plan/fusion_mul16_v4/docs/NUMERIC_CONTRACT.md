# Numeric contract

## Integer modes

- Inputs are signed two's-complement INT4/INT8.
- Products and lane reductions are exact.
- Four recurrent accumulators default to signed 48 bit.
- Overflow wraps in two's-complement form; no saturation is implemented.

## Floating and mixed modes

1. FP8 uses finite E4M3FN encoding with one NaN code per sign and no infinity encoding.
2. BF16 uses sign/E8/M7 encoding.
3. INT4/INT8 magnitudes and FP significands share exactly sixteen unsigned 4x4 multiplier bricks.
4. Every product is rounded RNE to BF16 by `fusion_mul16_v4_raw16_to_bf16_rne`.
5. Underflow below the minimum BF16 normal is flushed to signed zero before rounding.
6. Per lane, up to four products are reduced by a two-stage BF16 tree.
7. The BF16 lane sum is widened exactly to FP32.
8. Four FP32 recurrent accumulators update every valid lane sum. No multicycle exception is allowed on this recurrence.
9. Rounding mode is fixed to RNE (`3'b000`) in the final IP.

## Release profiles

`V4_FINAL_DYNAMIC_FTZ` is the release PPA profile:

```text
SUPPORT_SPECIALS=0
IEEE_COMPLIANCE=0
```

NaN and infinity inputs are illegal in this profile. All finite input codes, including BF16 subnormals, are covered by the product-domain scan.

`V4_FINAL_DYNAMIC_IEEE` is an optional characterization profile:

```text
SUPPORT_SPECIALS=1
IEEE_COMPLIANCE=1
```

The full raw-code product-domain proof includes zero, subnormal, normal, infinity and NaN categories. Final DW special/status behavior must be confirmed by local VCS against the installed DesignWare version.

## Evidence boundary

The exhaustive product scan covers every scalar raw pair in all seven modes. Arbitrary accumulator sequences are unbounded; accumulation is verified with bounded transaction tests and long-K Gaussian, positive, cancellation and outlier distributions. Target-model layer/logit/perplexity/task accuracy remains a separate signoff gate.

# Complete scalar input-domain coverage

The scan covers a raw-pair space of **4,312,932,352 pairs** using 30,200,504 literal comparisons or mathematically complete equivalence-class checks, with zero mismatches.

| Mode | Method | Raw pair space | Executed checks |
|---|---|---:|---:|
| I4xI8 | literal exhaustive | 4,096 | 4,096 |
| I8xI8 | literal exhaustive | 65,536 | 65,536 |
| FP8xFP8 | literal exhaustive | 65,536 | 65,536 |
| I4xFP8 | literal exhaustive | 4,096 | 4,096 |
| I4xBF16 | literal exhaustive | 1,048,576 | 1,048,576 |
| I8xBF16 | literal exhaustive | 16,777,216 | 16,777,216 |
| BF16xBF16 | complete equivalence-class proof | 4,294,967,296 | 12,235,448 |

BF16xBF16 is not falsely described as a 4.29-billion-iteration brute-force run. Every finite nonzero BF16 value is represented by:

```text
sign
8-bit significand
scale exponent
```

The exact product-to-BF16 result depends only on sign XOR, the 16-bit significand product and the scale-exponent sum. The scan exhausts:

- 7,102 unique normal×normal significand products × 507 scale sums × 2 signs;
- 9,891 unique subnormal×normal products × 254 scale sums × 2 signs;
- 4,646 unique subnormal×subnormal products × one scale sum × 2 signs;
- zero/normal/subnormal/infinity/NaN sign-category combinations.

Significand and exponent fields are independent in BF16, so these families cover every reachable finite raw pair. Two independent RNE implementations are compared: the RTL-style guard/sticky algorithm and an exact quotient/remainder tie-to-even reference.

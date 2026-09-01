# Sandbox validation

- Status: **PASS**
- Unit tests: 17
- Explicit multiplier bricks: 16
- Logical modes: 10
- Planned local DC groups/runs: 11 / 33
- Generated RTL vectors: 2560
- Full vector SHA-256: `24f1c3874e4a6fefdb7e33f249ab0ff4434b6d7509d809cfca21b810e0eb5211`

## Exhaustive / stratified coverage

```text
INT4×INT4       256 input pairs, 16 outputs/pair
INT4×INT8      4096 input pairs, 8 outputs/pair
INT8×INT8     65536 input pairs, 4 outputs/pair
INT16×INT16    boundaries + 5000 random pairs
FP8×FP8       65536 raw-code pairs
INT4×FP8       4096 raw-code pairs
INT8×FP8      65536 raw-code pairs
BF16/mixed     4776 directed/stratified checks
```

## Structural checks

- Only `rtl/mul4x4_brick.sv` contains an arithmetic multiply operator.
- The product core elaboration contract is a single generate loop with bound 16.
- No `DW_fp_mult` appears in the FusionMul16 RTL.
- All module names are unique; delimiters are balanced.
- DC manifest contains 11 groups × 3 periods = 33 runs.

## Boundary

The sandbox has no SystemVerilog compiler/simulator, CLN22UL `.db`, Design Compiler or DesignWare runtime. RTL syntax/elaboration, DW interface compatibility, gate-level equivalence and PPA remain mandatory local-agent gates.
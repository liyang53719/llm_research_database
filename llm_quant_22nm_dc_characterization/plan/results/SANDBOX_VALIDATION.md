# Sandbox validation

- Python files compiled: 8
- RTL files static-checked: 5
- Planned local DC groups: 21
- Planned local DC runs: 63
- INT4→FP8 exact codes: 16/16
- INT8→FP8 exact codes: 80/256
- INT8→FP8 max absolute integer-code error: 4.0
- INT8→BF16 exact codes: 256/256
- I4×FP8 converter dot exact fraction: 1.000
- I8×FP8 converter dot exact fraction: 0.000
- I8×FP8 mean relative dot error: 0.088044
- I8×FP8 p99 relative dot error: 1.219580

No HDL compiler, 22 nm `.db`, DC or DesignWare runtime was available in the sandbox. RTL validation here is structural, not synthesis signoff.

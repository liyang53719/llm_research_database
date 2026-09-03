# Integration guide

- Use `fusion_mul16_v4_flat` at Verilog-only hierarchy boundaries; it flattens the four accumulator/status arrays.
- Use `fusion_mul16_v4` inside SystemVerilog designs that support unpacked array ports.
- `fusion_mul16_v4.f` lists source order.
- Define `FUSION_USE_DW` for DC/VCS so each brick instantiates `DW_mult_uns #(4,4)`.
- Add the installed DesignWare simulation library for VCS.
- Do not apply multicycle exceptions to the four FP32 recurrent paths; II=1 requires true one-cycle recurrence closure.
- The IP has no output backpressure. Downstream logic must accept or sample outputs on valid pulses.
- Clock gating, scan insertion, SRAM and network interfaces are outside this IP.
- A fixed-mode build permits DC to remove inactive format logic. It is not area-equivalent to the dynamic seven-mode release profile.

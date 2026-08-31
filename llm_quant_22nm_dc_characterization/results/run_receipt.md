# CLN22UL 0.80 V TT DC characterization receipt

- Final acceptance tier: L2
- Final validation: 58 groups, 174 runs, `ERRORS=NONE`
- Common clock periods: 2.0 ns, 1.0 ns, 0.9 ns
- Target library: `sc6p5mcpp140z_cln22ul_base_svt_c35_tt_typical_max_0p80v_25c.db`
- Library SHA-256: `846ae0a44e5e194df7995c45ad63ac6a6527f45267a73ac2dae6f72470db4983`
- Library setup SHA-256: `d287a2bc825e981bb60b4cbb580a97ef0014ca2d296287928162262b5ce1bbc5`
- RTL bundle SHA-256: `207158581ab077db004b0627bf1709ee71ee9c88921cc57910bdbf0c9d5ddf6b`
- Design Compiler: `X-2025.06-SP3`
- DesignWare Building Blocks: `X-2025.06-DWBB_202506.3`
- Compile mode: `compile_ultra`
- CPU policy: CPUs 8-23; two DC processes maximum; one DC core per process
- Memory policy: cgroup `MemoryHigh=36G`, `MemoryMax=40G`, `MemorySwapMax=0`
- Maximum sampled cgroup `MemoryCurrent`: 37,779,120,128 bytes (about 35.18 GiB)
- Sampled cgroup memory events at peak: `high=0`, `max=0`, `oom=0`, `oom_kill=0`
- L2 service runtime: 7 h 50 min 7 s; CPU time: 13 h 58 min 38 s
- Blackbox count: zero for all 174 runs
- Timing-fail points: 13 total; retained in the raw results
- 1 GHz timing: 53/58 groups met timing

## 1 GHz timing-fail groups

| Group | WNS (ns) | Mapped cell area (um2) |
|---|---:|---:|
| FP_MAC_BF16_E8M7 | -0.193165 | 1373.918017 |
| FP_MAC_FP16_E5M10 | -0.549626 | 2014.831027 |
| ARRAY_BF16_4X4 | -0.295895 | 17310.111183 |
| ARRAY_BF16_8X8 | -0.430419 | 60157.552631 |
| ARRAY_BF16_16X16 | -0.488717 | 229805.396362 |

## Interpretation boundary

`mapped_cell_area_um2` is mapped standard-cell area. It excludes SRAM macros,
floorplan utilization, CTS, routing, power grid, DFT, and final die/core area.

The installed DesignWare release cannot implement native FP4 E2M1 or E2M2
`DW_fp_mac`. `FP_MAC_FP4_E2M1` is therefore explicitly implemented and labeled
as an E2M1-to-E3M2 conversion, minimum-DW-FP6 MAC, truncate/saturate surrogate.
It is an area upper-bound proxy including conversion logic, not bit-exact FP4.

Non-monotonic mapped-area points are retained and listed as warnings in
`validation_report.txt`; no results were manually altered.

The workbook was not overwritten because the required spreadsheet artifact
runtime was unavailable in this session. CSV and SQLite deliverables are the
authoritative populated outputs.

# Local DC handoff and acceptance

## Fixed environment

```text
CLN22UL base SVT C35
TT typical_max, 0.80 V, 25 C
DC X-2025.06-SP3
DWBB X-2025.06-DWBB_202506.3
compile_ultra
clock period 1.000 ns only
```

## Runs

Twelve groups are defined in `config/dc_experiments_1ghz.csv`:

- brick sharing proof;
- product pipe;
- selected accumulator backend;
- dynamic FTZ release IP;
- optional IEEE/special profile;
- seven fixed modes.

## Hard release gates

For `V4_FINAL_DYNAMIC_FTZ`:

```text
mapped_cell_area_um2 > 0
setup WNS >= 0
blackbox_count = 0
exactly 16 x DW_mult_uns 4x4
0 additional multipliers
12 BF16 DW_fp_add after elaboration
4 FP32 DW_fp_add after elaboration
VCS 28/28 PASS
full input-domain mismatches = 0
precision proxy = PASS
```

The v3 selected full cluster is 14,043.211 µm². The initial v4 integration budget is +10%, therefore the hard area ceiling is 15,447.532 µm². This ceiling includes configuration, clear/last protocol and flat output packing but excludes physical-design overhead.

## Mandatory reports

```text
report_qor.rpt
report_area.rpt
report_timing.rpt
report_hold.rpt
report_constraints.rpt
report_resources.rpt
report_reference.rpt
check_design_post.rpt
summary.kv
```

## Required warnings/reporting

Pre-layout hold violations, high-fanout nets, max-transition/max-capacitance violations and setup margin below 50 ps must be reported even if setup WNS is nonnegative. A nominal near-zero DC slack is not physical 1 GHz signoff.

## Output files

```text
results/vcs/vcs_summary.csv
results/local_dc/v4_area_1ghz.csv
results/local_dc/validation_report.txt
results/local_dc/architecture_decision.json
results/local_dc/structure_proof.json
```

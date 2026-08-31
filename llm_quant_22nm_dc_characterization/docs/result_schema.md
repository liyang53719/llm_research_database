# Result schema

The authoritative machine-readable file is `results/area_22nm_raw.csv`.

Minimum columns required for workbook/database import:

| Column | Meaning |
|---|---|
| run_id | Unique design group + clock point |
| group_id | Unique RTL topology/parameter set |
| tier | L1 or L2 |
| category | scalar, PE, array, quant/KV |
| clock_period_ns | Common synthesis constraint |
| library_set_id | Comparison-group identity |
| compile_mode | `ultra` or `standard` |
| mapped_cell_area_um2 | DC mapped standard-cell area |
| combinational_area_um2 | Parsed from report_area |
| noncombinational_area_um2 | Parsed from report_area |
| leaf_cell_count | Mapped leaf cells |
| blackbox_count | Must be zero |
| wns_ns | Worst slack |
| critical_delay_ns | `period - WNS` |
| achieved_fmax_mhz | Derived from critical delay |
| timing_met | 1 or 0 |
| tool_version | DC version |
| report_dir | Audit trail |

Do not fill missing values with zero.

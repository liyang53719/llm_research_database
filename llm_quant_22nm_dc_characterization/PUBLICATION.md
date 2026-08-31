# Public release notes

This directory contains sanitized CLN22UL 0.80 V TT Design Compiler characterization results.

- 58 design groups and 174 synthesis points are present.
- Local absolute paths, hostname, licensed library locations, build caches, DDC files, and mapped netlists are excluded.
- `<CLN22UL_DB>` and `<PROJECT_ROOT>` are deliberate placeholders.
- No proprietary `.db`, `.lib`, or DesignWare library file is included.
- `results/area_22nm_raw.csv` and `results/llm_quantization_with_22nm.sqlite` are the authoritative data files.
- FP4 E2M1 is explicitly labeled as a converted minimum-DW-FP6 area upper-bound surrogate, not a native bit-exact FP4 implementation.
- Timing-fail and non-monotonic area points are retained.

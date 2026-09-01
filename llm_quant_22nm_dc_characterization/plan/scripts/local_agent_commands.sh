#!/usr/bin/env bash
set -euo pipefail

# Run from llm_quant_22nm_dc_characterization/plan.
PARENT="$(cd .. && pwd)"
python3 scripts/gen_mixed_manifest.py
python3 scripts/static_rtl_check.py

# The local agent should extend the parent generator to elaborate the 21 groups,
# reuse ../scripts/dc_synth.tcl and ../config/library_setup.local.tcl, then run:
#
# python3 scripts/run_local_dc.py --parent-root "$PARENT" \
#   --lib-setup "$PARENT/config/library_setup.local.tcl" --jobs 1
# python3 scripts/collect_mixed_results.py
# python3 scripts/validate_local_results.py --raw results/mixed_area_raw.csv
# python3 scripts/build_arch_comparison.py

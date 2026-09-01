#!/usr/bin/env bash
set -euo pipefail

# Run from llm_quant_22nm_dc_characterization/plan.
PARENT="$(cd .. && pwd)"
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/static_rtl_check.py
python3 scripts/gen_mixed_manifest.py
python3 scripts/compile_generated_wrappers.py
python3 scripts/run_numeric_rtl_crosscheck.py
python3 scripts/run_dw_converter_crosscheck.py
scripts/run_local_capped.sh \
  --parent-root "$PARENT" \
  --lib-setup "$PARENT/config/library_setup.local.tcl" \
  --dc-shell "${DC_SHELL:-dc_shell}"
python3 scripts/collect_mixed_results.py
python3 scripts/validate_local_results.py
python3 scripts/build_arch_comparison.py
python3 scripts/gen_pipeline_followup.py
scripts/run_local_capped.sh --manifest build_pipeline/runs.csv \
  --parent-root "$PARENT" --lib-setup "$PARENT/config/library_setup.local.tcl" \
  --dc-shell "${DC_SHELL:-dc_shell}"
python3 scripts/collect_mixed_results.py --build-dir build_pipeline --output-dir results/pipeline
python3 scripts/validate_pipeline_results.py
python3 scripts/build_pipeline_comparison.py
python3 scripts/build_local_execution_report.py

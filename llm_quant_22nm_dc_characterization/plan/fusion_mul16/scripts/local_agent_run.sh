#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

: "${LIB_SETUP:?Set LIB_SETUP to the local CLN22UL 0.80 V TT setup Tcl}"

python3 scripts/run_sandbox_validation.py
python3 scripts/run_rtl_crosscheck.py
python3 scripts/gen_dc_runs.py
bash scripts/run_local_capped.sh "$LIB_SETUP"
python3 scripts/collect_dc_results.py
python3 scripts/validate_dc_results.py
python3 scripts/prove_brick_sharing.py \
  build_dc/FUSION16_CORE_PROOF__T1p0ns \
  --output results/local_dc/brick_sharing_proof.json
python3 scripts/build_architecture_pareto.py

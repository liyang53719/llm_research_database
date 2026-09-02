#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LIB_SETUP="${1:-$ROOT/../config/library_setup.local.tcl}"
JOBS=1

cd "$ROOT"
python3 scripts/run_sandbox_validation.py
python3 scripts/gen_test_vectors.py --per-mode 512 --output results/rtl_vectors_v2.jsonl
python3 scripts/gen_vcs_vectors.py --per-mode 512 --output-dir results/vcs_vectors
python3 scripts/run_vcs_crosscheck.py --per-mode 512
python3 scripts/gen_dc_runs.py
bash scripts/run_local_capped.sh "$LIB_SETUP"
python3 scripts/collect_dc_results.py
python3 scripts/validate_dc_results.py

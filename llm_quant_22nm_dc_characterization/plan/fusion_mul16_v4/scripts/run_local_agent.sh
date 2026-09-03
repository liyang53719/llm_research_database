#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 2 ]]; then
  echo "Usage: $0 /absolute/path/library_setup.local.tcl /absolute/path/DW/sim_ver [jobs]" >&2
  exit 2
fi
if [[ "${FUSION_V4_CAPPED:-0}" != "1" ]]; then
  available_kib=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
  if (( available_kib < 48 * 1024 * 1024 )); then echo "Refusing launch: MemAvailable below 48 GiB" >&2; exit 3; fi
  exec systemd-run --user --scope --quiet -p MemoryHigh=36G -p MemoryMax=40G -p MemorySwapMax=0 \
    env FUSION_V4_CAPPED=1 taskset -c 8-23 bash "$0" "$@"
fi
LIB_SETUP="$(realpath "$1")"
DW_SIM="$(realpath "$2")"
JOBS="${3:-1}"
if [[ "$JOBS" != "1" && "$JOBS" != "2" ]]; then echo "jobs must be 1 or 2" >&2; exit 2; fi
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/model"
python3 scripts/run_sandbox_validation.py
python3 scripts/gen_vcs_vectors.py
python3 scripts/run_vcs.py --vcs vcs --dw-sim "$DW_SIM"
python3 scripts/run_vcs_protocol.py --vcs vcs --dw-sim "$DW_SIM"
python3 scripts/gen_dc_runs.py
python3 scripts/run_dc.py --root "$ROOT" --lib-setup "$LIB_SETUP" --jobs "$JOBS" --max-cores 1 --cpus 8-23
python3 scripts/collect_dc_results.py
python3 scripts/build_structure_proof.py
python3 scripts/validate_dc_results.py

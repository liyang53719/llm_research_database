#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
MIN_AVAILABLE_KIB=$((48 * 1024 * 1024))
MEM_AVAILABLE_KIB=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
SYSTEMD_ENV_ARGS=()

for ENV_NAME in SNPSLMD_LICENSE_FILE LM_LICENSE_FILE SYNOPSYS; do
  if [[ -v $ENV_NAME ]]; then
    SYSTEMD_ENV_ARGS+=(--setenv="$ENV_NAME=${!ENV_NAME}")
  fi
done

if (( MEM_AVAILABLE_KIB < MIN_AVAILABLE_KIB )); then
  echo "Refusing to start: MemAvailable is below the 48 GiB admission floor." >&2
  exit 75
fi

cd "$ROOT"
exec systemd-run --user --collect --wait --pipe \
  --working-directory="$ROOT" \
  "${SYSTEMD_ENV_ARGS[@]}" \
  -p AllowedCPUs=8-23 \
  -p MemoryHigh=36G \
  -p MemoryMax=40G \
  -p MemorySwapMax=0 \
  taskset -c 8-23 \
  python3 scripts/run_all.py --jobs 2 --dc-max-cores 1 "$@"

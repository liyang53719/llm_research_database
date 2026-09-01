#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
lib_setup=${1:-}
if [[ -z "$lib_setup" || ! -f "$lib_setup" ]]; then
  echo "usage: $0 /path/to/library_setup.local.tcl" >&2
  exit 2
fi
shift

available_kib=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
if (( available_kib < 48 * 1024 * 1024 )); then
  echo "Refusing DC launch: MemAvailable below 48 GiB" >&2
  exit 3
fi

exec systemd-run --user --scope --quiet \
  -p MemoryHigh=36G -p MemoryMax=40G -p MemorySwapMax=0 \
  taskset -c 8-23 python3 "$root/scripts/run_dc.py" \
    --root "$root" --lib-setup "$lib_setup" --jobs 1 --max-cores 1 --cpus 8-23 \
    "$@"

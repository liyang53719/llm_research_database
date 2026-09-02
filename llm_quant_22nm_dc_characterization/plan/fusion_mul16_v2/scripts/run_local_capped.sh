#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
lib=${1:-}
if [[ -z "$lib" || ! -f "$lib" ]]; then echo "usage: $0 /path/to/library_setup.local.tcl" >&2; exit 2; fi
shift
available_kib=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
if (( available_kib < 48 * 1024 * 1024 )); then echo "Refusing launch: MemAvailable below 48 GiB" >&2; exit 3; fi
exec systemd-run --user --scope --quiet -p MemoryHigh=36G -p MemoryMax=40G -p MemorySwapMax=0 \
  taskset -c 8-23 python3 "$root/scripts/run_dc.py" --root "$root" --lib-setup "$lib" --jobs 1 --max-cores 1 --cpus 8-23 "$@"

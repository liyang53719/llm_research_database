#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json
from collections import defaultdict
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument("--raw",required=True); a=p.parse_args()
root=Path(__file__).resolve().parents[1]
cfg=json.loads((root/"config/mixed_characterization.json").read_text())
with Path(a.raw).open(encoding="utf-8-sig") as f: rows=list(csv.DictReader(f))
errors=[]
if len(rows)!=cfg["expected_dc_runs"]: errors.append("run count mismatch")
by=defaultdict(list)
for r in rows:
    by[r["group_id"]].append(r)
    if r.get("status")!="ok": errors.append(f'{r.get("run_id")}: status')
    try:
        if float(r["mapped_cell_area_um2"])<=0: errors.append(f'{r.get("run_id")}: area')
    except Exception: errors.append(f'{r.get("run_id")}: missing area')
    if str(r.get("blackbox_count")) not in {"0","0.0"}: errors.append(f'{r.get("run_id")}: blackbox')
for g,v in by.items():
    if len(v)!=len(cfg["clock_periods_ns"]): errors.append(f"{g}: period sweep")
if errors: raise SystemExit("\n".join(errors))
print(f"Validated {len(rows)} runs across {len(by)} groups")

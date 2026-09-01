#!/usr/bin/env python3
from __future__ import annotations
import csv, json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
cfg=json.loads((root/"config/mixed_characterization.json").read_text())
with (root/"config/mixed_experiment_groups.csv").open(encoding="utf-8-sig") as f:
    groups=list(csv.DictReader(f))
rows=[]
for g in groups:
    for p in cfg["clock_periods_ns"]:
        rows.append({**g,"run_id":f'{g["group_id"]}__T{str(p).replace(".","p")}ns',
                     "clock_period_ns":p,"clock_mhz":1000.0/p,"status":"PLANNED"})
out=root/"results/mixed_expected_runs.csv"
with out.open("w",newline="",encoding="utf-8-sig") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(f"Wrote {len(rows)} planned runs")

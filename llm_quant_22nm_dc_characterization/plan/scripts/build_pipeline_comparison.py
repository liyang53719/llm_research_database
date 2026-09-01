#!/usr/bin/env python3
from __future__ import annotations
import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(path):
    with Path(path).open(encoding="utf-8-sig") as f:return list(csv.DictReader(f))
def num(v):
    try:return float(v)
    except:return None

def main():
    baseline={r["group_id"]:r for r in read(ROOT/"results/mixed_group_summary.csv")}
    pipeline=read(ROOT/"results/pipeline/mixed_group_summary.csv")
    rows=[]
    for p in pipeline:
        b=baseline[p["base_group"]]
        pa=num(p["area_1ghz_um2"]);ba=num(b["area_1ghz_um2"])
        rows.append({
            "pipeline_group":p["group_id"],"base_group":p["base_group"],
            "throughput_contract":p["throughput_contract"],"pipeline_latency_note":p.get("notes","explicit pipeline follow-up"),
            "base_area_1ghz_um2":ba,"pipeline_area_1ghz_um2":pa,
            "pipeline_area_overhead_pct":((pa/ba)-1)*100 if pa and ba else None,
            "base_wns_1ghz_ns":b["wns_1ghz_ns"],"pipeline_wns_1ghz_ns":p["wns_1ghz_ns"],
            "base_timing_met_1ghz":b["timing_met_1ghz"],"pipeline_timing_met_1ghz":p["timing_met_1ghz"],
            "pipeline_closes_1ghz":str(p["timing_met_1ghz"] in {"1","1.0"}).lower(),
            "pipeline_best_feasible_area_um2":p["best_feasible_area_um2"],
        })
    out=ROOT/"results/pipeline_followup_comparison.csv"
    with out.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(f"Wrote {len(rows)} pipeline comparisons")

if __name__=="__main__":main()

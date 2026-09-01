#!/usr/bin/env python3
from __future__ import annotations
import csv,json,re
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def read(path:Path):
    with path.open(encoding="utf-8-sig") as f:return list(csv.DictReader(f))

def main():
    cfg=json.loads((ROOT/"config/pipeline_characterization.json").read_text())
    groups=read(ROOT/"config/pipeline_followup_groups.csv")
    manifest=read(ROOT/"build_pipeline/runs.csv")
    rows=read(ROOT/"results/pipeline/mixed_area_raw.csv")
    errors=[];warnings=[];by=defaultdict(list)
    if len(groups)!=cfg["unique_groups"]:errors.append("group count mismatch")
    if len(manifest)!=cfg["expected_dc_runs"]:errors.append("manifest count mismatch")
    if len(rows)!=len(manifest):errors.append("raw count mismatch")
    if {r["run_id"] for r in rows}!={r["run_id"] for r in manifest}:errors.append("run ID mismatch")
    for r in rows:
        by[r["group_id"]].append(r);rid=r["run_id"]
        try:
            if float(r["mapped_cell_area_um2"])<=0:errors.append(f"{rid}: area")
        except Exception:errors.append(f"{rid}: missing area")
        if r.get("blackbox_count") not in {"0","0.0"}:errors.append(f"{rid}: blackbox")
        if r.get("status")!="ok":errors.append(f"{rid}: status")
        if r.get("rtl_bundle_sha256_reported")!=r.get("rtl_bundle_sha256"):errors.append(f"{rid}: RTL hash")
        run=Path(r["run_dir"])
        for name in ("report_area.rpt","report_qor.rpt","report_resources.rpt","check_design_post.rpt"):
            if not (run/"reports"/name).is_file():errors.append(f"{rid}: {name}")
        text=(run/"dc_stdout.log").read_text(errors="ignore")
        if re.search(r"^(Error|Fatal):",text,re.MULTILINE):errors.append(f"{rid}: DC error")
    periods=sorted(cfg["clock_periods_ns"])
    for g in groups:
        grows=by[g["group_id"]]
        if sorted(float(r["clock_period_ns"]) for r in grows)!=periods:errors.append(f"{g['group_id']}: periods")
        if not any(r.get("timing_met") in {"1","1.0"} for r in grows):warnings.append(f"{g['group_id']}: no timing-met point")
    for field in ("library_set_id","target_libraries","compile_mode","library_setup_sha256","rtl_bundle_sha256","tool_version"):
        values={r.get(field,"").strip() for r in rows if r.get(field,"").strip()}
        if len(values)!=1:errors.append(f"{field}: comparison contract")
    report=ROOT/"results/pipeline/validation_report.txt"
    with report.open("w") as f:
        f.write(f"Expected groups: {cfg['unique_groups']}\nExpected runs: {cfg['expected_dc_runs']}\nObserved groups: {len(by)}\nObserved rows: {len(rows)}\n\nERRORS\n")
        f.write("\n".join(errors) if errors else "NONE");f.write("\n\nWARNINGS\n")
        f.write("\n".join(warnings) if warnings else "NONE");f.write("\n")
    print(report.read_text())
    if errors:raise SystemExit(2)

if __name__=="__main__":main()

#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parent
HOME=Path.home()
PUBLIC_DB="<CLN22UL_DB>/sc6p5mcpp140z_cln22ul_base_svt_c35_tt_typical_max_0p80v_25c.db"

def sanitize(text:str)->str:
    text=text.replace(str(PROJECT),"<PROJECT_ROOT>").replace(str(HOME),"<LOCAL_HOME>")
    text=text.replace("<HOST>","<HOST>")
    return text

def write_text(src:Path,dst:Path):
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(sanitize(src.read_text(encoding="utf-8-sig",errors="ignore")),encoding="utf-8")

def write_csv(src:Path,dst:Path,evidence_kind:str|None=None):
    with src.open(encoding="utf-8-sig") as f:rows=list(csv.DictReader(f));fields=list(rows[0]) if rows else []
    for row in rows:
        run_id=row.get("run_id","")
        if run_id and evidence_kind:
            if "run_dir" in row:row["run_dir"]=f"evidence/{evidence_kind}/{run_id}"
            if "report_dir" in row:row["report_dir"]=f"evidence/{evidence_kind}/{run_id}/reports"
            if "rtl_list" in row:row["rtl_list"]="<GENERATED_RTL_LIST>"
        if "target_libraries" in row and row["target_libraries"]:row["target_libraries"]=PUBLIC_DB
        for key,value in row.items():row[key]=sanitize(value) if isinstance(value,str) else value
    dst.parent.mkdir(parents=True,exist_ok=True)
    with dst.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)

def copy_tree_files(src_dir:Path,dst_dir:Path):
    for src in sorted(src_dir.rglob("*")):
        if not src.is_file() or "__pycache__" in src.parts or src.suffix==".pyc":continue
        rel=src.relative_to(src_dir);dst=dst_dir/rel
        if src.suffix.lower() in {".csv"}:write_csv(src,dst)
        else:write_text(src,dst)

def evidence(build:Path,dst:Path):
    for run in sorted(build.glob("*__T*ns")):
        out=dst/run.name
        if (run/"summary.kv").is_file():write_text(run/"summary.kv",out/"summary.kv")
        reports=run/"reports"
        if reports.is_dir():
            for report in sorted(reports.iterdir()):
                if report.is_file():write_text(report,out/"reports"/report.name)

def manifest(dst:Path):
    out=dst/"PUBLIC_LOCAL_RESULTS_MANIFEST.csv"
    files=[p for p in sorted(dst.rglob("*")) if p.is_file() and p!=out]
    with out.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(["relative_path","size_bytes","sha256"])
        for p in files:w.writerow([p.relative_to(dst),p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()])

def main():
    ap=argparse.ArgumentParser();ap.add_argument("destination");args=ap.parse_args()
    dst=Path(args.destination).resolve()
    if dst.exists():raise SystemExit(f"Refusing to overwrite {dst}")
    dst.mkdir(parents=True)
    for name in ("AGENT_TASK.md","README_CN.md"):
        write_text(ROOT/name,dst/name)
    for dirname in ("config","docs","model","rtl","scripts","tests"):
        copy_tree_files(ROOT/dirname,dst/dirname)
    for src in sorted((ROOT/"results").rglob("*")):
        if not src.is_file() or "__pycache__" in src.parts:continue
        rel=src.relative_to(ROOT/"results");out=dst/"results"/rel
        kind="pipeline" if rel.parts and rel.parts[0]=="pipeline" else "baseline"
        if src.suffix.lower()==".csv":write_csv(src,out,kind)
        else:write_text(src,out)
    evidence(ROOT/"build_mixed",dst/"evidence/baseline")
    evidence(ROOT/"build_pipeline",dst/"evidence/pipeline")
    (dst/"PUBLIC_LOCAL_RESULTS.md").write_text(
        "# Sanitized local execution results\n\n"
        "- Baseline: 21 groups / 63 DC runs.\n"
        "- Pipeline follow-up: 10 groups / 30 DC runs.\n"
        "- Local absolute paths, hostname, licensed library paths, build caches, DDC and netlists are excluded.\n"
        "- No proprietary .db/.lib/.sldb file is included.\n"
        "- The target-model operator/window trace was not provided; real r remains unmeasured.\n",
        encoding="utf-8")
    manifest(dst);print(dst)

if __name__=="__main__":main()

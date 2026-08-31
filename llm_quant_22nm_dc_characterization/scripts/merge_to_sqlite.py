#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read_csv(path):
    with path.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def sqlite_type(values):
    vals = [v for v in values if v not in (None, "")]
    if not vals:
        return "TEXT"
    try:
        for v in vals:
            float(v)
        return "REAL"
    except Exception:
        return "TEXT"

def replace_table(con, name, rows):
    con.execute(f'DROP TABLE IF EXISTS "{name}"')
    cols = list(rows[0].keys())
    ddl = ", ".join(f'"{c}" {sqlite_type([r.get(c) for r in rows])}' for c in cols)
    con.execute(f'CREATE TABLE "{name}" ({ddl})')
    placeholders = ",".join("?" for _ in cols)
    quoted = ",".join(f'"{c}"' for c in cols)
    con.executemany(
        f'INSERT INTO "{name}" ({quoted}) VALUES ({placeholders})',
        [tuple(r.get(c) for c in cols) for r in rows],
    )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-db", required=True)
    ap.add_argument("--output-db", default=str(ROOT / "results/llm_quantization_with_22nm.sqlite"))
    args = ap.parse_args()

    raw = read_csv(ROOT / "results/area_22nm_raw.csv")
    summary = read_csv(ROOT / "results/area_22nm_group_summary.csv")
    mapping = read_csv(ROOT / "config/scheme_to_group_map.csv")
    out = Path(args.output_db)
    shutil.copy2(args.base_db, out)

    con = sqlite3.connect(out)
    replace_table(con, "local_22nm_runs", raw)
    replace_table(con, "local_22nm_group_summary", summary)
    replace_table(con, "local_22nm_scheme_map", mapping)
    con.execute('CREATE INDEX IF NOT EXISTS idx_local22_group ON local_22nm_runs(group_id)')
    con.execute('CREATE INDEX IF NOT EXISTS idx_local22_scheme ON local_22nm_scheme_map(scheme_id)')
    con.commit()
    con.close()
    print(f"Updated database: {out}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def n(x):
    try:return int(float(x))
    except:return None
def main():
    with (ROOT/'results/local_dc/v4_area_1ghz.csv').open(encoding='utf-8-sig') as f: rows={r['group_id']:r for r in csv.DictReader(f)}
    r=rows['V4_FINAL_DYNAMIC_FTZ']
    proof={
      'group_id':'V4_FINAL_DYNAMIC_FTZ',
      'brick_instance_count_precompile':n(r.get('brick_instance_count_precompile')),
      'dw_mult_instance_count_precompile':n(r.get('dw_mult_instance_count_precompile')),
      'dw_mult_4x4_rows':n(r.get('dw_mult_4x4_rows')),
      'other_multiplier_rows':n(r.get('other_multiplier_rows')),
      'bf16_add_rows':n(r.get('bf16_add_rows')),
      'fp32_add_rows':n(r.get('fp32_add_rows')),
      'blackbox_count':n(r.get('blackbox_count')),
    }
    proof['checks']={
      'brick_precompile_16':proof['brick_instance_count_precompile']==16,
      'dw_mult_precompile_16':proof['dw_mult_instance_count_precompile']==16,
      'no_other_multiplier':proof['other_multiplier_rows'] in (0,None),
      'bf16_adders_12':proof['bf16_add_rows']==12,
      'fp32_adders_4':proof['fp32_add_rows']==4,
      'blackbox_zero':proof['blackbox_count']==0,
    }
    proof['status']='PASS' if all(proof['checks'].values()) else 'FAIL'
    out=ROOT/'results/local_dc/structure_proof.json'; out.write_text(json.dumps(proof,indent=2))
    print(json.dumps(proof,indent=2))
    if proof['status']!='PASS': raise SystemExit(2)
if __name__=='__main__':main()

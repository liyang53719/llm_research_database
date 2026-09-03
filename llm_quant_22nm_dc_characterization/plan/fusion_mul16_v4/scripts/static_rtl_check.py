#!/usr/bin/env python3
from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
errors=[]; rtl=list((ROOT/'rtl').glob('*.sv'))
for p in rtl:
    t=p.read_text()
    if len(re.findall(r'\bmodule\b',t))!=len(re.findall(r'\bendmodule\b',t)): errors.append(f'{p.name}: module/end mismatch')
    if t.count('(')!=t.count(')'): errors.append(f'{p.name}: paren mismatch')
    if t.count('{')!=t.count('}'): errors.append(f'{p.name}: brace mismatch')
all_text='\n'.join(p.read_text() for p in rtl)
pipe=(ROOT/'rtl/fusion_mul16_v4_product_pipe.sv').read_text()
tree=(ROOT/'rtl/fusion_mul16_v4_bf16_tree_dw.sv').read_text()
rec=(ROOT/'rtl/fusion_mul16_v4_fp32_recurrent_accum_dw.sv').read_text()
top=(ROOT/'rtl/fusion_mul16_v4.sv').read_text()
checks={
 'rtl_files':len(rtl),
 'single_brick_generate':pipe.count('fusion_mul16_v4_mul4x4_brick u_brick')==1 and 'g < 16' in pipe,
 'no_dw_fp_mult':'DW_fp_mult' not in all_text,
 'bf16_add_source_instances':tree.count('DW_fp_add #(7, 8, IEEE_COMPLIANCE)'),
 'fp32_add_source_instances':rec.count('DW_fp_add #(23, 8, IEEE_COMPLIANCE)'),
 'packed_128bit_inputs':'logic [127:0] lhs_packed_i' in top and 'logic [127:0] rhs_packed_i' in top,
 'fixed_rne':".rnd_i(3'b000)" in top and 'cfg_rnd_i' not in top,
 'no_direct_int16_mode':'I16' not in (ROOT/'rtl/fusion_mul16_v4_pkg.sv').read_text(),
 'latency_constants':'INT_VISIBLE_LATENCY = 4' in top and 'FP_VISIBLE_LATENCY  = 7' in top,
}
if checks['bf16_add_source_instances']!=3: errors.append('expected 3 BF16 add source instances under four-lane generate')
if checks['fp32_add_source_instances']!=1: errors.append('expected 1 FP32 add source instance under four-lane generate')
for k,v in checks.items():
    if isinstance(v,bool) and not v: errors.append(k)
listed={x.strip() for x in (ROOT/'rtl/fusion_mul16_v4.f').read_text().splitlines() if x.strip()}
actual={p.name for p in rtl}
if listed!=actual: errors.append(f'filelist mismatch missing={actual-listed} extra={listed-actual}')
report={'status':'PASS' if not errors else 'FAIL','checks':checks,'errors':errors}
(ROOT/'results/rtl_static_check.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
if errors: raise SystemExit(2)

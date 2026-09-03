#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def normalize_loop_declarations(text):
    # VCS requires process-local loop variables in v4; v2 used the equivalent
    # `integer` declaration.  Normalize only this declaration spelling so the
    # source-lock comparison remains an arithmetic/data-path comparison.
    return re.sub(r'for \((?:integer|int) (i|lane|item) =', r'for (\1 =', text)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--v2-root',default='../fusion_mul16_v2'); ap.add_argument('--v3-root',default='../fusion_mul16_v3_accum'); args=ap.parse_args()
    v2=Path(args.v2_root).resolve(); v3=Path(args.v3_root).resolve()
    checks=[]
    pairs=[
      ('pkg',v2/'rtl/fusion_mul16_v2_pkg.sv',ROOT/'rtl/fusion_mul16_v4_pkg.sv', [('fusion_mul16_v2_pkg','fusion_mul16_v4_pkg')]),
      ('brick',v2/'rtl/mul4x4_brick.sv',ROOT/'rtl/fusion_mul16_v4_mul4x4_brick.sv',[('module mul4x4_brick','module fusion_mul16_v4_mul4x4_brick')]),
      ('normalizer',v2/'rtl/raw16_to_bf16_rne.sv',ROOT/'rtl/fusion_mul16_v4_raw16_to_bf16_rne.sv',[('module raw16_to_bf16_rne','module fusion_mul16_v4_raw16_to_bf16_rne')]),
      ('product_pipe',v2/'rtl/fusion_mul16_v2_product_pipe.sv',ROOT/'rtl/fusion_mul16_v4_product_pipe.sv',[
        ('fusion_mul16_v2_product_pipe','fusion_mul16_v4_product_pipe'),('fusion_mul16_v2_pkg','fusion_mul16_v4_pkg'),
        ('mul4x4_brick u_brick','fusion_mul16_v4_mul4x4_brick u_brick'),('raw16_to_bf16_rne #','fusion_mul16_v4_raw16_to_bf16_rne #')]),
    ]
    for name,src,dst,repls in pairs:
        if not src.exists(): checks.append({'name':name,'status':'SOURCE_MISSING','source':str(src)}); continue
        text=src.read_text()
        for a,b in repls:text=text.replace(a,b)
        text=normalize_loop_declarations(text)
        dst_text=normalize_loop_declarations(dst.read_text())
        checks.append({'name':name,'status':'PASS' if text==dst_text else 'FAIL','source_sha256':sha(src),'v4_sha256':sha(dst)})
    report={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL','checks':checks,
            'derived_sources':[
              {'v4':'fusion_mul16_v4_bf16_tree_dw.sv','base':'fusion_mul16_v3_accum/rtl/fusion_mul16_v3_bf16_tree_dw.sv','changes':'namespace + IEEE_COMPLIANCE parameter only'},
              {'v4':'fusion_mul16_v4_fp32_recurrent_accum_dw.sv','base':'fusion_mul16_v3_accum/rtl/fusion_mul16_v3_accum_fp32_recurrent_dw.sv','changes':'namespace + IEEE_COMPLIANCE parameter + clear_done output'}]}
    (ROOT/'results/source_lock_report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    if report['status']!='PASS': raise SystemExit(2)
if __name__=='__main__':main()

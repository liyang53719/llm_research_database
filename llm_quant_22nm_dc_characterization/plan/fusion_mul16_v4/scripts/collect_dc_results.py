#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REQUIRED_REPORTS=('report_qor.rpt','report_area.rpt','report_timing.rpt','report_hold.rpt','report_constraints.rpt','report_resources.rpt','report_reference.rpt','check_design_post.rpt')
def kv(path):
    d={}
    if path.exists():
        for line in path.read_text(errors='ignore').splitlines():
            if '=' in line: k,v=line.split('=',1); d[k.strip()]=v.strip()
    return d
def num(x):
    try:return float(x)
    except:return None
def find(text,pat):
    m=re.search(pat,text,re.I|re.M); return num(m.group(1)) if m else None
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--build-dir',default='build_dc_1ghz'); ap.add_argument('--output',default='results/local_dc/v4_area_1ghz.csv'); a=ap.parse_args()
    rows=[]
    for mp in sorted((ROOT/a.build_dir).glob('*/meta.json')):
        rd=mp.parent; meta=json.loads(mp.read_text()); k=kv(rd/'summary.kv')
        qor=(rd/'reports/report_qor.rpt').read_text(errors='ignore') if (rd/'reports/report_qor.rpt').exists() else ''
        area=(rd/'reports/report_area.rpt').read_text(errors='ignore') if (rd/'reports/report_area.rpt').exists() else ''
        timing=(rd/'reports/report_timing.rpt').read_text(errors='ignore') if (rd/'reports/report_timing.rpt').exists() else ''
        hold=(rd/'reports/report_hold.rpt').read_text(errors='ignore') if (rd/'reports/report_hold.rpt').exists() else ''
        cons=(rd/'reports/report_constraints.rpt').read_text(errors='ignore') if (rd/'reports/report_constraints.rpt').exists() else ''
        stdout=(rd/'dc_stdout.log').read_text(errors='ignore') if (rd/'dc_stdout.log').exists() else ''
        refs=(rd/'reports/report_reference.rpt').read_text(errors='ignore') if (rd/'reports/report_reference.rpt').exists() else (rd/'reports/report_reference_post.rpt').read_text(errors='ignore') if (rd/'reports/report_reference_post.rpt').exists() else ''
        refs_pre=(rd/'reports/report_reference_pre.rpt').read_text(errors='ignore') if (rd/'reports/report_reference_pre.rpt').exists() else ''
        res=(rd/'reports/report_resources.rpt').read_text(errors='ignore') if (rd/'reports/report_resources.rpt').exists() else (rd/'reports/report_resources_post.rpt').read_text(errors='ignore') if (rd/'reports/report_resources_post.rpt').exists() else ''
        text=refs+'\n'+res
        mult_lines=[line for line in res.splitlines() if 'DW_' in line and 'mult' in line.lower()]
        dw_mult_4x4=sum(bool(re.search(r'DW_mult_uns\s*\|.*a_width=4',line)) for line in mult_lines)
        def ref_count(name):
            match=re.search(r'^\s*'+re.escape(name)+r'\s+\S+\s+([0-9]+)\s+',refs_pre,re.M)
            return int(match.group(1)) if match else 0
        row={**meta,'library_set_id':k.get('library_set_id',''),'compile_mode':k.get('compile_mode',''),'mapped_cell_area_um2':num(k.get('mapped_cell_area_um2')),
             'combinational_area_um2':find(area,r'Combinational area:\s*([0-9eE+\-.]+)'),'noncombinational_area_um2':find(area,r'Noncombinational area:\s*([0-9eE+\-.]+)'),
             'total_cell_area_um2':find(area,r'Total cell area:\s*([0-9eE+\-.]+)'),
             'leaf_cell_count':num(k.get('leaf_cell_count')),'blackbox_count':num(k.get('blackbox_count')),'wns_ns':num(k.get('wns_ns')),'critical_delay_ns':num(k.get('critical_delay_ns')),
             'achieved_fmax_mhz':num(k.get('achieved_fmax_mhz')),'timing_met':int(float(k['timing_met'])) if k.get('timing_met') not in ('',None,'NA') else None,
             'worst_hold_violation_ns':find(qor,r'Worst Hold Violation:\s*([0-9eE+\-.]+)'),
             'hold_violation_count':find(qor,r'No\. of Hold Violations:\s*([0-9eE+\-.]+)'),
             'hold_tns_ns':find(qor,r'Total Hold Violation:\s*([0-9eE+\-.]+)'),
             'setup_tns_ns':find(qor,r'Total Negative Slack:\s*([0-9eE+\-.]+)'),
             'setup_violating_paths':find(qor,r'No\. of Violating Paths:\s*([0-9eE+\-.]+)'),
             'high_fanout_warning_count':qor.count('high-fanout'),
             'high_fanout_net_count':find(stdout,r'contains\s+([0-9]+) high-fanout nets'),
             'max_transition_violations':find(qor,r'Max Trans Violations:\s*([0-9eE+\-.]+)'),
             'max_capacitance_violations':find(qor,r'Max Cap Violations:\s*([0-9eE+\-.]+)'),
             'unconstrained_endpoint_count':len(re.findall(r'unconstrained endpoint',qor+'\n'+(rd/'reports/check_design_post.rpt').read_text(errors='ignore') if (rd/'reports/check_design_post.rpt').exists() else qor,re.I)),
             'critical_startpoint':(re.search(r'Startpoint:\s*(.+)',timing,re.I).group(1).strip() if re.search(r'Startpoint:\s*(.+)',timing,re.I) else ''),
             'critical_endpoint':(re.search(r'Endpoint:\s*(.+)',timing,re.I).group(1).strip() if re.search(r'Endpoint:\s*(.+)',timing,re.I) else ''),
             'constraint_violator_lines':sum('VIOLATED' in x for x in cons.splitlines()),
             'dc_error_count':len(re.findall(r'^Error(?::|-\[)',stdout,re.M)),
             'brick_instance_count_precompile':num(k.get('brick_instance_count_precompile')),'dw_mult_instance_count_precompile':num(k.get('dw_mult_instance_count_precompile')),
             'dw_mult_4x4_rows':dw_mult_4x4,
             'bf16_add_rows':ref_count('DW_fp_add_param_1_1'),
             'fp32_add_rows':ref_count('DW_fp_add_param_1'),
             'other_multiplier_rows':sum('DW_mult_uns' not in line for line in mult_lines),
             'rtl_input_sha256_reported':k.get('rtl_input_sha256',''),'library_setup_sha256':k.get('library_setup_sha256',''),'dc_max_cores':num(k.get('dc_max_cores')),
             'compile_mode_reported':k.get('compile_mode',''),'reports_complete':int(all((rd/'reports'/name).exists() for name in REQUIRED_REPORTS)),
             'status':'ok' if k and all((rd/'reports'/name).exists() for name in REQUIRED_REPORTS) else 'missing_evidence','report_dir':str((rd/'reports').resolve())}
        rows.append(row)
    if not rows: raise SystemExit('no DC result rows')
    out=ROOT/a.output; out.parent.mkdir(parents=True,exist_ok=True)
    fields=[]
    for r in rows:
        for x in r:
            if x not in fields: fields.append(x)
    with out.open('w',newline='',encoding='utf-8-sig') as f: w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    print(f'wrote {len(rows)} rows to {out}')
if __name__=='__main__':main()

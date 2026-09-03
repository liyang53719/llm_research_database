#!/usr/bin/env python3
from __future__ import annotations
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def n(x):
    try:return float(x)
    except:return None
def main():
    cfg=json.loads((ROOT/'config/characterization_1ghz.json').read_text())
    with (ROOT/'results/local_dc/v4_area_1ghz.csv').open(encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    by={r['group_id']:r for r in rows}; errors=[]; warnings=[]
    if len(rows)!=cfg['expected_groups']: errors.append(f'expected {cfg["expected_groups"]} rows, got {len(rows)}')
    if set(by) != {e['group_id'] for e in csv.DictReader((ROOT/'config/dc_experiments_1ghz.csv').open(encoding='utf-8-sig'))}:
        errors.append('DC group set mismatch')
    with (ROOT/'config/dc_experiments_1ghz.csv').open(encoding='utf-8-sig') as f: exps=list(csv.DictReader(f))
    if {r.get('library_set_id') for r in rows} != {cfg['environment']['library_set_id']}: errors.append('library/PVT mismatch')
    for e in exps:
        r=by.get(e['group_id'])
        if not r: errors.append(f'missing {e["group_id"]}'); continue
        if r.get('status')!='ok': errors.append(f'{e["group_id"]}: status={r.get("status")}')
        if r.get('reports_complete') not in ('1','1.0',1): errors.append(f'{e["group_id"]}: incomplete reports')
        if r.get('compile_mode')!='ultra' or r.get('compile_mode_reported')!='ultra': errors.append(f'{e["group_id"]}: compile mode')
        if n(r.get('clock_period_ns')) != 1.0: errors.append(f'{e["group_id"]}: clock period')
        if n(r.get('dc_max_cores')) != 1.0: errors.append(f'{e["group_id"]}: DC max cores')
        if r.get('rtl_input_sha256') != r.get('rtl_input_sha256_reported') or not r.get('rtl_input_sha256'): errors.append(f'{e["group_id"]}: RTL hash')
        if n(r.get('dc_error_count')) not in (None,0): errors.append(f'{e["group_id"]}: DC errors={r.get("dc_error_count")}')
        if not n(r.get('mapped_cell_area_um2')) or n(r['mapped_cell_area_um2'])<=0: errors.append(f'{e["group_id"]}: area')
        if n(r.get('blackbox_count'))!=0: errors.append(f'{e["group_id"]}: blackbox={r.get("blackbox_count")}')
        wanted_bricks=int(e['expected_bricks'])
        if n(r.get('brick_instance_count_precompile')) != wanted_bricks: errors.append(f'{e["group_id"]}: brick count expected {wanted_bricks}')
        if n(r.get('dw_mult_instance_count_precompile')) != wanted_bricks: errors.append(f'{e["group_id"]}: DW multiplier count expected {wanted_bricks}')
        if n(r.get('dw_mult_4x4_rows')) != wanted_bricks: errors.append(f'{e["group_id"]}: DW 4x4 rows expected {wanted_bricks}')
        if n(r.get('other_multiplier_rows')) not in (None,0): errors.append(f'{e["group_id"]}: additional multipliers')
        if n(r.get('bf16_add_rows')) != int(e['expected_bf16_adders']): errors.append(f'{e["group_id"]}: BF16 adder rows')
        if n(r.get('fp32_add_rows')) != int(e['expected_fp32_adders']): errors.append(f'{e["group_id"]}: FP32 adder rows')
        if e['hard_timing_gate']=='1' and r.get('timing_met') not in ('1','1.0',1): errors.append(f'{e["group_id"]}: 1GHz setup fail WNS={r.get("wns_ns")}')
        if n(r.get('max_transition_violations')) not in (None,0): warnings.append(f'{e["group_id"]}: max transition violations')
        if n(r.get('max_capacitance_violations')) not in (None,0): warnings.append(f'{e["group_id"]}: max capacitance violations')
        if n(r.get('hold_violation_count')) not in (None,0): warnings.append(f'{e["group_id"]}: pre-layout hold violations={r.get("hold_violation_count")}')
        if n(r.get('wns_ns')) is not None and n(r['wns_ns'])<0.05: warnings.append(f'{e["group_id"]}: setup margin below 50ps')
    final=by.get('V4_FINAL_DYNAMIC_FTZ')
    if final and n(final.get('mapped_cell_area_um2')):
        delta=(n(final['mapped_cell_area_um2'])/cfg['baseline']['v3_area_um2']-1)*100
        if delta>cfg['release_gates']['v4_integration_area_over_v3_max_pct']: errors.append(f'v4 area overhead {delta:.3f}% > limit')
    # External evidence gates.
    domain=json.loads((ROOT/'results/full_input_domain_report.json').read_text())
    precision=json.loads((ROOT/'results/precision_sweep_report.json').read_text())
    if domain['mismatches']!=0: errors.append('full input domain mismatch')
    if precision['status']!='PASS': errors.append('precision proxy fail')
    proof=ROOT/'results/local_dc/structure_proof.json'
    if not proof.exists(): errors.append('missing structure proof')
    else:
        pd=json.loads(proof.read_text())
        if pd.get('status')!='PASS': errors.append('structure proof fail')
    vcs=ROOT/'results/vcs/vcs_summary.csv'
    if not vcs.exists(): errors.append('missing VCS summary')
    else:
        with vcs.open(encoding='utf-8-sig') as f: vr=list(csv.DictReader(f))
        if len(vr)!=cfg['release_gates']['required_vcs_cases'] or any(r.get('passed') not in ('1','1.0') for r in vr): errors.append('VCS cases incomplete/fail')
    protocol=ROOT/'results/vcs/protocol_summary.json'
    if not protocol.exists() or not json.loads(protocol.read_text()).get('passed'): errors.append('VCS protocol gate failed')
    source_lock=ROOT/'results/source_lock_report.json'
    if not source_lock.exists() or json.loads(source_lock.read_text()).get('status')!='PASS': errors.append('source lock proof failed')
    status='PASS' if not errors else 'FAIL'
    report=['ERRORS',*(errors or ['NONE']),'','WARNINGS',*(warnings or ['NONE'])]
    (ROOT/'results/local_dc/validation_report.txt').write_text('\n'.join(report)+'\n')
    decision={'status':status,'release_profile':'V4_FINAL_DYNAMIC_FTZ','errors':errors,'warnings':warnings,'full_domain':domain['status'],'precision_proxy':precision['status'],'target_model_accuracy':'OPEN','physical_signoff':'OPEN'}
    (ROOT/'results/local_dc/architecture_decision.json').write_text(json.dumps(decision,indent=2))
    print('\n'.join(report))
    if errors: raise SystemExit(2)
if __name__=='__main__':main()

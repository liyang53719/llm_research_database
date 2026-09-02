#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def load(path):
    with Path(path).open(encoding='utf-8-sig') as f: return list(csv.DictReader(f))


def num(v):
    try:return float(v)
    except:return None


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--raw',default='results/local_dc/fusion16_v2_area_1ghz.csv'); a=ap.parse_args()
    cfg=json.loads((ROOT/'config/characterization_1ghz.json').read_text())
    rows=load(ROOT/a.raw); by={r['group_id']:r for r in rows}
    errors=[]; warnings=[]
    if len(rows)!=cfg['expected_runs']: errors.append(f"Expected {cfg['expected_runs']} rows, found {len(rows)}")
    libraries={r.get('library_set_id') for r in rows}
    if libraries!={cfg['library_set_id']}: errors.append(f'Library set mismatch: {libraries}')
    if any(not r.get('rtl_input_sha256') or r.get('rtl_input_sha256')!=r.get('rtl_input_sha256_reported') for r in rows): errors.append('RTL input hash mismatch')
    if len({r.get('library_setup_sha256') for r in rows})!=1 or '' in {r.get('library_setup_sha256') for r in rows}: errors.append('Library setup hash mismatch')
    fixed={'input_transition':0.05,'output_load':0.005,'max_transition':0.20,'clock_uncertainty_ratio':0.05,'input_delay_ratio':0.10,'output_delay_ratio':0.10}
    for r in rows:
        if r.get('status')!='ok': errors.append(f"{r['group_id']}: status={r.get('status')}")
        if num(r.get('mapped_cell_area_um2')) in (None,0): errors.append(f"{r['group_id']}: missing area")
        if num(r.get('blackbox_count'))!=0: errors.append(f"{r['group_id']}: blackbox={r.get('blackbox_count')}")
        if abs(num(r.get('clock_period_ns'))-1.0)>1e-12: errors.append(f"{r['group_id']}: not 1.0ns")
        if num(r.get('fp32_add_rows')) not in (None,0): errors.append(f"{r['group_id']}: FP32 adder row detected")
        if num(r.get('dc_error_count')) not in (None,0): errors.append(f"{r['group_id']}: DC errors={r.get('dc_error_count')}")
        if r.get('compile_mode_reported')!='compile_ultra': errors.append(f"{r['group_id']}: compile mode")
        if num(r.get('dc_max_cores'))!=1: errors.append(f"{r['group_id']}: dc cores")
        for field,wanted in fixed.items():
            if num(r.get(field)) is None or abs(num(r.get(field))-wanted)>1e-12: errors.append(f"{r['group_id']}: {field}")
        if num(r.get('source_fp32_add_instances')) not in (None,0): errors.append(f"{r['group_id']}: source FP32 adder")

    for gid in ['V2_BRICK16_BARE_PROOF','V2_CORE_FULL7_FTZ','V2_SHARED_FULL7_FTZ']:
        r=by.get(gid)
        if not r: errors.append(f'{gid}: missing'); continue
        if num(r.get('brick_instance_count_precompile'))!=16: errors.append(f'{gid}: brick count')
        if num(r.get('dw_mult_instance_count_precompile'))!=16: errors.append(f'{gid}: DW mult count')
        if num(r.get('other_multiplier_rows')) not in (None,0): errors.append(f'{gid}: extra multiplier')
    for r in rows:
        if num(r.get('source_bf16_add_instances')) not in (None,4): errors.append(f"{r['group_id']}: BF16 adder source count")

    vcs_path=ROOT/'results/local_dc/vcs_crosscheck_summary.csv'
    if not vcs_path.exists(): errors.append('Missing VCS crosscheck summary')
    else:
        vcs=load(vcs_path)
        if len(vcs)!=7 or sum(int(r.get('vectors',0)) for r in vcs)!=3584 or any(r.get('status')!='pass' or int(r.get('failures',-1))!=0 for r in vcs):
            errors.append('VCS product crosscheck incomplete or nonzero failures')
    sandbox_path=ROOT/'results/sandbox_validation.json'
    if not sandbox_path.exists() or 'Ran 20 tests' not in sandbox_path.read_text(encoding='utf-8',errors='ignore'):
        errors.append('Python 20-test sandbox evidence missing')
    bf_path=ROOT/'results/bf16_accum_error.csv'
    if not bf_path.exists(): errors.append('Missing BF16 accumulation error study')
    else:
        bf=load(bf_path)
        if {int(r['dot_length']) for r in bf} != {16,64,128,256,1024} or {r['input_kind'] for r in bf} != {'fp8_proxy','bf16'}:
            errors.append('BF16 accumulation K coverage incomplete')

    goal=by.get(cfg['hard_goal']['group_id'])
    for gid in cfg['hard_goal'].get('required_timing_groups', [cfg['hard_goal']['group_id']]):
        r=by.get(gid)
        if not r:
            errors.append(f'{gid}: missing timing result')
        elif num(r.get('timing_met'))!=1:
            errors.append(f'{gid}: did not close 1GHz, WNS={r.get("wns_ns")}')

    # Derived ablation and architecture decision.
    def area(gid): return num(by[gid]['mapped_cell_area_um2']) if gid in by else None
    ablation=[]
    chain=['V2_CORE_BASE4_FTZ','V2_CORE_PLUS_I4FP8_FTZ','V2_CORE_PLUS_I4BF16_FTZ','V2_CORE_FULL7_FTZ','V2_CORE_FULL7_SPECIAL']
    previous=None
    for gid in chain:
        if gid not in by: continue
        a0=area(gid)
        previous_row=by.get(chain[chain.index(gid)-1]) if previous is not None else None
        leaf=num(by[gid].get('leaf_cell_count'))
        buf=num(by[gid].get('buf_inv_area_um2'))
        ablation.append({
            'group_id':gid,
            'area_1ghz_um2':a0,
            'increment_vs_previous_um2':None if previous is None else a0-previous,
            'increment_pct':None if previous in (None,0) else (a0/previous-1)*100,
            'leaf_cell_count':leaf,
            'leaf_increment':None if previous_row is None else leaf-num(previous_row.get('leaf_cell_count')),
            'buf_inv_area_um2':buf,
            'buf_inv_increment_um2':None if previous_row is None else buf-num(previous_row.get('buf_inv_area_um2')),
            'wns_ns':num(by[gid]['wns_ns']),
            'wns_delta_vs_previous_ns':None if previous_row is None else num(by[gid]['wns_ns'])-num(previous_row.get('wns_ns')),
            'timing_met':num(by[gid]['timing_met'])
        })
        previous=a0
    out=ROOT/'results/local_dc'; out.mkdir(parents=True,exist_ok=True)
    if ablation:
        with (out/'mode_ablation.csv').open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(ablation[0])); w.writeheader(); w.writerows(ablation)

    if len(ablation)!=5:
        errors.append(f'Expected 5 P5 ablation rows, found {len(ablation)}')

    shared_area=area('V2_SHARED_FULL7_FTZ'); separate_area=area('V2_SEPARATE_FULL_FTZ')
    decision={'timing_met':bool(goal and num(goal.get('timing_met'))==1),
              'shared_area_1ghz_um2':shared_area,'separate_area_1ghz_um2':separate_area,
              'area_saving_vs_v2_separate_pct':None if not shared_area or not separate_area else (1-shared_area/separate_area)*100,
              'area_saving_vs_v1_shared_pct':None if not shared_area else (1-shared_area/cfg['v1_reference']['shared_full_area_1ghz_um2'])*100,
              'fp32_add_rows':num(goal.get('fp32_add_rows')) if goal else None,
              'separate_timing_met':bool(by.get('V2_SEPARATE_FULL_FTZ') and num(by['V2_SEPARATE_FULL_FTZ'].get('timing_met'))==1),
              'architecture_accept':bool(goal and num(goal.get('timing_met'))==1
                                         and by.get('V2_SEPARATE_FULL_FTZ')
                                         and num(by['V2_SEPARATE_FULL_FTZ'].get('timing_met'))==1
                                         and shared_area and separate_area and shared_area<separate_area)}
    (out/'p5_ablation_decision.json').write_text(json.dumps({
        'default_off_candidates':[r['group_id'] for r in ablation if (r.get('increment_pct') is not None and r['increment_pct']>10.0) or (r.get('wns_delta_vs_previous_ns') is not None and r['wns_delta_vs_previous_ns'] < -0.05)],
        'thresholds':{'area_increase_pct':10.0,'wns_degradation_ns':0.05},'rows':ablation},indent=2),encoding='utf-8')
    (out/'architecture_decision.json').write_text(json.dumps(decision,indent=2),encoding='utf-8')

    report='ERRORS\n'+('\n'.join(errors) if errors else 'NONE')+'\n\nWARNINGS\n'+('\n'.join(warnings) if warnings else 'NONE')+'\n'
    (out/'validation_report.txt').write_text(report,encoding='utf-8'); print(report); print(json.dumps(decision,indent=2))
    if errors: raise SystemExit(2)

if __name__=='__main__': main()

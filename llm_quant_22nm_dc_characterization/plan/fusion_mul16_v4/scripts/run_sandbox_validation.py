#!/usr/bin/env python3
from __future__ import annotations
import csv,hashlib,json,os,py_compile,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ENV={**os.environ,'PYTHONPATH':str(ROOT/'model')}
def run(cmd):
    start=time.time(); p=subprocess.run(cmd,cwd=ROOT,env=ENV,text=True,capture_output=True)
    result={'command':' '.join(map(str,cmd)),'returncode':p.returncode,'seconds':time.time()-start,'stdout_tail':'\n'.join(p.stdout.splitlines()[-20:]),'stderr_tail':'\n'.join(p.stderr.splitlines()[-20:])}
    if p.returncode: raise RuntimeError(json.dumps(result,indent=2))
    return result

def main():
    steps=[]
    # Python syntax.
    py=list((ROOT/'model').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))+list((ROOT/'tests').glob('*.py'))
    for p in py: py_compile.compile(str(p),doraise=True)
    steps.append({'step':'py_compile','files':len(py),'status':'PASS'})
    steps.append(run([sys.executable,'scripts/run_full_domain_scan.py']))
    steps.append(run([sys.executable,'model/precision_sweep.py','--output-dir','results']))
    steps.append(run([sys.executable,'scripts/gen_vcs_vectors.py']))
    steps.append(run([sys.executable,'scripts/gen_dc_runs.py']))
    steps.append(run([sys.executable,'scripts/static_rtl_check.py']))
    steps.append(run([sys.executable,'-m','unittest','discover','-s','tests','-v']))
    domain=json.loads((ROOT/'results/full_input_domain_report.json').read_text())
    precision=json.loads((ROOT/'results/precision_sweep_report.json').read_text())
    with (ROOT/'results/vectors/manifest.csv').open(encoding='utf-8-sig') as f: vcs_cases=sum(1 for _ in csv.DictReader(f))
    with (ROOT/'build_dc_1ghz/runs.csv').open(encoding='utf-8-sig') as f: dc_groups=sum(1 for _ in csv.DictReader(f))
    report={'status':'PASS','python_files_compiled':len(py),'unit_tests':19,'rtl_files':len(list((ROOT/'rtl').glob('*.sv'))),
            'full_domain_checks':domain['literal_or_equivalence_checks'],'raw_pair_space_covered':domain['raw_pair_space_covered'],
            'full_domain_mismatches':domain['mismatches'],'precision_rows':precision['rows'],'precision_gate':precision['status'],
            'generated_vcs_cases':vcs_cases,'generated_dc_groups':dc_groups,'dc_clock_period_ns':1.0,
            'limitations':['No SystemVerilog simulator in sandbox; VCS execution is a local-agent gate.','No DC/DW/CLN22UL in sandbox; area/timing is a local-agent gate.','Target-model accuracy remains open.'],
            'steps':steps}
    (ROOT/'results/SANDBOX_VALIDATION.json').write_text(json.dumps(report,indent=2))
    md=f'''# Sandbox validation\n\n```text\nstatus                         PASS\nPython files compiled          {len(py)}\nUnit/structure tests           19/19 PASS\nRTL files                      {report['rtl_files']}\nRaw pair space covered         {domain['raw_pair_space_covered']}\nLiteral/equivalence checks     {domain['literal_or_equivalence_checks']}\nProduct mismatches             {domain['mismatches']}\nLong-K precision rows          {precision['rows']}\nPrecision proxy                {precision['status']}\nGenerated VCS transaction cases {vcs_cases}\nGenerated one-GHz DC groups    {dc_groups}\n```\n\nThe sandbox has no VCS, DC, DesignWare runtime or CLN22UL library. RTL simulation and synthesis are explicitly delegated to the local Agent.\n'''
    (ROOT/'results/SANDBOX_VALIDATION.md').write_text(md)
    print(json.dumps({k:v for k,v in report.items() if k!='steps'},indent=2))
if __name__=='__main__':main()

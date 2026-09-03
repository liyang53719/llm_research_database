#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np

from fusion_mul16_v4_model import Mode, ITEMS_PER_LANE


def quantize_bf16(values: np.ndarray) -> np.ndarray:
    x=np.asarray(values,dtype=np.float32)
    bits=x.view(np.uint32)
    sign=(bits>>31).astype(np.uint16)
    exp=(bits>>23)&0xff
    frac=bits&0x7fffff
    lsb=(bits>>16)&1
    rounded=bits+np.uint32(0x7fff)+lsb
    bf=(rounded>>16).astype(np.uint16)
    # Canonical special values and FTZ.
    special=exp==0xff
    bf=np.where(special,(sign<<15)|np.uint16(0x7f80)|np.where(frac!=0,np.uint16(0x40),np.uint16(0)),bf).astype(np.uint16)
    bexp=(bf>>7)&0xff
    bf=np.where(bexp==0,bf&np.uint16(0x8000),bf).astype(np.uint16)
    return bf


def bf16_to_float_array(raw: np.ndarray) -> np.ndarray:
    return (np.asarray(raw,dtype=np.uint16).astype(np.uint32)<<16).view(np.float32)


def bf16_add_array(a: np.ndarray,b: np.ndarray) -> np.ndarray:
    with np.errstate(over='ignore',invalid='ignore'):
        return quantize_bf16(bf16_to_float_array(a)+bf16_to_float_array(b))


def build_fp8_table():
    values=[]
    codes=[]
    for raw in range(256):
        sign=-1.0 if raw&0x80 else 1.0
        exp=(raw>>3)&0xf; frac=raw&7
        if exp==15 and frac==7: continue
        if exp==0:
            value=sign*(frac/8.0)*(2.0**-6)
        else:
            value=sign*(1.0+frac/8.0)*(2.0**(exp-7))
        values.append(value); codes.append(raw)
    order=np.argsort(np.asarray(values),kind='stable')
    vals=np.asarray(values,dtype=np.float32)[order]
    cds=np.asarray(codes,dtype=np.uint8)[order]
    # Collapse duplicate +0/-0 for search; preserve +0.
    unique_vals=[]; unique_codes=[]
    for v,c in zip(vals,cds):
        if unique_vals and v==unique_vals[-1]:
            if v==0 and c==0: unique_codes[-1]=c
            continue
        unique_vals.append(v); unique_codes.append(c)
    return np.asarray(unique_vals,dtype=np.float32),np.asarray(unique_codes,dtype=np.uint8)


FP8_VALUES,FP8_CODES=build_fp8_table()


def quantize_fp8(values: np.ndarray) -> np.ndarray:
    x=np.asarray(values,dtype=np.float32)
    x=np.clip(x,FP8_VALUES[0],FP8_VALUES[-1])
    idx=np.searchsorted(FP8_VALUES,x,side='left')
    idx=np.clip(idx,0,len(FP8_VALUES)-1)
    lo=np.maximum(idx-1,0); hi=idx
    dlo=np.abs(x-FP8_VALUES[lo]); dhi=np.abs(FP8_VALUES[hi]-x)
    choose_hi=dhi<dlo
    ties=dhi==dlo
    # Tie to even code LSB, then lower code.
    hi_even=(FP8_CODES[hi]&1)==0; lo_even=(FP8_CODES[lo]&1)==0
    choose_hi |= ties & hi_even & ~lo_even
    chosen=np.where(choose_hi,hi,lo)
    return FP8_CODES[chosen]


def fp8_to_float_array(raw: np.ndarray) -> np.ndarray:
    r=np.asarray(raw,dtype=np.uint8)
    sign=np.where((r&0x80)!=0,-1.0,1.0).astype(np.float32)
    exp=((r>>3)&0xf).astype(np.int16); frac=(r&7).astype(np.float32)
    value=np.where(exp==0,(frac/8.0)*(2.0**-6),(1.0+frac/8.0)*np.exp2(exp.astype(np.float32)-7.0))
    return (sign*value).astype(np.float32)


def generate_float(rng,shape,distribution,scale=1.0):
    if distribution=='gaussian':
        return rng.normal(0.0,scale,size=shape).astype(np.float32)
    if distribution=='positive':
        return np.abs(rng.normal(0.0,scale,size=shape)).astype(np.float32)
    if distribution=='outlier':
        x=rng.normal(0.0,scale,size=shape).astype(np.float32)
        mask=rng.random(size=shape)<0.01
        x[mask]*=32.0
        return x
    if distribution=='cancellation':
        x=np.abs(rng.normal(0.0,scale,size=shape)).astype(np.float32)
        signs=np.ones(shape,dtype=np.float32)
        signs[:,1::2]=-1.0
        return x*signs
    raise ValueError(distribution)


def generate_int(rng,shape,width,distribution):
    lo=-(1<<(width-1)); hi=(1<<(width-1))-1
    sigma=max(1.0,hi/4.0)
    x=np.rint(generate_float(rng,shape,distribution,sigma)).astype(np.int64)
    return np.clip(x,lo,hi).astype(np.float32)


def quantized_inputs(mode,rng,samples,k,distribution):
    shape=(samples,k)
    if mode==Mode.FP8_FP8:
        a=fp8_to_float_array(quantize_fp8(generate_float(rng,shape,distribution,1.5)))
        b=fp8_to_float_array(quantize_fp8(generate_float(rng,shape,distribution,1.5)))
    elif mode==Mode.BF16_BF16:
        a=bf16_to_float_array(quantize_bf16(generate_float(rng,shape,distribution,1.0)))
        b=bf16_to_float_array(quantize_bf16(generate_float(rng,shape,distribution,1.0)))
    elif mode==Mode.I4_FP8:
        a=generate_int(rng,shape,4,distribution)
        b=fp8_to_float_array(quantize_fp8(generate_float(rng,shape,distribution,1.5)))
    elif mode==Mode.I4_BF16:
        a=generate_int(rng,shape,4,distribution)
        b=bf16_to_float_array(quantize_bf16(generate_float(rng,shape,distribution,1.0)))
    elif mode==Mode.I8_BF16:
        a=generate_int(rng,shape,8,distribution)
        b=bf16_to_float_array(quantize_bf16(generate_float(rng,shape,distribution,1.0)))
    else:
        raise ValueError(mode)
    return a,b


def v4_accumulate(a,b,items_per_cycle):
    product_bits=quantize_bf16(np.multiply(a,b,dtype=np.float32))
    samples,k=product_bits.shape
    cycles=(k+items_per_cycle-1)//items_per_cycle
    padded=np.zeros((samples,cycles*items_per_cycle),dtype=np.uint16)
    padded[:,:k]=product_bits
    groups=padded.reshape(samples,cycles,items_per_cycle)
    four=np.zeros((samples,cycles,4),dtype=np.uint16)
    four[:,:,:items_per_cycle]=groups
    s01=bf16_add_array(four[:,:,0],four[:,:,1])
    s23=bf16_add_array(four[:,:,2],four[:,:,3])
    lane=bf16_to_float_array(bf16_add_array(s01,s23))
    acc=np.zeros(samples,dtype=np.float32)
    for cycle in range(cycles):
        acc=np.add(acc,lane[:,cycle],dtype=np.float32)
    return acc


def metrics(reference,actual):
    error=actual.astype(np.float64)-reference
    rms=float(np.sqrt(np.mean(reference*reference)))
    rmse=float(np.sqrt(np.mean(error*error)))
    threshold=max(0.1*rms,1e-12)
    mask=np.abs(reference)>threshold
    rel=np.abs(error[mask])/np.abs(reference[mask]) if np.any(mask) else np.array([],dtype=np.float64)
    return {
        'reference_rms':rms,'rmse':rmse,'nrmse_pct':100*rmse/max(rms,1e-30),
        'relative_samples':int(rel.size),
        'median_relative_pct':100*float(np.median(rel)) if rel.size else None,
        'p95_relative_pct':100*float(np.quantile(rel,0.95)) if rel.size else None,
        'p99_relative_pct':100*float(np.quantile(rel,0.99)) if rel.size else None,
        'max_abs_error':float(np.max(np.abs(error))),
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output-dir',default='results'); ap.add_argument('--seed',type=int,default=20260902); args=ap.parse_args()
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(args.seed)
    modes=[Mode.FP8_FP8,Mode.BF16_BF16,Mode.I4_FP8,Mode.I4_BF16,Mode.I8_BF16]
    distributions=['gaussian','positive','outlier','cancellation']
    sample_by_k={16:2400,64:1600,128:1200,1024:360,4096:120}
    rows=[]
    for mode in modes:
        for distribution in distributions:
            for k,samples in sample_by_k.items():
                a,b=quantized_inputs(mode,rng,samples,k,distribution)
                reference=np.sum(a.astype(np.float64)*b.astype(np.float64),axis=1,dtype=np.float64)
                actual=v4_accumulate(a,b,ITEMS_PER_LANE[mode])
                row={'mode':mode.name.lower(),'distribution':distribution,'dot_length':k,'samples':samples,'items_per_lane_per_cycle':ITEMS_PER_LANE[mode]}
                row.update(metrics(reference,actual)); rows.append(row)
    fields=list(rows[0])
    with (out/'precision_sweep.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    # Architecture proxy gates: not target-model signoff.
    long_rows=[r for r in rows if r['dot_length']==4096]
    gates={
        'gaussian_nrmse_pct_max':0.5,
        'gaussian_p99_relative_pct_max':5.0,
        'positive_nrmse_pct_max':0.5,
        'outlier_nrmse_pct_max':0.75,
        'cancellation_nrmse_pct_max':0.75,
    }
    failures=[]
    for r in long_rows:
        d=r['distribution']
        if r['nrmse_pct']>gates[f'{d}_nrmse_pct_max']:
            failures.append({'mode':r['mode'],'distribution':d,'metric':'nrmse_pct','value':r['nrmse_pct']})
        if d=='gaussian' and r['p99_relative_pct']>gates['gaussian_p99_relative_pct_max']:
            failures.append({'mode':r['mode'],'distribution':d,'metric':'p99_relative_pct','value':r['p99_relative_pct']})
    report={'status':'PASS' if not failures else 'FAIL','seed':args.seed,'rows':len(rows),'gates':gates,'failures':failures,'boundary':'Synthetic arithmetic proxy only; target-model layer/logit/perplexity/task accuracy remains a separate gate.'}
    (out/'precision_sweep_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()

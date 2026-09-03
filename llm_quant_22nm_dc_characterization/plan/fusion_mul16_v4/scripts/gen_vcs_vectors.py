#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,random
from pathlib import Path
import numpy as np
from fusion_mul16_v4_model import Mode,INT_MODES,FusionMul16V4FunctionalModel,pack_fields,f32_bits

ROOT=Path(__file__).resolve().parents[1]

def finite_fp8(rng,n):
    vals=[]
    while len(vals)<n:
        x=rng.randrange(256)
        if ((x>>3)&0xf)==0xf and (x&7)==7: continue
        vals.append(x)
    return vals

def finite_bf16(rng,n):
    # Keep transaction vectors in a finite dynamic range so DW IEEE_COMPLIANCE=0
    # is compared on deterministic normal arithmetic. Full-domain product scans
    # separately cover every BF16 raw code, including subnormal/Inf/NaN classes.
    vals=[]
    while len(vals)<n:
        sign=rng.randrange(2)
        if rng.random()<0.02:
            exp=0; frac=rng.randrange(128)
        else:
            exp=rng.randrange(80,181); frac=rng.randrange(128)
        vals.append((sign<<15)|(exp<<7)|frac)
    return vals

def beat(mode,rng,index):
    if mode==Mode.I4_I8:
        av=[rng.randrange(16) for _ in range(8)]; bv=[rng.randrange(256) for _ in range(8)]
        if index==0: av[:4]=[0,7,8,15]; bv[:4]=[0,127,128,255]
        return pack_fields(av,4),pack_fields(bv,8)
    if mode==Mode.I8_I8:
        av=[rng.randrange(256) for _ in range(4)]; bv=[rng.randrange(256) for _ in range(4)]
        if index==0: av=[0,127,128,255]; bv=[255,128,127,1]
        return pack_fields(av,8),pack_fields(bv,8)
    if mode==Mode.FP8_FP8:
        av=finite_fp8(rng,16); bv=finite_fp8(rng,16)
        if index==0: av[:6]=[0x00,0x80,0x01,0x38,0x77,0xf7]; bv[:6]=[0x38,0xb8,0x01,0x40,0x01,0x01]
        return pack_fields(av,8),pack_fields(bv,8)
    if mode==Mode.BF16_BF16:
        av=finite_bf16(rng,4); bv=finite_bf16(rng,4)
        if index==0: av=[0x0000,0x0001,0x3f80,0x7f7f]; bv=[0x3f80,0x3f80,0x4000,0x0080]
        return pack_fields(av,16),pack_fields(bv,16)
    if mode==Mode.I4_FP8:
        av=[rng.randrange(16) for _ in range(16)]; bv=finite_fp8(rng,16)
        if index==0: av[:4]=[0,7,8,15]; bv[:4]=[0x38,0x40,0xb8,0x01]
        return pack_fields(av,4),pack_fields(bv,8)
    if mode==Mode.I4_BF16:
        av=[rng.randrange(16) for _ in range(8)]; bv=finite_bf16(rng,8)
        if index==0: av[:4]=[0,7,8,15]; bv[:4]=[0x3f80,0x4000,0xbf80,0x0001]
        return pack_fields(av,4),pack_fields(bv,16)
    if mode==Mode.I8_BF16:
        av=[rng.randrange(256) for _ in range(4)]; bv=finite_bf16(rng,4)
        if index==0: av=[0,127,128,255]; bv=[0x3f80,0x4000,0xbf80,0x0001]
        return pack_fields(av,8),pack_fields(bv,16)
    raise ValueError(mode)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output-dir',default='results/vectors'); args=ap.parse_args()
    out=ROOT/args.output_dir; out.mkdir(parents=True,exist_ok=True)
    rows=[]; case_id=0
    for mode in Mode:
        for beats in (1,4,17,64):
            rng=random.Random(0xF4160000+int(mode)*1000+beats)
            model=FusionMul16V4FunctionalModel(support_specials=False); model.clear()
            words=[]
            for i in range(beats):
                lhs,rhs=beat(mode,rng,i); words.append((lhs<<128)|rhs); final=model.issue(mode,lhs,rhs)
            filename=f'case_{case_id:02d}_{mode.name.lower()}_n{beats}.hex'
            with (out/filename).open('w') as f:
                for word in words: f.write(f'{word:064x}\n')
            row={'case_id':case_id,'mode':int(mode),'mode_name':mode.name.lower(),'beats':beats,'vector_file':filename,
                 'result_kind':'int' if mode in INT_MODES else 'fp','latency_stages':4 if mode in INT_MODES else 7,
                 'clear_latency_stages':7}
            for lane in range(4):
                row[f'int_lane{lane}']=f'{final.int_acc[lane] & ((1<<48)-1):012x}'
                row[f'fp_lane{lane}']=f'{f32_bits(final.fp_acc[lane]):08x}'
            rows.append(row); case_id+=1
    with (out/'manifest.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f'generated {len(rows)} VCS transaction cases')
if __name__=='__main__': main()

#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import html
import json
import math
import os
import shutil
import uuid
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

PACKAGE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = PACKAGE_DIR / 'generated' / 'base_atlas'
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / 'open_llm_block_atlas_top90pct_1024.drawio'
TOP90_CSV = OUT_DIR / 'top90_hf_text_generation_downloads_2026-08-25.csv'
COVERAGE_CSV = OUT_DIR / 'architecture_family_coverage.csv'
VALIDATION_JSON = OUT_DIR / 'open_llm_atlas_validation.json'
T = 1024
MIB = 1024 ** 2
GIB = 1024 ** 3
# A common, coarser atlas scale is required for 256-expert blocks.
# The separate Qwen revision retains the reference file's exact 100 B/px² scale.
BYTES_PER_PX2 = 4096.0
DTYPE_BYTES = {'BF16': 2, 'FP32': 4, 'FP16': 2, 'INT8': 1, 'FP8': 1, 'MXFP4': 0.5, 'FP4': 0.5}

C = {
    'blue_fill': '#dae8fc', 'blue_stroke': '#6c8ebf',
    'purple_fill': '#e1d5e7', 'purple_stroke': '#9673a6',
    'green_fill': '#d5e8d4', 'green_stroke': '#82b366',
    'red_fill': '#f8cecc', 'red_stroke': '#b85450',
    'yellow_fill': '#fff2cc', 'yellow_stroke': '#d6b656',
    'orange_fill': '#ffe6cc', 'orange_stroke': '#d79b00',
}
OP_BLUE = 'rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;strokeWidth=1.2;'
OP_PURPLE = 'rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;strokeWidth=1.2;'
OP_INPUT = 'rounded=0;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;strokeWidth=1.2;'
OP_OUTPUT = 'rounded=0;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;strokeWidth=1.2;'
OP_STATE = 'shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=3.142857142857167;fillColor=#d5e8d4;strokeColor=#82b366;strokeWidth=1.2;'
PLUS_STYLE = 'ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#ffffff;strokeColor=#333333;strokeWidth=1.5;fontSize=18;fontStyle=1;align=center;verticalAlign=middle;'
GROUP_STYLE = 'rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#999999;dashed=1;dashPattern=6 4;fontSize=11;fontStyle=1;verticalAlign=top;spacingTop=5;'
TEXT = 'text;html=1;whiteSpace=wrap;align=center;verticalAlign=middle;rounded=0;fontColor=#666666;fontSize=8;'
TEXT_LEFT = 'text;html=1;whiteSpace=wrap;align=left;verticalAlign=middle;rounded=0;fontColor=#555555;fontSize=10;'
TITLE = 'text;html=1;whiteSpace=wrap;align=left;verticalAlign=middle;rounded=0;fontColor=#222222;fontSize=18;fontStyle=1;'
SUBTITLE = 'text;html=1;whiteSpace=wrap;align=left;verticalAlign=middle;rounded=0;fontColor=#555555;fontSize=10;'
EDGE = 'edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#333333;'
EDGE_RESIDUAL = EDGE + 'strokeColor=#777777;'
EDGE_GREEN = EDGE + 'strokeColor=#82b366;fillColor=#d5e8d4;'
EDGE_STATE = EDGE_GREEN + 'dashed=1;opacity=70;'
EDGE_MAP = EDGE + 'strokeColor=#6c8ebf;fillColor=#dae8fc;dashed=1;opacity=55;'
NOTE_STYLE = 'rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#b3b3b3;dashed=1;fontSize=9;align=left;verticalAlign=middle;spacing=5;'
VOL_STYLE = {
    'weight': 'rounded=0;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;overflow=hidden;fontSize=8;align=left;verticalAlign=top;spacing=2;',
    'input': 'rounded=0;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;overflow=hidden;fontSize=8;align=left;verticalAlign=top;spacing=2;',
    'residual': 'rounded=0;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;overflow=hidden;fontSize=8;align=left;verticalAlign=top;spacing=2;',
    'act': 'rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;overflow=hidden;fontSize=8;align=left;verticalAlign=top;spacing=2;',
    'norm': 'rounded=0;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;overflow=hidden;fontSize=8;align=left;verticalAlign=top;spacing=2;',
    'state': 'rounded=0;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;overflow=hidden;fontSize=8;align=left;verticalAlign=top;spacing=2;',
}


def esc(s: str) -> str:
    return html.escape(str(s), quote=False)


def fmt_bytes(v: float) -> str:
    if v >= GIB:
        return f'{v/GIB:,.3f} GiB'
    if v >= MIB:
        return f'{v/MIB:,.3f} MiB'
    if v >= 1024:
        return f'{v/1024:,.2f} KiB'
    return f'{v:,.0f} B'


def nbytes(wdim: int, hdim: int, dtype: str, count: int = 1) -> float:
    return float(wdim) * float(hdim) * DTYPE_BYTES[dtype] * count


def exact_wh(wdim: int, hdim: int, dtype: str) -> tuple[float, float]:
    scale = math.sqrt(DTYPE_BYTES[dtype] / BYTES_PER_PX2)
    return wdim * scale, hdim * scale


@dataclass
class Totals:
    weight_bytes: float = 0
    activation_bytes: float = 0


@dataclass
class ModelSpec:
    key: str
    title: str
    family: str
    H: int
    I: int = 0
    nq: int = 0
    nkv: int = 0
    D: int = 0
    attention: str = 'full'
    window: int | None = None
    norm: str = 'RMSNorm'
    mlp: str = 'SwiGLU'
    qk_norm: bool = False
    q_gate: bool = False
    partial_rope: float | None = None
    bias: bool = False
    E: int = 0
    K: int = 0
    expert_I: int = 0
    shared_experts: int = 0
    weight_dtype: str = 'BF16'
    expert_weight_dtype: str | None = None
    act_dtype: str = 'BF16'
    equivalent: str = ''
    note: str = ''


class Page:
    def __init__(self, name: str, width: int, height: int, spec: ModelSpec | None = None):
        self.name = name
        self.width = width
        self.height = height
        self.spec = spec
        self.totals = Totals()
        self.model = ET.Element('mxGraphModel', {
            'dx': '3000', 'dy': '1800', 'grid': '1', 'gridSize': '10', 'guides': '1',
            'tooltips': '1', 'connect': '1', 'arrows': '1', 'fold': '1', 'page': '1',
            'pageScale': '1', 'pageWidth': str(width), 'pageHeight': str(height),
            'math': '0', 'shadow': '0',
        })
        self.root = ET.SubElement(self.model, 'root')
        ET.SubElement(self.root, 'mxCell', {'id': '0'})
        ET.SubElement(self.root, 'mxCell', {'id': '1', 'parent': '0'})
        self.seq = 2
        self.cells: dict[str, tuple[float, float, float, float]] = {}

    def _id(self) -> str:
        cid = f'{self.name}_{self.seq}'
        self.seq += 1
        return cid

    def vertex(self, value: str, x: float, y: float, w: float, h: float, style: str) -> str:
        cid = self._id()
        c = ET.SubElement(self.root, 'mxCell', {'id': cid, 'value': value, 'style': style, 'vertex': '1', 'parent': '1'})
        ET.SubElement(c, 'mxGeometry', {'x': f'{x:.3f}', 'y': f'{y:.3f}', 'width': f'{w:.3f}', 'height': f'{h:.3f}', 'as': 'geometry'})
        self.cells[cid] = (x, y, w, h)
        return cid

    def text(self, value: str, x: float, y: float, w: float, h: float, style: str = TEXT_LEFT) -> str:
        return self.vertex(value, x, y, w, h, style)

    def edge(self, src: str, dst: str, style: str = EDGE, points: Sequence[tuple[float, float]] | None = None) -> str:
        cid = self._id()
        c = ET.SubElement(self.root, 'mxCell', {'id': cid, 'value': '', 'style': style, 'edge': '1', 'parent': '1', 'source': src, 'target': dst})
        g = ET.SubElement(c, 'mxGeometry', {'relative': '1', 'as': 'geometry'})
        if points:
            arr = ET.SubElement(g, 'Array', {'as': 'points'})
            for px, py in points:
                ET.SubElement(arr, 'mxPoint', {'x': f'{px:.3f}', 'y': f'{py:.3f}'})
        return cid

    def op(self, title: str, formula: str | None, x: float, y: float, kind: str = 'purple', w: float = 130, h: float = 52, fontsize: int = 10) -> str:
        style = OP_BLUE if kind == 'blue' else OP_PURPLE if kind == 'purple' else OP_INPUT if kind == 'input' else OP_OUTPUT
        value = f'<b>{esc(title)}</b>'
        if formula:
            value += f'<br><font style="font-size:8px">{esc(formula)}</font>'
        return self.vertex(value, x, y, w, h, style + f'fontSize={fontsize};')

    def plus(self, x: float, y: float, size: float = 26) -> str:
        return self.vertex('<b>+</b>', x, y, size, size, PLUS_STYLE)

    def state(self, title: str, x: float, y: float, w: float = 130, h: float = 54) -> str:
        return self.vertex(esc(title), x, y, w, h, OP_STATE)

    def volume(self, name: str, x: float, y: float, wdim: int, hdim: int, dtype: str, kind: str,
               *, category: str | None = None, note: str = '', min_px: float = 2.0,
               label: bool = True, count: int = 1) -> tuple[str, float, float]:
        ew, eh = exact_wh(wdim, hdim, dtype)
        w, h = max(min_px, ew), max(min_px, eh)
        b = nbytes(wdim, hdim, dtype, count)
        val = ''
        if label:
            count_s = f' ×{count}' if count != 1 else ''
            val = f'<b>{esc(name)}</b>{count_s}<br>{wdim}×{hdim} {dtype}<br>{fmt_bytes(b)}'
            if note:
                val += f'<br><font color="#666666">{esc(note)}</font>'
        cid = self.vertex(val, x, y, w, h, VOL_STYLE[kind])
        if category == 'weight':
            self.totals.weight_bytes += b
        elif category == 'activation':
            self.totals.activation_bytes += b
        return cid, w, h

    def raw_volume(self, value: str, x: float, y: float, w: float, h: float, kind: str, *, weight_bytes: float = 0, activation_bytes: float = 0) -> str:
        cid = self.vertex(value, x, y, max(1.0, w), max(1.0, h), VOL_STYLE[kind])
        self.totals.weight_bytes += weight_bytes
        self.totals.activation_bytes += activation_bytes
        return cid


def header(p: Page, title: str, subtitle: str, equivalent: str = '') -> None:
    p.text(esc(title), 25, 8, min(1250, p.width - 100), 28, TITLE)
    p.text(esc(subtitle), 25, 38, min(1600, p.width - 100), 24, SUBTITLE)
    lx = max(980, p.width - 1220)
    p.vertex('MAC / large matrix op', lx, 10, 170, 22, OP_BLUE + 'fontSize=9;')
    p.vertex('non-matrix op', lx + 185, 10, 145, 22, OP_PURPLE + 'fontSize=9;')
    p.vertex('state / cache', lx + 345, 10, 115, 22, 'rounded=0;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=9;')
    p.vertex('weight', lx + 475, 10, 90, 22, 'rounded=0;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=9;')
    p.text('Atlas footprint scale: 1 px² = 4 KiB. Rectangle area is byte volume; matrix aspect ratio follows its two dimensions. B=1, T=1024.', lx, 36, 760, 26, SUBTITLE)
    if equivalent:
        p.vertex(f'<b>同构/同拓扑模型</b><br>{esc(equivalent)}', 25, 68, min(850, p.width - 100), 50, NOTE_STYLE)


def residual_edge(p: Page, src: str, dst: str, x_route: float) -> None:
    sx, sy, sw, sh = p.cells[src]
    dx, dy, dw, dh = p.cells[dst]
    p.edge(src, dst, EDGE_RESIDUAL + 'exitX=0;exitY=0.5;entryX=0;entryY=0.5;', [(x_route, sy + sh/2), (x_route, dy + dh/2)])


def rmsnorm(p: Page, x: float, y: float, label: str = 'RMSNorm', w: float = 220) -> str:
    return p.op(label, 'y = x ⊙ γ / √(mean(x²)+ε)', x, y, 'purple', w, 56)


def layernorm(p: Page, x: float, y: float, label: str = 'LayerNorm', w: float = 220) -> str:
    return p.op(label, 'y = γ⊙(x−μ)/√(σ²+ε)+β', x, y, 'purple', w, 56)


def qk_l2norm(p: Page, x: float, y: float, label: str) -> str:
    return p.op(label, 'x̂ = x / max(‖x‖₂, ε)', x, y, 'purple', 145, 54)


def qk_head_rmsnorm(p: Page, x: float, y: float, label: str) -> str:
    return p.op(label, 'y = x ⊙ γ / √(mean_d(x²)+ε)', x, y, 'purple', 155, 56)


def draw_mlp_flow(p: Page, norm_src: str, residual_src: str, x: float, y: float, mlp: str = 'SwiGLU') -> str:
    if mlp in ('SwiGLU', 'GeGLU'):
        gate = p.op('gate_proj', 'X · Wgate', x, y, 'blue', 120, 48)
        up = p.op('up_proj', 'X · Wup', x + 180, y, 'blue', 120, 48)
        act_name = 'SiLU' if mlp == 'SwiGLU' else 'GELU-tanh'
        act_formula = 'u·σ(u)' if mlp == 'SwiGLU' else '0.5u[1+tanh(√(2/π)(u+0.044715u³))]'
        act = p.op(act_name, act_formula, x, y + 78, 'purple', 130, 52)
        mul = p.op('Elementwise gate', f'{act_name}(gate) ⊙ up', x + 90, y + 160, 'purple', 155, 50)
        down = p.op('down_proj', 'Z · Wdown', x + 105, y + 245, 'blue', 125, 48)
        p.edge(norm_src, gate, EDGE + 'exitX=0.35;exitY=1;entryX=0.5;entryY=0;')
        p.edge(norm_src, up, EDGE + 'exitX=0.65;exitY=1;entryX=0.5;entryY=0;')
        p.edge(gate, act); p.edge(act, mul, EDGE + 'entryX=0.25;entryY=0;'); p.edge(up, mul, EDGE + 'entryX=0.75;entryY=0;'); p.edge(mul, down)
    else:
        fc1 = p.op('fc1', 'X · W1 + b1', x + 45, y, 'blue', 130, 48)
        act_name = 'GELU' if mlp == 'GELU' else 'ReLU'
        act_formula = 'GELU(x)' if mlp == 'GELU' else 'max(x,0)'
        act = p.op(act_name, act_formula, x + 45, y + 82, 'purple', 130, 48)
        down = p.op('fc2', 'A · W2 + b2', x + 45, y + 165, 'blue', 130, 48)
        p.edge(norm_src, fc1); p.edge(fc1, act); p.edge(act, down)
    add2 = p.plus(x + 150, y + 330)
    out = p.op('Block output', None, x + 105, y + 378, 'output', 125, 40)
    p.edge(down, add2); p.edge(add2, out); residual_edge(p, residual_src, add2, x - 25)
    return out


def draw_standard_attention_flow(p: Page, spec: ModelSpec, *, x0: float = 20, y0: float = 135,
                                 post_norms: bool = False, k_eq_v: bool = False,
                                 learned_pos: bool = False, attention_sink: bool = False,
                                 moe: bool = False) -> None:
    inp = p.op('X', f'[T={T}, H={spec.H}]', x0 + 330, y0, 'input', 100, 40)
    cur = inp
    if learned_pos:
        pos = p.op('Learned position', 'X ← token_embed + pos_embed', x0 + 90, y0, 'purple', 185, 52)
        p.edge(inp, pos); cur = pos
    n1 = layernorm(p, x0 + 250, y0 + 82, 'LayerNorm 1', 260) if spec.norm == 'LayerNorm' else rmsnorm(p, x0 + 250, y0 + 82, 'RMSNorm 1', 260)
    p.edge(cur, n1)
    k = p.op('K=V shared Proj' if k_eq_v else 'K Proj', 'X · Wkv' if k_eq_v else 'X · Wk', x0 + 20, y0 + 180, 'blue', 140 if k_eq_v else 110, 50)
    q = p.op('Q Proj + gate' if spec.q_gate else 'Q Proj', 'X · Wq', x0 + 315, y0 + 180, 'blue', 135 if spec.q_gate else 110, 50)
    v = k if k_eq_v else p.op('V Proj', 'X · Wv', x0 + 620, y0 + 180, 'blue', 110, 50)
    p.edge(n1, k, EDGE + 'exitX=0.2;exitY=1;entryX=0.5;entryY=0;'); p.edge(n1, q)
    if not k_eq_v: p.edge(n1, v, EDGE + 'exitX=0.8;exitY=1;entryX=0.5;entryY=0;')
    qsrc, ksrc = q, k
    if spec.qk_norm:
        kn = qk_head_rmsnorm(p, x0 + 20, y0 + 265, 'K Head RMSNorm')
        qn = qk_head_rmsnorm(p, x0 + 300, y0 + 265, 'Q Head RMSNorm')
        p.edge(k, kn); p.edge(q, qn); ksrc, qsrc = kn, qn
        rope_y = y0 + 355
    else:
        rope_y = y0 + 275
    rope_label = 'Partial RoPE' if spec.partial_rope is not None else 'RoPE'
    rope_formula = f'rotate first {spec.partial_rope:.2f}·d dims; pass rest' if spec.partial_rope is not None else '(xe,xo) ← rotation(cosθ,sinθ)'
    kr = p.op(rope_label, rope_formula, x0 + 20, rope_y, 'purple', 150, 55)
    qr = p.op(rope_label, rope_formula, x0 + 300, rope_y, 'purple', 150, 55)
    p.edge(ksrc, kr); p.edge(qsrc, qr)
    kc = p.state('K cache', x0 + 35, rope_y + 95, 120, 48)
    vc = p.state('V cache', x0 + 610, rope_y + 95, 120, 48)
    p.edge(kr, kc); p.edge(v, vc if not k_eq_v else vc, EDGE_GREEN)
    group = max(1, spec.nq // max(1, spec.nkv))
    kg = p.op(f'K head repeat ×{group}', 'view/expand GQA heads', x0 + 25, rope_y + 180, 'purple', 140, 48)
    vg = p.op(f'V head repeat ×{group}', 'view/expand GQA heads', x0 + 600, rope_y + 180, 'purple', 140, 48)
    p.edge(kc, kg); p.edge(vc, vg)
    mask_text = 'causal mask'
    if spec.attention == 'sliding': mask_text = f'causal sliding window W={spec.window}'
    qk = p.op('Q × Kᵀ', f'batched head GEMM; {mask_text}', x0 + 300, rope_y + 185, 'blue', 170, 55)
    sm_formula = 'p_i = exp(s_i−m)/Σj exp(s_j−m)'
    if attention_sink: sm_formula = 'P = softmax([QKᵀ/√d, learned sink_head]); discard sink output'
    sm = p.op('Softmax FP32' + (' + sink' if attention_sink else ''), sm_formula, x0 + 300, rope_y + 285, 'purple', 190, 62)
    pv = p.op('P × V', 'batched head GEMM', x0 + 535, rope_y + 390, 'blue', 150, 52)
    p.edge(qr, qk); p.edge(kg, qk, EDGE + 'entryX=0;entryY=0.5;'); p.edge(qk, sm); p.edge(sm, pv); p.edge(vg, pv)
    cur2 = pv
    if spec.q_gate:
        sg = p.op('Q-gate sigmoid', 'gq = σ(q_gate)', x0 + 55, rope_y + 390, 'purple', 150, 50)
        gm = p.op('Context gating', 'C ← C ⊙ gq', x0 + 300, rope_y + 480, 'purple', 165, 50)
        p.edge(q, sg, EDGE + 'exitX=0.15;exitY=1;entryX=0.5;entryY=0;', [(x0 + 275, y0 + 245), (x0 + 275, rope_y + 415), (x0 + 205, rope_y + 415)])
        p.edge(pv, gm, EDGE + 'entryX=0.75;entryY=0;'); p.edge(sg, gm, EDGE + 'entryX=0.25;entryY=0;'); cur2 = gm
        o_y = rope_y + 575
    else:
        o_y = rope_y + 490
    o = p.op('O Proj', 'C · Wo', x0 + 540, o_y, 'blue', 130, 48); p.edge(cur2, o)
    if post_norms:
        post = rmsnorm(p, x0 + 320, o_y + 75, 'Post-Attention RMSNorm', 220); p.edge(o, post); o = post
    add1 = p.plus(x0 + 380, o_y + 155); p.edge(o, add1); residual_edge(p, cur, add1, x0 + 5)
    r1 = p.op('X + Attention', None, x0 + 325, o_y + 205, 'output', 140, 40); p.edge(add1, r1)
    n2 = layernorm(p, x0 + 250, o_y + 275, 'LayerNorm 2', 260) if spec.norm == 'LayerNorm' else rmsnorm(p, x0 + 250, o_y + 275, 'RMSNorm 2', 260)
    p.edge(r1, n2)
    if moe:
        draw_moe_flow(p, spec, n2, r1, x0 + 10, o_y + 380)
    else:
        out = draw_mlp_flow(p, n2, r1, x0 + 230, o_y + 380, spec.mlp)
        if post_norms:
            # Gemma-style post-FFN norm is shown explicitly before the second residual.
            pass
    p.vertex(f'<b>Attention dimensions</b><br>Q={spec.nq}×{spec.D}; K/V={spec.nkv}×{spec.D}; logical score rows={spec.nq}×T×' + (str(spec.window) if spec.attention == 'sliding' else 'T'),
             x0 + 40, o_y + (1010 if moe else 840), 650, 55, NOTE_STYLE)


def expert_body_flow(p: Page, x: float, y: float, label: str, mlp: str = 'SwiGLU', w: float = 430, h: float = 265) -> tuple[str, str, str]:
    p.vertex(label, x, y, w, h, GROUP_STYLE)
    gate = p.op('gate_proj', 'X · Wg', x + 20, y + 42, 'blue', 105, 44, 9)
    up = p.op('up_proj', 'X · Wu', x + 155, y + 42, 'blue', 105, 44, 9)
    act_name = 'SiLU' if mlp == 'SwiGLU' else 'GELU-tanh'
    act = p.op(act_name, 'u·σ(u)' if mlp == 'SwiGLU' else 'GELU_tanh(u)', x + 20, y + 112, 'purple', 105, 44, 9)
    mul = p.op('Elementwise gate', f'{act_name}(gate) ⊙ up', x + 145, y + 112, 'purple', 130, 44, 9)
    down = p.op('down_proj', 'Z · Wd', x + 292, y + 112, 'blue', 105, 44, 9)
    p.edge(gate, act); p.edge(act, mul); p.edge(up, mul); p.edge(mul, down)
    return gate, up, down


def draw_moe_flow(p: Page, spec: ModelSpec, norm_src: str, residual_src: str, x: float, y: float, router_score: str = 'softmax') -> str:
    router = p.op('Router projection', 'logits = X · Wrouter', x + 10, y, 'blue', 150, 50)
    score_formula = 'p = softmax_FP32(logits)' if router_score == 'softmax' else ('p = sigmoid_FP32(logits)' if router_score == 'sigmoid' else 'p = √softplus(logits)')
    score = p.op('Router scoring', score_formula, x + 10, y + 78, 'purple', 150, 50)
    topk = p.op(f'Top-{spec.K} + renorm', 'select experts; p ← p/ΣTopK p', x + 10, y + 156, 'purple', 150, 54)
    dispatch = p.op('Dispatch / gather', 'group token rows by expert_id', x + 10, y + 238, 'purple', 150, 54)
    routed_gate, routed_up, routed_down = expert_body_flow(p, x + 190, y + 105, f'Routed expert body × E={spec.E}; {spec.K} active/token', spec.mlp, 445, 270)
    weight = p.op('Expert weighting', 'p_e ⊙ E_e(X)', x + 515, y + 410, 'purple', 135, 50)
    reduce = p.op('Scatter / weighted reduce', 'Yroute = Σe p_e E_e(X)', x + 405, y + 490, 'purple', 245, 55)
    p.edge(norm_src, router, EDGE + 'exitX=0.2;exitY=1;entryX=0.5;entryY=0;')
    p.edge(router, score); p.edge(score, topk); p.edge(topk, dispatch)
    p.edge(dispatch, routed_gate, EDGE + 'exitX=1;exitY=0.35;entryX=0.5;entryY=0;')
    p.edge(dispatch, routed_up, EDGE + 'exitX=1;exitY=0.7;entryX=0.5;entryY=0;')
    p.edge(routed_down, weight); p.edge(topk, weight, EDGE + 'exitX=1;exitY=0.7;entryX=0;entryY=0.3;', [(x + 175, y + 195), (x + 495, y + 430)]); p.edge(weight, reduce)
    merge_src = reduce
    if spec.shared_experts:
        shared_gate, shared_up, shared_down = expert_body_flow(p, x + 700, y + 20, f'Shared expert body × {spec.shared_experts}', spec.mlp, 420, 255)
        sg_lin = p.op('Shared gate projection', 's = X · ws', x + 710, y + 310, 'blue', 160, 48)
        sg = p.op('Sigmoid', 'σ(s)', x + 710, y + 382, 'purple', 160, 44)
        smul = p.op('Shared gating', 'σ(s) ⊙ Eshared(X)', x + 890, y + 382, 'purple', 190, 48)
        p.edge(norm_src, shared_gate, EDGE + 'exitX=0.72;exitY=1;entryX=0.5;entryY=0;', [(x + 760, y - 15), (x + 760, y + 62)])
        p.edge(norm_src, shared_up, EDGE + 'exitX=0.82;exitY=1;entryX=0.5;entryY=0;', [(x + 920, y - 15), (x + 920, y + 62)])
        p.edge(norm_src, sg_lin, EDGE + 'exitX=0.9;exitY=1;entryX=0.5;entryY=0;', [(x + 1130, y - 15), (x + 1130, y + 333), (x + 870, y + 333)])
        p.edge(sg_lin, sg); p.edge(sg, smul); p.edge(shared_down, smul)
        merge = p.plus(x + 745, y + 520); p.edge(reduce, merge); p.edge(smul, merge); merge_src = merge
    add2 = p.plus(x + 745, y + 595)
    out = p.op('Block output', None, x + 695, y + 645, 'output', 130, 40)
    p.edge(merge_src, add2); p.edge(add2, out); residual_edge(p, residual_src, add2, x - 15)
    return out


def draw_gdn_flow(p: Page, spec: ModelSpec, *, x0: float = 20, y0: float = 135, moe: bool = False) -> None:
    # gk/nv stored in nq/nkv here; D is dK=dV for representative Qwen3.5 blocks.
    gk, gv, d = spec.nq, spec.nkv, spec.D
    inp = p.op('X', f'[T={T}, H={spec.H}]', x0 + 355, y0, 'input', 100, 40)
    n1 = rmsnorm(p, x0 + 275, y0 + 75, 'RMSNorm 1', 260); p.edge(inp, n1)
    qkv = p.op('in_proj_qkv', 'X · Wqkv', x0 + 25, y0 + 180, 'blue', 135, 50)
    z = p.op('in_proj_z', 'X · Wz', x0 + 225, y0 + 180, 'blue', 120, 50)
    a = p.op('in_proj_a', 'X · Wa', x0 + 425, y0 + 180, 'blue', 120, 50)
    b = p.op('in_proj_b', 'X · Wb', x0 + 620, y0 + 180, 'blue', 120, 50)
    for i, o in enumerate([qkv, z, a, b]): p.edge(n1, o, EDGE + f'exitX={0.12+i*0.25:.2f};exitY=1;entryX=0.5;entryY=0;')
    conv = p.op('Depthwise Conv1D', 'causal, k=4; channelwise', x0 + 25, y0 + 270, 'purple', 140, 52)
    silu = p.op('SiLU', 'u·σ(u)', x0 + 25, y0 + 350, 'purple', 140, 48)
    split = p.op('Split Q / K / V', 'reshape mixed projection into three tensors', x0 + 245, y0 + 430, 'purple', 230, 55)
    p.edge(qkv, conv); p.edge(conv, silu); p.edge(silu, split)
    g = p.op('Decay preactivation', 'g = −exp(A_log)·softplus(a+dt_bias)', x0 + 410, y0 + 275, 'purple', 215, 58)
    alpha = p.op('Decay factor', 'α = exp(g)', x0 + 435, y0 + 365, 'purple', 165, 48)
    beta = p.op('Update gate', 'β = sigmoid(b)', x0 + 625, y0 + 365, 'purple', 155, 48)
    p.edge(a, g); p.edge(g, alpha); p.edge(b, beta)
    q = p.op('Q reshape', f'[{gk},T,{d}]', x0 + 25, y0 + 530, 'purple', 135, 44)
    k = p.op('K reshape', f'[{gk},T,{d}]', x0 + 245, y0 + 530, 'purple', 135, 44)
    v = p.op('V reshape', f'[{gv},T,{d}]', x0 + 465, y0 + 530, 'purple', 135, 44)
    p.edge(split, q, EDGE + 'exitX=0.2;exitY=1;entryX=0.5;entryY=0;'); p.edge(split, k); p.edge(split, v, EDGE + 'exitX=0.8;exitY=1;entryX=0.5;entryY=0;')
    qsrc, ksrc = q, k
    if gv != gk:
        qr = p.op(f'Q head repeat ×{gv//gk}', 'repeat_interleave to V-head count', x0 + 25, y0 + 605, 'purple', 155, 48)
        kr = p.op(f'K head repeat ×{gv//gk}', 'repeat_interleave to V-head count', x0 + 235, y0 + 605, 'purple', 155, 48)
        p.edge(q, qr); p.edge(k, kr); qsrc, ksrc = qr, kr; normy = y0 + 685
    else:
        normy = y0 + 610
    qn = qk_l2norm(p, x0 + 25, normy, 'Q L2Norm'); kn = qk_l2norm(p, x0 + 235, normy, 'K L2Norm')
    p.edge(qsrc, qn); p.edge(ksrc, kn)
    core_y = normy + 95
    p.vertex('Chunk Gated Delta Rule — expanded logical prefill dataflow', x0 + 15, core_y, 790, 665, GROUP_STYLE)
    p.vertex('<b>Token-equivalent recurrence</b><br>r_t = v_t − k_tᵀS_{t−1}<br>S_t = α_tS_{t−1}+β_t k_t r_tᵀ<br>o_t = q_tᵀS_t', x0 + 35, core_y + 42, 260, 90, NOTE_STYLE)
    chunk = p.op('Chunk partition', 'T=1024; representative C=64', x0 + 330, core_y + 48, 'purple', 160, 48)
    decay = p.op('Decay matrix Γ', 'Γij = exp(Σr=j+1..i g_r)', x0 + 535, core_y + 48, 'purple', 220, 52)
    p.edge(alpha, decay); p.edge(qn, chunk); p.edge(kn, chunk); p.edge(v, chunk)
    kk = p.op('K Kᵀ', 'batched head GEMM', x0 + 55, core_y + 180, 'blue', 155, 48)
    lower = p.op('Build strict-lower L', 'L = I + tril(β·Γ·KKᵀ, −1)', x0 + 260, core_y + 180, 'purple', 220, 55)
    solve = p.op('Triangular solve', 'U = L⁻¹(β ⊙ V)', x0 + 545, core_y + 180, 'purple', 190, 55)
    p.edge(chunk, kk); p.edge(kk, lower); p.edge(beta, lower); p.edge(decay, lower); p.edge(lower, solve)
    qk = p.op('Q Kᵀ', 'batched head GEMM', x0 + 55, core_y + 305, 'blue', 155, 48)
    intra = p.op('Intra-chunk output', 'Ointra=(Γ⊙QKᵀ)·U', x0 + 260, core_y + 305, 'blue', 220, 55)
    sread = p.op('State read', 'Ostate = Q · Sin', x0 + 545, core_y + 305, 'blue', 190, 55)
    p.edge(chunk, qk); p.edge(qk, intra); p.edge(decay, intra); p.edge(solve, intra); p.edge(qn, sread)
    combine = p.op('Output combine', 'O = Ostate + Ointra', x0 + 260, core_y + 425, 'purple', 220, 50)
    p.edge(intra, combine); p.edge(sread, combine)
    ku = p.op('Kᵀ U', 'state-delta GEMM', x0 + 55, core_y + 535, 'blue', 155, 48)
    sdecay = p.op('State decay', 'Sdecay = αend ⊙ Sin', x0 + 260, core_y + 535, 'purple', 220, 50)
    sadd = p.plus(x0 + 565, core_y + 545)
    state = p.state('Recurrent state S\n[heads,dK,dV] FP32', x0 + 665, core_y + 480, 125, 72)
    p.edge(chunk, ku); p.edge(solve, ku); p.edge(decay, sdecay); p.edge(ku, sadd); p.edge(sdecay, sadd); p.edge(sadd, state, EDGE_STATE); p.edge(state, sread, EDGE_STATE); p.edge(state, sdecay, EDGE_STATE)
    gy = core_y + 725
    gated = p.op('RMSNormGated', 'Y = RMSNorm(O) ⊙ SiLU(z)', x0 + 300, gy, 'purple', 235, 58); p.edge(combine, gated); p.edge(z, gated)
    outp = p.op('out_proj', 'Y · Wout', x0 + 585, gy + 5, 'blue', 135, 48); p.edge(gated, outp)
    add1 = p.plus(x0 + 400, gy + 110); p.edge(outp, add1); residual_edge(p, inp, add1, x0 + 5)
    r1 = p.op('X + GDN', None, x0 + 345, gy + 155, 'output', 140, 40); p.edge(add1, r1)
    n2 = rmsnorm(p, x0 + 275, gy + 230, 'RMSNorm 2', 260); p.edge(r1, n2)
    if moe: draw_moe_flow(p, spec, n2, r1, x0 + 10, gy + 335)
    else: draw_mlp_flow(p, n2, r1, x0 + 230, gy + 335, spec.mlp)


def draw_gemma_flow(p: Page, spec: ModelSpec, *, x0: float = 20, y0: float = 135) -> None:
    # Gemma 3/4 use pre- and post-sub-layer RMSNorms. Explicit K/V sharing is selectable in spec.note.
    k_eq_v = 'K=V' in spec.note
    inp = p.op('X', f'[T={T}, H={spec.H}]', x0 + 345, y0, 'input', 100, 40)
    pre = rmsnorm(p, x0 + 265, y0 + 78, 'Pre-Attention RMSNorm', 260); p.edge(inp, pre)
    q = p.op('Q Proj', 'X · Wq', x0 + 300, y0 + 175, 'blue', 120, 48)
    kv = p.op('K=V shared Proj' if k_eq_v else 'K Proj', 'X · Wkv' if k_eq_v else 'X · Wk', x0 + 25, y0 + 175, 'blue', 155 if k_eq_v else 120, 48)
    v = kv if k_eq_v else p.op('V Proj', 'X · Wv', x0 + 620, y0 + 175, 'blue', 120, 48)
    p.edge(pre, kv); p.edge(pre, q);
    if not k_eq_v: p.edge(pre, v)
    qn = qk_head_rmsnorm(p, x0 + 300, y0 + 255, 'Q Head RMSNorm')
    kn = qk_head_rmsnorm(p, x0 + 25, y0 + 255, 'K Head RMSNorm')
    p.edge(q, qn); p.edge(kv, kn)
    rname = 'Partial RoPE' if spec.partial_rope is not None else 'RoPE'
    rformula = f'rotate {spec.partial_rope:.2f}·d dims' if spec.partial_rope is not None else 'rotate all head dims'
    qr = p.op(rname, rformula, x0 + 300, y0 + 340, 'purple', 150, 52)
    kr = p.op(rname, rformula, x0 + 25, y0 + 340, 'purple', 150, 52)
    p.edge(qn, qr); p.edge(kn, kr)
    kc = p.state('K cache', x0 + 40, y0 + 430, 120, 48); vc = p.state('V cache', x0 + 620, y0 + 430, 120, 48)
    p.edge(kr, kc); p.edge(v, vc, EDGE_GREEN)
    group = max(1, spec.nq // spec.nkv)
    kg = p.op(f'K repeat ×{group}', 'GQA expansion', x0 + 25, y0 + 515, 'purple', 140, 46)
    vg = p.op(f'V repeat ×{group}', 'GQA expansion', x0 + 610, y0 + 515, 'purple', 140, 46)
    p.edge(kc, kg); p.edge(vc, vg)
    mask = f'sliding W={spec.window}' if spec.attention == 'sliding' else 'full causal'
    qk = p.op('Q × Kᵀ', f'batched GEMM; {mask}', x0 + 300, y0 + 520, 'blue', 170, 52)
    soft = p.op('Softmax FP32', 'p_i=exp(s_i−m)/Σexp(s_j−m)', x0 + 300, y0 + 615, 'purple', 170, 58)
    pv = p.op('P × V', 'batched head GEMM', x0 + 540, y0 + 710, 'blue', 150, 52)
    p.edge(qr,qk);p.edge(kg,qk);p.edge(qk,soft);p.edge(soft,pv);p.edge(vg,pv)
    o = p.op('O Proj', 'C · Wo', x0 + 540, y0 + 805, 'blue', 130, 48);p.edge(pv,o)
    post_attn = rmsnorm(p, x0 + 285, y0 + 885, 'Post-Attention RMSNorm', 240);p.edge(o,post_attn)
    add1=p.plus(x0+395,y0+975);p.edge(post_attn,add1);residual_edge(p,inp,add1,x0+5)
    r1=p.op('X + Attention',None,x0+335,y0+1025,'output',145,40);p.edge(add1,r1)
    pre_ff=rmsnorm(p,x0+270,y0+1100,'Pre-FFN RMSNorm',260);p.edge(r1,pre_ff)
    gate=p.op('gate_proj','X · Wgate',x0+185,y0+1200,'blue',125,48)
    up=p.op('up_proj','X · Wup',x0+420,y0+1200,'blue',125,48)
    gelu=p.op('GELU-tanh','0.5u[1+tanh(√(2/π)(u+0.044715u³))]',x0+175,y0+1280,'purple',150,56)
    mul=p.op('Elementwise gate','GELU(gate) ⊙ up',x0+285,y0+1370,'purple',165,50)
    down=p.op('down_proj','Z · Wdown',x0+305,y0+1455,'blue',130,48)
    post_ff=rmsnorm(p,x0+260,y0+1535,'Post-FFN RMSNorm',250)
    p.edge(pre_ff,gate);p.edge(pre_ff,up);p.edge(gate,gelu);p.edge(gelu,mul);p.edge(up,mul);p.edge(mul,down);p.edge(down,post_ff)
    add2=p.plus(x0+395,y0+1625);p.edge(post_ff,add2);residual_edge(p,r1,add2,x0+5)
    out=p.op('Block output',None,x0+340,y0+1675,'output',135,40);p.edge(add2,out)


def draw_gpt2_opt_flow(p: Page, spec: ModelSpec, *, opt: bool = False, x0: float = 20, y0: float = 135) -> None:
    inp = p.op('X', f'[T={T}, H={spec.H}]', x0 + 330, y0, 'input', 100, 40)
    pos = p.op('Learned absolute position', 'X ← token_embed + pos_embed', x0 + 250, y0 + 72, 'purple', 260, 54);p.edge(inp,pos)
    n1=layernorm(p,x0+270,y0+155,'LayerNorm 1',220);p.edge(pos,n1)
    if opt:
        q=p.op('Q Proj','X·Wq+bq',x0+45,y0+250,'blue',120,48);k=p.op('K Proj','X·Wk+bk',x0+315,y0+250,'blue',120,48);v=p.op('V Proj','X·Wv+bv',x0+585,y0+250,'blue',120,48)
        p.edge(n1,q);p.edge(n1,k);p.edge(n1,v)
    else:
        qkv=p.op('Combined QKV Proj','X · Wqkv + bqkv',x0+270,y0+250,'blue',220,50);p.edge(n1,qkv)
        split=p.op('Split heads','reshape Q/K/V',x0+285,y0+330,'purple',190,48);p.edge(qkv,split);q=k=v=split
    qk=p.op('Q × Kᵀ','MHA score GEMM + causal mask',x0+285,y0+430,'blue',190,54)
    sm=p.op('Softmax FP32','p_i=exp(s_i−m)/Σexp(s_j−m)',x0+300,y0+525,'purple',165,58)
    pv=p.op('P × V','batched head GEMM',x0+535,y0+620,'blue',150,52)
    p.edge(q,qk);p.edge(k,qk);p.edge(qk,sm);p.edge(sm,pv);p.edge(v,pv)
    o=p.op('Output Proj','C·Wo+bo',x0+535,y0+710,'blue',140,48);p.edge(pv,o)
    add1=p.plus(x0+385,y0+795);p.edge(o,add1);residual_edge(p,pos,add1,x0+5)
    r1=p.op('X + Attention',None,x0+330,y0+840,'output',140,40);p.edge(add1,r1)
    n2=layernorm(p,x0+270,y0+915,'LayerNorm 2',220);p.edge(r1,n2)
    draw_mlp_flow(p,n2,r1,x0+250,y0+1010,'ReLU' if opt else 'GELU')


def draw_glm_dsa_flow(p: Page, spec: ModelSpec, *, x0: float = 20, y0: float = 135) -> None:
    inp=p.op('X',f'[T={T},H={spec.H}]',x0+370,y0,'input',110,40)
    n1=rmsnorm(p,x0+285,y0+75,'RMSNorm 1',280);p.edge(inp,n1)
    qa=p.op('Q down-proj','X · Wq_a → rank 2048',x0+40,y0+180,'blue',175,52)
    qan=rmsnorm(p,x0+35,y0+260,'Q low-rank RMSNorm',190);qb=p.op('Q up-proj','rank → 64×(192+64)',x0+35,y0+345,'blue',200,52)
    kva=p.op('KV compression','X·Wkv_a → latent512 + K_rope64',x0+330,y0+180,'blue',220,52)
    kvn=rmsnorm(p,x0+345,y0+260,'KV latent RMSNorm',190);kvb=p.op('KV up-proj','latent → K_nope + V per head',x0+335,y0+345,'blue',210,52)
    p.edge(n1,qa);p.edge(qa,qan);p.edge(qan,qb);p.edge(n1,kva);p.edge(kva,kvn);p.edge(kvn,kvb)
    qsplit=p.op('Split Q','Q_nope[192] + Q_rope[64]',x0+35,y0+435,'purple',200,50)
    kvsplit=p.op('Split KV','K_nope[192], K_rope[64], V[256]',x0+335,y0+435,'purple',220,50)
    rope=p.op('RoPE','apply only 64 rotary dims',x0+205,y0+520,'purple',180,50)
    p.edge(qb,qsplit);p.edge(kvb,kvsplit);p.edge(qsplit,rope);p.edge(kvsplit,rope)
    # DSA indexer expanded.
    p.vertex('DeepSeek Sparse Attention indexer',x0+20,y0+610,740,330,GROUP_STYLE)
    iq=p.op('Indexer Q projection','32 heads × 128',x0+45,y0+660,'blue',165,48)
    ik=p.op('Indexer K projection','32 heads × 128',x0+260,y0+660,'blue',165,48)
    iscore=p.op('Indexer Q × Kᵀ','relevance score GEMM',x0+475,y0+660,'blue',165,48)
    itop=p.op('Top-2048 select','causal candidate indices',x0+475,y0+745,'purple',165,50)
    gather=p.op('Sparse gather','collect selected compressed KV',x0+260,y0+830,'purple',180,50)
    p.edge(n1,iq);p.edge(n1,ik);p.edge(iq,iscore);p.edge(ik,iscore);p.edge(iscore,itop);p.edge(itop,gather)
    attn=p.op('Selected Q × Kᵀ','64-head sparse GEMM',x0+45,y0+830,'blue',170,50);soft=p.op('Softmax FP32','over selected 2048 keys',x0+45,y0+915,'purple',170,52);pv=p.op('P × V','sparse value GEMM',x0+260,y0+1005,'blue',170,50)
    p.edge(rope,attn);p.edge(gather,attn);p.edge(attn,soft);p.edge(soft,pv);p.edge(gather,pv)
    o=p.op('O Proj','[64×256] → H',x0+500,y0+1005,'blue',150,48);p.edge(pv,o)
    add1=p.plus(x0+405,y0+1095);p.edge(o,add1);residual_edge(p,inp,add1,x0+5)
    r1=p.op('X + DSA/MLA',None,x0+345,y0+1140,'output',150,40);p.edge(add1,r1)
    n2=rmsnorm(p,x0+285,y0+1215,'RMSNorm 2',280);p.edge(r1,n2)
    draw_moe_flow(p,spec,n2,r1,x0+10,y0+1320,router_score='sigmoid')
    p.vertex('<b>Layer variation</b><br>Layers 0–2 use dense SwiGLU I=12288. Later layers use 256 routed experts, top-8, plus one shared expert.',x0+30,y0+2070,720,60,NOTE_STYLE)


def draw_deepseek_v3_flow(p: Page, spec: ModelSpec, *, x0: float=20,y0:float=135) -> None:
    inp=p.op('X',f'[T={T},H={spec.H}]',x0+370,y0,'input',110,40);n1=rmsnorm(p,x0+285,y0+75,'RMSNorm 1',280);p.edge(inp,n1)
    qa=p.op('Q low-rank A','H → rank1536',x0+35,y0+180,'blue',160,48);qan=rmsnorm(p,x0+25,y0+255,'Q LoRA RMSNorm',180);qb=p.op('Q low-rank B','rank → 128×(128+64)',x0+20,y0+335,'blue',200,50)
    kva=p.op('KV compression','H → latent512 + K_rope64',x0+335,y0+180,'blue',210,50);kvn=rmsnorm(p,x0+350,y0+255,'KV latent RMSNorm',180);kvb=p.op('KV expansion','latent → K_nope + V128/head',x0+330,y0+335,'blue',220,50)
    p.edge(n1,qa);p.edge(qa,qan);p.edge(qan,qb);p.edge(n1,kva);p.edge(kva,kvn);p.edge(kvn,kvb)
    splitq=p.op('Split Q','Q_nope128 + Q_rope64',x0+25,y0+425,'purple',190,48);splitkv=p.op('Split KV','K_nope128 + K_rope64 + V128',x0+335,y0+425,'purple',220,48);rope=p.op('YaRN RoPE','apply only 64 rotary dims',x0+205,y0+505,'purple',180,50)
    p.edge(qb,splitq);p.edge(kvb,splitkv);p.edge(splitq,rope);p.edge(splitkv,rope)
    qk=p.op('MLA Q × Kᵀ','128 heads; latent KV reconstruction/fusion',x0+205,y0+600,'blue',230,55);sm=p.op('Softmax FP32','full causal attention',x0+235,y0+695,'purple',170,52);pv=p.op('P × V','latent/value GEMM',x0+235,y0+785,'blue',170,50);o=p.op('O Proj','[128×128] → H',x0+480,y0+785,'blue',150,48)
    p.edge(rope,qk);p.edge(qk,sm);p.edge(sm,pv);p.edge(pv,o)
    add1=p.plus(x0+405,y0+875);p.edge(o,add1);residual_edge(p,inp,add1,x0+5);r1=p.op('X + MLA',None,x0+350,y0+920,'output',140,40);p.edge(add1,r1);n2=rmsnorm(p,x0+285,y0+995,'RMSNorm 2',280);p.edge(r1,n2)
    draw_moe_flow(p,spec,n2,r1,x0+10,y0+1100,router_score='sigmoid')
    p.vertex('<b>Layer variation</b><br>First 3 layers use dense SwiGLU I=18432; later layers use 256 routed experts top-8 + one shared expert.',x0+30,y0+1850,720,58,NOTE_STYLE)


def draw_deepseek_v4_flow(p: Page, spec: ModelSpec, mode: str, *, x0: float=20,y0:float=135) -> None:
    inp=p.op('4 residual streams X₁…X₄',f'each [T={T},H={spec.H}]',x0+300,y0,'input',200,46)
    sink=p.op('mHC Sinkhorn matrix','M = Sinkhorn(learned logits), 20 iterations',x0+245,y0+80,'purple',310,58)
    mix=p.op('mHC input mixing','Xin = Σj Mij Xj',x0+300,y0+170,'purple',200,50);p.edge(inp,sink);p.edge(sink,mix)
    n1=rmsnorm(p,x0+285,y0+250,'RMSNorm 1',230);p.edge(mix,n1)
    qa=p.op('Q LoRA A','H → rank1024',x0+25,y0+350,'blue',150,48);qan=rmsnorm(p,x0+20,y0+425,'Q LoRA RMSNorm',165);qb=p.op('Q LoRA B','rank → 64×512',x0+20,y0+505,'blue',170,48)
    kv=p.op('Shared K=V projection','H → one 512-d head',x0+300,y0+350,'blue',200,50);split=p.op('Partial RoPE split','448 content + 64 rotary',x0+310,y0+430,'purple',180,50);rope=p.op('YaRN RoPE','rotate 64 dims',x0+325,y0+510,'purple',150,48)
    p.edge(n1,qa);p.edge(qa,qan);p.edge(qan,qb);p.edge(n1,kv);p.edge(kv,split);p.edge(split,rope)
    p.vertex(f'{mode} attention branch + supplementary local window',x0+15,y0+590,790,450,GROUP_STYLE)
    localqk=p.op('Sliding Q × Kᵀ','window W=128',x0+35,y0+650,'blue',155,48);localsm=p.op('Local Softmax','FP32 over W=128',x0+35,y0+730,'purple',155,48);localpv=p.op('Local P × V','batched GEMM',x0+35,y0+810,'blue',155,48)
    p.edge(qb,localqk);p.edge(rope,localqk);p.edge(localqk,localsm);p.edge(localsm,localpv);p.edge(kv,localpv)
    if mode == 'Sliding-only':
        longout = localpv
    elif mode == 'CSA':
        comp=p.op('Block KV compressor','C = Pool₄(KV) · Wc; causal summaries',x0+265,y0+650,'blue',210,52)
        iq=p.op('Lightning indexer','score = (X·Wq) · (C·Wk)ᵀ; 64×128',x0+515,y0+650,'blue',190,52)
        top=p.op('Top-512 blocks','select compressed candidates',x0+520,y0+735,'purple',180,50)
        sqk=p.op('Sparse Q × Kᵀ','selected compressed KV',x0+285,y0+815,'blue',190,50)
        ssm=p.op('Sparse Softmax','FP32 over selected keys',x0+520,y0+815,'purple',180,50)
        spv=p.op('Sparse P × V','selected value GEMM',x0+405,y0+900,'blue',180,48)
        p.edge(kv,comp);p.edge(qb,iq);p.edge(comp,iq);p.edge(iq,top);p.edge(top,sqk);p.edge(comp,sqk);p.edge(sqk,ssm);p.edge(ssm,spv);p.edge(comp,spv);longout=spv
    else:
        comp1=p.op('Hierarchical compressor L1','C1 = Pool₄(KV) · Wc1',x0+255,y0+650,'blue',190,50)
        comp2=p.op('Hierarchical compressor L2','C2 = Pool₃₂(C1) · Wc2; total ratio 128',x0+505,y0+650,'blue',200,50)
        hqk=p.op('Q × compressed Kᵀ','dense over heavily-compressed memory',x0+300,y0+750,'blue',230,52)
        hsm=p.op('Compressed Softmax','FP32',x0+545,y0+750,'purple',150,50)
        hpv=p.op('P × compressed V','compressed value GEMM',x0+410,y0+845,'blue',190,48)
        p.edge(kv,comp1);p.edge(comp1,comp2);p.edge(qb,hqk);p.edge(comp2,hqk);p.edge(hqk,hsm);p.edge(hsm,hpv);p.edge(comp2,hpv);longout=hpv
    if longout != localpv:
        merge=p.plus(x0+315,y0+970);p.edge(localpv,merge);p.edge(longout,merge);attnout=merge
    else: attnout=localpv
    sinknode=p.op('Attention sink','learned head logit in denominator',x0+590,y0+930,'purple',180,50);p.edge(n1,sinknode)
    p.edge(sinknode, localsm, EDGE + 'dashed=1;opacity=65;')
    if mode == 'CSA': p.edge(sinknode, ssm, EDGE + 'dashed=1;opacity=65;')
    elif mode == 'HCA': p.edge(sinknode, hsm, EDGE + 'dashed=1;opacity=65;')
    oA=p.op('Grouped O low-rank A','64×512 → rank1024; 8 groups',x0+250,y0+1080,'blue',250,52);oB=p.op('O low-rank B','rank1024 → H',x0+545,y0+1080,'blue',170,50);p.edge(attnout,oA);p.edge(oA,oB)
    mixout=p.op('mHC output mixing','redistribute branch output to 4 streams',x0+300,y0+1175,'purple',230,52);p.edge(oB,mixout)
    add1=p.plus(x0+405,y0+1265);p.edge(mixout,add1);residual_edge(p,inp,add1,x0+5);r1=p.op(f'4 streams + {mode}',None,x0+335,y0+1310,'output',170,40);p.edge(add1,r1)
    n2=rmsnorm(p,x0+285,y0+1385,'RMSNorm 2',250);p.edge(r1,n2)
    draw_moe_flow(p,spec,n2,r1,x0+10,y0+1490,router_score='sqrtsoftplus')
    p.vertex('<b>MoE variation</b><br>First 3 layers use hash routing; later layers use learned no-aux top-6 routing. Experts use clamped SwiGLU (limit=10).',x0+35,y0+2240,735,58,NOTE_STYLE)


# -------------------------- footprint helpers --------------------------


def weight_matrix(p: Page, name: str, x: float, y: float, out_dim: int, in_dim: int, dtype: str | None = None,
                  note: str = '', label: bool = True) -> tuple[str,float,float]:
    dt = dtype or (p.spec.weight_dtype if p.spec else 'BF16')
    return p.volume(name, x, y, out_dim, in_dim, dt, 'weight', category='weight', note=note, label=label)


def activation(p: Page, name: str, x: float, y: float, channels: int, tokens: int = T, dtype: str | None = None,
               kind: str = 'act', note: str = '') -> tuple[str,float,float]:
    dt = dtype or (p.spec.act_dtype if p.spec else 'BF16')
    return p.volume(name, x, y, channels, tokens, dt, kind, category='activation', note=note)


def vector_weight(p: Page, name: str, x: float, y: float, n: int, dtype: str = 'BF16') -> tuple[str,float,float]:
    return p.volume(name, x, y, n, 1, dtype, 'weight', category='weight', min_px=2.0)


def matrix_row(p: Page, mats: Sequence[tuple[str,int,int,str]], x: float, y: float, gap: float = 35) -> tuple[float,float]:
    cx=x; mh=0
    for name,od,idim,dt in mats:
        _,w,h=weight_matrix(p,name,cx,y,od,idim,dt);cx+=w+gap;mh=max(mh,h)
    return cx-x,mh


def score_grid(p: Page, name: str, x: float, y: float, heads: int, width_tokens: int, kind: str, cols: int = 8) -> tuple[list[str],float,float]:
    ids=[]
    ew,eh=exact_wh(width_tokens,T,'BF16');w=max(4,ew);h=max(4,eh);gap=5
    rows=math.ceil(heads/cols)
    for i in range(heads):
        c=i%cols;r=i//cols
        label=(f'<b>{esc(name)}</b><br>head {i}<br>{width_tokens}×{T} BF16<br>{fmt_bytes(nbytes(width_tokens,T,"BF16"))}' if i==0 else '')
        cid=p.raw_volume(label,x+c*(w+gap),y+r*(h+gap),w,h,kind,activation_bytes=nbytes(width_tokens,T,'BF16'))
        ids.append(cid)
    p.text(f'{name}: {heads} head matrices',x,y-24,max(180,cols*(w+gap)),20,TEXT_LEFT)
    return ids,cols*(w+gap)-gap,rows*(h+gap)-gap


def dense_weight_footprint(p: Page, x: float, y: float, H: int, I: int, mlp: str, dtype: str | None = None) -> tuple[float,float]:
    if mlp in ('SwiGLU','GeGLU'):
        _,gw,gh=weight_matrix(p,'gate_proj',x,y,I,H,dtype)
        _,uw,uh=weight_matrix(p,'up_proj',x,y+gh+25,I,H,dtype)
        dx=x+max(gw,uw)+35
        _,dw,dh=weight_matrix(p,'down_proj',dx,y,H,I,dtype)
        return max(gw,uw)+35+dw,max(gh+25+uh,dh)
    _,w1,h1=weight_matrix(p,'fc1',x,y,I,H,dtype)
    _,w2,h2=weight_matrix(p,'fc2',x+w1+35,y,H,I,dtype)
    return w1+35+w2,max(h1,h2)


def expert_tile_geometry(H:int,I:int,dtype:str) -> tuple[float,float,float,float,float,float]:
    gw,gh=exact_wh(I,H,dtype);dw,dh=exact_wh(H,I,dtype)
    gw=max(2,gw);gh=max(2,gh);dw=max(2,dw);dh=max(2,dh)
    tilew=max(gw*2+5,dw);tileh=gh+5+dh
    return gw,gh,dw,dh,tilew,tileh


def expert_grid(p: Page, x: float, y: float, E: int, H: int, I: int, dtype: str, cols: int | None = None, title: str='Routed experts') -> tuple[float,float]:
    if cols is None: cols=16 if E>=128 else 8
    rows=math.ceil(E/cols);gw,gh,dw,dh,tw,th=expert_tile_geometry(H,I,dtype);gap=8
    p.text(f'<b>{esc(title)}</b>: E={E}, each expert = gate/up/down; rectangles preserve each matrix aspect ratio',x,y-28,max(700,cols*(tw+gap)),24,TEXT_LEFT)
    for i in range(E):
        c=i%cols;r=i//cols;tx=x+c*(tw+gap);ty=y+r*(th+gap)
        label=i<2
        p.volume(f'E{i} gate' if label else '',tx,ty,I,H,dtype,'weight',category='weight',label=label)
        p.volume(f'E{i} up' if label else '',tx+gw+5,ty,I,H,dtype,'weight',category='weight',label=label)
        p.volume(f'E{i} down' if label else '',tx,ty+gh+5,H,I,dtype,'weight',category='weight',label=label)
    return cols*(tw+gap)-gap,rows*(th+gap)-gap


def standard_footprint(p: Page, spec: ModelSpec, *, x: float=900,y:float=135, moe:bool=False,k_eq_v:bool=False,
                       post_norms:bool=False,attention_sink:bool=False) -> float:
    p.text('<b>Weight footprint</b>',x,y-30,300,24,TEXT_LEFT)
    qdim=spec.nq*spec.D;kvdim=spec.nkv*spec.D
    mats=[('q_proj',qdim*(2 if spec.q_gate else 1),spec.H,spec.weight_dtype),('k=v_proj' if k_eq_v else 'k_proj',kvdim,spec.H,spec.weight_dtype)]
    if not k_eq_v:mats.append(('v_proj',kvdim,spec.H,spec.weight_dtype))
    mats.append(('o_proj',spec.H,qdim,spec.weight_dtype))
    attw,atth=matrix_row(p,mats,x,y,35)
    vy=y+atth+25
    vx=x
    norm_count=4 if post_norms else 2
    for ni in range(norm_count):
        _,vwgt,_=vector_weight(p,f'norm γ{ni+1}',vx,vy,spec.H)
        vx += vwgt + 18
    if spec.qk_norm:
        _,vwgt,_=vector_weight(p,'Q norm γ',vx,vy,spec.D); vx += vwgt + 18
        _,vwgt,_=vector_weight(p,'K norm γ',vx,vy,spec.D); vx += vwgt + 18
    if attention_sink:
        _,vwgt,_=vector_weight(p,'attention sink',vx,vy,spec.nq); vx += vwgt + 18
    mlpx=max(x+attw+70, vx+45)
    max_weight_bottom=y+atth+80
    if moe:
        _,rw,rh=weight_matrix(p,'router',mlpx,y,spec.E,spec.H)
        exy=y+rh+55
        egw,egh=expert_grid(p,mlpx,exy,spec.E,spec.H,spec.expert_I,spec.expert_weight_dtype or spec.weight_dtype)
        max_weight_bottom=max(max_weight_bottom,exy+egh)
        if spec.shared_experts:
            sy=exy+egh+55
            shared_right=mlpx
            shared_h=0.0
            for si in range(spec.shared_experts):
                sw,sh=dense_weight_footprint(p,shared_right,sy,spec.H,spec.expert_I,spec.mlp,spec.expert_weight_dtype or spec.weight_dtype)
                shared_right += sw + 40
                shared_h=max(shared_h,sh)
            _,sgw,sgh=weight_matrix(p,'shared scalar gate',shared_right,sy,spec.shared_experts,spec.H,spec.weight_dtype)
            max_weight_bottom=max(max_weight_bottom,sy+max(shared_h,sgh))
    else:
        _,mlph=dense_weight_footprint(p,mlpx,y,spec.H,spec.I,spec.mlp);max_weight_bottom=max(max_weight_bottom,y+mlph)
    acty=max_weight_bottom+80
    p.text('<b>Activation + cache footprint</b>',x,acty-32,380,24,TEXT_LEFT)
    xid,xw,xh=activation(p,'X prefill',x,acty,spec.H,kind='input')
    nid,nw,nh=activation(p,'Norm1 output',x+xw+20,acty,spec.H,kind='norm')
    qid,qw,qh=activation(p,'Q',x+xw+nw+40,acty,qdim,note=f'{spec.nq}×{spec.D}')
    cx=x+xw+nw+qw+60
    kid,kw,kh=activation(p,'K',cx,acty,kvdim,kind='state',note=f'{spec.nkv}×{spec.D}')
    vid,vw,vh=activation(p,'V',cx+kw+20,acty,kvdim,kind='state')
    cache,cvw,cvh=activation(p,'K/V cache write',cx+kw+vw+40,acty,2*kvdim,kind='state')
    scorey=acty+max(xh,nh,qh,kh,vh,cvh)+50
    score_width=spec.window if spec.attention=='sliding' and spec.window else T
    sids,sw,sh=score_grid(p,'S = QKᵀ',x,scorey,spec.nq,score_width,'act')
    pids,pw,ph=score_grid(p,'P = softmax(S)',x+sw+50,scorey,spec.nq,score_width,'norm')
    cy=scorey+max(sh,ph)+50
    cid,cw,ch=activation(p,'Context P·V',x,cy,qdim)
    oa,oaw,oah=activation(p,'Attention/O output',x+cw+25,cy,spec.H)
    r1,rw1,rh1=activation(p,'Residual #1',x+cw+oaw+50,cy,spec.H,kind='residual')
    n2,n2w,n2h=activation(p,'Norm2 output',x+cw+oaw+rw1+75,cy,spec.H,kind='norm')
    tail_y=cy+max(ch,oah,rh1,n2h)+55
    if moe:
        lg,lw,lh=activation(p,'Router logits/prob',x,tail_y,spec.E,dtype='FP32',kind='norm')
        disp,dw,dh=activation(p,'Dispatched rows',x+lw+25,tail_y,spec.H,T*spec.K,kind='norm',note=f'T×top-{spec.K}')
        gate,gw,gh=activation(p,'Expert gate',x+lw+dw+50,tail_y,spec.expert_I,T*spec.K)
        up,uw,uh=activation(p,'Expert up',x+lw+dw+gw+75,tail_y,spec.expert_I,T*spec.K)
        prod,pdw,pdh=activation(p,'Expert product',x+lw+dw+gw+uw+100,tail_y,spec.expert_I,T*spec.K,kind='norm')
        outy=tail_y+max(lh,dh,gh,uh,pdh)+45
        activation(p,'Weighted routed output',x,outy,spec.H,kind='norm')
        activation(p,'Residual #2 / block output',x+150,outy,spec.H,kind='residual')
        return outy+350
    if spec.mlp in ('SwiGLU','GeGLU'):
        g,gw,gh=activation(p,'MLP gate',x,tail_y,spec.I)
        u,uw,uh=activation(p,'MLP up',x+gw+25,tail_y,spec.I)
        prod,pdw,pdh=activation(p,'Activated product',x+gw+uw+50,tail_y,spec.I,kind='norm')
        oy=tail_y+max(gh,uh,pdh)+40
    else:
        fc,fw,fh=activation(p,'FFN hidden',x,tail_y,spec.I,kind='norm');oy=tail_y+fh+40
    activation(p,'FFN/down output',x,oy,spec.H);activation(p,'Residual #2 / block output',x+150,oy,spec.H,kind='residual')
    return oy+350


def gdn_footprint(p: Page,spec:ModelSpec,*,x:float=900,y:float=135,moe:bool=False)->float:
    gk,gv,d=spec.nq,spec.nkv,spec.D;key=gk*d;val=gv*d;conv=2*key+val
    p.text('<b>Weight footprint</b>',x,y-30,300,24,TEXT_LEFT)
    mats=[('in_proj_qkv',conv,spec.H,spec.weight_dtype),('in_proj_z',val,spec.H,spec.weight_dtype),('out_proj',spec.H,val,spec.weight_dtype),('in_proj_a',gv,spec.H,spec.weight_dtype),('in_proj_b',gv,spec.H,spec.weight_dtype)]
    aw,ah=matrix_row(p,mats,x,y,32)
    vy=y+ah+25
    vx=x
    for vname,vn,vdt in [('DWConv k=4',conv*4,'BF16'),('A_log',gv,'FP32'),('dt_bias',gv,'FP32'),('norm vectors',spec.H*3,'BF16')]:
        _,vwgt,_=vector_weight(p,vname,vx,vy,vn,vdt)
        vx += vwgt + 18
    mx=max(x+aw+65,vx+45);bottom=y+ah+80
    if moe:
        _,rh=weight_matrix(p,'router',mx,y,spec.E,spec.H)[1:]
        exy=y+rh+50;egw,egh=expert_grid(p,mx,exy,spec.E,spec.H,spec.expert_I,spec.expert_weight_dtype or spec.weight_dtype);bottom=max(bottom,exy+egh)
        if spec.shared_experts:
            sy=exy+egh+45
            sw,sh=dense_weight_footprint(p,mx,sy,spec.H,spec.expert_I,spec.mlp,spec.expert_weight_dtype or spec.weight_dtype)
            _,sgw,sgh=weight_matrix(p,'shared scalar gate',mx+sw+40,sy,spec.shared_experts,spec.H,spec.weight_dtype)
            bottom=max(bottom,sy+max(sh,sgh))
    else:
        _,mh=dense_weight_footprint(p,mx,y,spec.H,spec.I,spec.mlp);bottom=max(bottom,y+mh)
    ay=bottom+75;p.text('<b>Activation + persistent state footprint</b>',x,ay-32,420,24,TEXT_LEFT)
    _,xw,xh=activation(p,'X prefill',x,ay,spec.H,kind='input');_,nw,nh=activation(p,'Norm1 output',x+xw+20,ay,spec.H,kind='norm');_,mw,mh=activation(p,'mixed_qkv',x+xw+nw+40,ay,conv)
    y2=ay+max(xh,nh,mh)+40
    _,dw,dh=activation(p,'DWConv+SiLU',x,y2,conv,kind='norm');_,zw,zh=activation(p,'z projection',x+dw+25,y2,val,kind='act');activation(p,'a/b gates',x+dw+zw+50,y2,2*gv,dtype='FP32',kind='norm')
    y3=y2+max(dh,zh)+45
    _,qw,qh=activation(p,'Q core FP32',x,y3,gv*d,dtype='FP32');_,kw,kh=activation(p,'K core FP32',x+qw+20,y3,gv*d,dtype='FP32');_,vw,vh=activation(p,'V core FP32',x+qw+kw+40,y3,gv*d,dtype='FP32')
    y4=y3+max(qh,kh,vh)+45
    _,sw,sh=p.volume('Recurrent state S',x,y4,gv*d,d,'FP32','state',category='activation',note=f'[{gv},{d},{d}]')
    _,ow,oh=activation(p,'GDN core output',x+sw+30,y4,val);activation(p,'Gated norm output',x+sw+ow+55,y4,val,kind='norm')
    y5=y4+max(sh,oh)+45;activation(p,'GDN out/residual',x,y5,spec.H);activation(p,'Norm2 output',x+150,y5,spec.H,kind='norm')
    if moe:
        ly=y5+170;activation(p,'Router logits/prob',x,ly,spec.E,dtype='FP32',kind='norm');activation(p,'Dispatched rows',x+150,ly,spec.H,T*spec.K,kind='norm');activation(p,'Expert intermediate',x+350,ly,spec.expert_I,T*spec.K);return ly+500
    ly=y5+170;activation(p,'MLP gate/up/product',x,ly,3*spec.I);activation(p,'Block output',x+250,ly,spec.H,kind='residual');return ly+400



def gpt2_opt_footprint(p: Page, spec: ModelSpec, *, opt: bool, x: float = 900, y: float = 135) -> float:
    p.text('<b>Weight footprint</b>', x, y-30, 300, 24, TEXT_LEFT)
    if opt:
        mats=[('q_proj',spec.H,spec.H,'BF16'),('k_proj',spec.H,spec.H,'BF16'),('v_proj',spec.H,spec.H,'BF16'),('o_proj',spec.H,spec.H,'BF16')]
    else:
        mats=[('combined_qkv',3*spec.H,spec.H,'BF16'),('o_proj',spec.H,spec.H,'BF16')]
    attw,atth=matrix_row(p,mats,x,y,28)
    ffx=x+attw+55
    ffw,ffh=dense_weight_footprint(p,ffx,y,spec.H,spec.I,spec.mlp,'BF16')
    vy=y+max(atth,ffh)+25
    vx=x
    for name,n in [('LN1 γ',spec.H),('LN1 β',spec.H),('LN2 γ',spec.H),('LN2 β',spec.H),('attention biases',4*spec.H),('FFN biases',spec.I+spec.H)]:
        _,vw,_=vector_weight(p,name,vx,vy,n,'BF16'); vx += vw+18
    bottom=vy+35
    ay=bottom+70
    p.text('<b>Activation footprint</b>',x,ay-30,320,24,TEXT_LEFT)
    _,xw,xh=activation(p,'X + learned position',x,ay,spec.H,kind='input')
    _,nw,nh=activation(p,'LayerNorm1 output',x+xw+20,ay,spec.H,kind='norm')
    qkv_ch=3*spec.H
    _,qw,qh=activation(p,'Combined QKV' if not opt else 'Q/K/V projections',x+xw+nw+40,ay,qkv_ch)
    sy=ay+max(xh,nh,qh)+45
    _,sw,sh=score_grid(p,'S = QKᵀ',x,sy,spec.nq,T,'act',cols=6)
    _,pw,ph=score_grid(p,'P = softmax(S)',x+sw+45,sy,spec.nq,T,'norm',cols=6)
    cy=sy+max(sh,ph)+45
    _,cw,ch=activation(p,'Context',x,cy,spec.H)
    _,ow,oh=activation(p,'Attention output + residual',x+cw+25,cy,spec.H,kind='residual')
    _,lw,lh=activation(p,'LayerNorm2 output',x+cw+ow+50,cy,spec.H,kind='norm')
    fy=cy+max(ch,oh,lh)+45
    _,fw,fh=activation(p,'FFN hidden',x,fy,spec.I,kind='norm')
    activation(p,'FFN output / block output',x+fw+25,fy,spec.H,kind='residual')
    return fy+fh+250


def gemma_footprint(p:Page,spec:ModelSpec,*,x:float=900,y:float=135,k_eq_v:bool=False)->float:
    return standard_footprint(p,spec,x=x,y=y,moe=False,k_eq_v=k_eq_v,post_norms=True)


def glm_footprint(p:Page,spec:ModelSpec,*,x:float=900,y:float=135)->float:
    p.text('<b>Weight footprint</b>',x,y-30,300,24,TEXT_LEFT)
    nq=64;qk=256;v=256;ql=2048;kvl=512;rope=64
    mats=[('q_a',ql,spec.H,'BF16'),('q_b',nq*qk,ql,'BF16'),('kv_a',kvl+rope,spec.H,'BF16'),('kv_b',nq*(192+v),kvl,'BF16'),('o_proj',spec.H,nq*v,'BF16'),('index Q/K proj',32*128,spec.H,'BF16')]
    aw,ah=matrix_row(p,mats,x,y,30);mx=x+aw+60
    weight_matrix(p,'router',mx,y,spec.E,spec.H);exy=y+160;egw,egh=expert_grid(p,mx,exy,spec.E,spec.H,spec.expert_I,spec.expert_weight_dtype or spec.weight_dtype);sy=exy+egh+45;sw,sh=dense_weight_footprint(p,mx,sy,spec.H,spec.expert_I,'SwiGLU',spec.expert_weight_dtype or spec.weight_dtype);weight_matrix(p,'shared scalar gate',mx+sw+40,sy,spec.shared_experts,spec.H,spec.weight_dtype);bottom=sy+max(sh,80)
    ay=bottom+70;p.text('<b>Activation + cache footprint</b>',x,ay-30,350,24,TEXT_LEFT)
    activation(p,'X prefill',x,ay,spec.H,kind='input');activation(p,'Q low-rank',x+170,ay,ql);activation(p,'KV latent cache',x+330,ay,kvl+rope,kind='state')
    y2=ay+170;activation(p,'Indexer scores',x,y2,32*T,dtype='BF16',note='logical 32×T×T');activation(p,'Selected indices',x+350,y2,2048,T,dtype='FP32',kind='norm');activation(p,'Sparse attention output',x+600,y2,nq*v)
    y3=y2+260;activation(p,'Router logits',x,y3,spec.E,dtype='FP32',kind='act');activation(p,'Dispatched rows',x+150,y3,spec.H,T*spec.K,kind='norm');activation(p,'Expert intermediate',x+400,y3,spec.expert_I,T*spec.K);return y3+500


def deepseek_v3_footprint(p:Page,spec:ModelSpec,*,x:float=900,y:float=135)->float:
    p.text('<b>Weight footprint</b>',x,y-30,300,24,TEXT_LEFT)
    nq=128;nope=128;rope=64;v=128;ql=1536;kvl=512
    mats=[('q_a',ql,spec.H,'BF16'),('q_b',nq*(nope+rope),ql,'BF16'),('kv_a',kvl+rope,spec.H,'BF16'),('kv_b',nq*(nope+v),kvl,'BF16'),('o_proj',spec.H,nq*v,'BF16')]
    aw,ah=matrix_row(p,mats,x,y,30);mx=x+aw+60;weight_matrix(p,'router',mx,y,spec.E,spec.H);exy=y+160;egw,egh=expert_grid(p,mx,exy,spec.E,spec.H,spec.expert_I,spec.expert_weight_dtype or spec.weight_dtype);sy=exy+egh+45;sw,sh=dense_weight_footprint(p,mx,sy,spec.H,spec.expert_I,'SwiGLU',spec.expert_weight_dtype or spec.weight_dtype);weight_matrix(p,'shared scalar gate',mx+sw+40,sy,spec.shared_experts,spec.H,spec.weight_dtype);bottom=sy+max(sh,80)
    ay=bottom+70;p.text('<b>Activation + cache footprint</b>',x,ay-30,350,24,TEXT_LEFT);activation(p,'X prefill',x,ay,spec.H,kind='input');activation(p,'Q low-rank',x+180,ay,ql);activation(p,'KV latent cache',x+340,ay,kvl+rope,kind='state')
    y2=ay+180;score_grid(p,'MLA score',x,y2,nq,T,'act',cols=16);score_grid(p,'MLA probability',x+520,y2,nq,T,'norm',cols=16)
    y3=y2+310;activation(p,'Attention output',x,y3,nq*v);activation(p,'Router logits',x+250,y3,spec.E,dtype='FP32',kind='act');activation(p,'Dispatched rows',x+450,y3,spec.H,T*spec.K,kind='norm');activation(p,'Expert intermediate',x+700,y3,spec.expert_I,T*spec.K);return y3+500


def deepseek_v4_footprint(p:Page,spec:ModelSpec,mode:str,*,x:float=900,y:float=135)->float:
    p.text('<b>Weight footprint</b>',x,y-30,300,24,TEXT_LEFT)
    nq=64;hd=512;ql=1024;ol=1024
    mats=[('q_a',ql,spec.H,'BF16'),('q_b',nq*hd,ql,'BF16'),('shared K=V',hd,spec.H,'BF16'),('o_lora_A',ol,nq*hd,'BF16'),('o_lora_B',spec.H,ol,'BF16')]
    if mode=='CSA':mats.extend([('compressor',hd,hd,'BF16'),('indexer Q/K',64*128,spec.H,'BF16')])
    elif mode=='HCA':mats.extend([('compressor L1',hd,hd,'BF16'),('compressor L2',hd,hd,'BF16')])
    aw,ah=matrix_row(p,mats,x,y,25);mx=x+aw+55;weight_matrix(p,'router',mx,y,spec.E,spec.H);exy=y+160;egw,egh=expert_grid(p,mx,exy,spec.E,spec.H,spec.expert_I,spec.expert_weight_dtype or spec.weight_dtype);sy=exy+egh+45;sw,sh=dense_weight_footprint(p,mx,sy,spec.H,spec.expert_I,'SwiGLU',spec.expert_weight_dtype or spec.weight_dtype);weight_matrix(p,'shared scalar gate',mx+sw+40,sy,spec.shared_experts,spec.H,spec.weight_dtype);bottom=sy+max(sh,80)
    ay=bottom+70;p.text('<b>Activation + state footprint</b>',x,ay-30,380,24,TEXT_LEFT);activation(p,'4 residual streams',x,ay,4*spec.H,kind='input');activation(p,'Q low-rank',x+350,ay,ql);activation(p,'Shared K/V cache',x+520,ay,hd,kind='state')
    y2=ay+220;activation(p,'Local W=128 score/prob',x,y2,2*nq*128,kind='norm');
    if mode=='CSA':activation(p,'Compressed KV',x+350,y2,hd,T//4,kind='state');activation(p,'Top-512 selected indices',x+520,y2,512,T,dtype='FP32',kind='norm')
    elif mode=='HCA':activation(p,'Hierarchical compressed KV',x+350,y2,hd,max(1,T//128),kind='state')
    y3=y2+220;activation(p,'Attention output',x,y3,nq*hd);activation(p,'Router logits',x+350,y3,spec.E,dtype='FP32',kind='act');activation(p,'Dispatched rows',x+520,y3,spec.H,T*spec.K,kind='norm');activation(p,'Expert intermediate',x+800,y3,spec.expert_I,T*spec.K);return y3+500


# -------------------------- source sample and family grouping --------------------------
TOP90: list[tuple[str,float,str]] = [
('Qwen/Qwen3-0.6B',24.3,'Qwen3 dense'),('trl-internal-testing/tiny-Qwen2ForCausalLM-2.5',15.7,'Qwen2/2.5 dense'),('facebook/opt-125m',14.8,'OPT dense'),('Qwen/Qwen3-8B',14.7,'Qwen3 dense'),('openai-community/gpt2',14.2,'GPT-2 dense'),('unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF',12.7,'Qwen3 MoE'),('nvidia/Qwen3.6-35B-A3B-NVFP4',12.4,'Qwen3.5/3.6 hybrid MoE'),('Qwen/Qwen2.5-7B-Instruct',11.5,'Qwen2/2.5 dense'),('Qwen/Qwen2.5-1.5B-Instruct',8.86,'Qwen2/2.5 dense'),('Qwen/Qwen2.5-3B-Instruct',7.58,'Qwen2/2.5 dense'),('meta-llama/Llama-3.2-1B-Instruct',7.52,'Llama/Yi/SmolLM dense'),('farbodtavakkoli/OTel-2.0-LLM-31B-IT',7.15,'Gemma4 dense'),('openai/gpt-oss-20b',7.04,'GPT-OSS MoE'),('Qwen/Qwen2.5-0.5B-Instruct',6.83,'Qwen2/2.5 dense'),('meta-llama/Llama-3.1-8B-Instruct',6.44,'Llama/Yi/SmolLM dense'),('deepseek-ai/DeepSeek-R1',5.04,'DeepSeek V3/R1 MLA MoE'),('openai/gpt-oss-120b',5.01,'GPT-OSS MoE'),('ornith-ai/Ornith-1.0-9B-GGUF',4.95,'Qwen3.5/3.6 hybrid dense'),('Qwen/Qwen3-4B',4.84,'Qwen3 dense'),('dphn/dolphin-2.9.1-yi-1.5-34b',4.72,'Llama/Yi/SmolLM dense'),('Qwen/Qwen3-1.7B',4.71,'Qwen3 dense'),('google/gemma-3-1b-it',4.71,'Gemma3 dense'),('Qwen/Qwen2.5-7B-Instruct-AWQ',4.21,'Qwen2/2.5 dense'),('ornith-ai/Ornith-1.0-35B-GGUF',3.67,'Qwen3.5/3.6 hybrid MoE'),('Qwen/Qwen3-32B',3.62,'Qwen3 dense'),('EleutherAI/pythia-160m',3.53,'GPT-NeoX/Pythia dense'),('Qwen/Qwen3-4B-Instruct-2507',3.41,'Qwen3 dense'),('ornith-ai/Ornith-1.0-35B',3.32,'Qwen3.5/3.6 hybrid MoE'),('deepseek-ai/DeepSeek-V4-Flash-0731',3.27,'DeepSeek V4 hybrid MoE'),('RadixArk/Kimi-K3-DSpark',2.93,'Kimi K3 hybrid MoE'),('Qwen/Qwen2.5-14B-Instruct',2.82,'Qwen2/2.5 dense'),('Qwen/Qwen3-30B-A3B',2.59,'Qwen3 MoE'),('zai-org/GLM-5.2',2.58,'GLM DSA MoE'),('hmellor/tiny-random-LlamaForCausalLM',2.54,'Llama/Yi/SmolLM dense'),('HuggingFaceTB/SmolLM2-135M',2.53,'Llama/Yi/SmolLM dense'),('Qwen/Qwen2.5-Coder-7B-Instruct',2.44,'Qwen2/2.5 dense'),('Qwen/Qwen2.5-32B-Instruct',2.33,'Qwen2/2.5 dense'),('nvidia/Gemma-4-31B-IT-NVFP4',2.26,'Gemma4 dense'),('Qwen/Qwen3-14B-AWQ',2.25,'Qwen3 dense'),('distilbert/distilgpt2',2.24,'GPT-2 dense'),('Qwen/Qwen2.5-Coder-14B-Instruct',2.21,'Qwen2/2.5 dense'),('ornith-ai/Ornith-1.0-9B',2.21,'Qwen3.5/3.6 hybrid dense'),('TinyLlama/TinyLlama-1.1B-Chat-v1.0',2.18,'Llama/Yi/SmolLM dense'),('Qwen/Qwen2.5-14B-Instruct-AWQ',2.17,'Qwen2/2.5 dense'),('ibm-granite/granite-4.1-8b',2.12,'Granite4 hybrid'),('Qwen/Qwen-72B',2.04,'Qwen1 dense'),('Qwen/Qwen3-14B',2.0,'Qwen3 dense'),('zai-org/GLM-4.7-Flash',1.99,'GLM DSA MoE'),('Qwen/Qwen2.5-0.5B',1.9,'Qwen2/2.5 dense'),('prism-ml/Ternary-Bonsai-27B-mlx-2bit',1.89,'Qwen3.5/3.6 hybrid dense'),('prism-ml/Bonsai-27B-mlx-1bit',1.87,'Qwen3.5/3.6 hybrid dense'),('antirez/deepseek-v4-gguf',1.82,'DeepSeek V4 hybrid MoE'),('zai-org/GLM-5.2-FP8',1.77,'GLM DSA MoE'),('deepseek-ai/DeepSeek-V4-Flash',1.76,'DeepSeek V4 hybrid MoE'),('Qwen/Qwen3-Coder-Next-FP8',1.75,'Qwen3.5/3.6 hybrid MoE'),('Qwen/Qwen3-8B-AWQ',1.74,'Qwen3 dense'),('meta-llama/Meta-Llama-3-8B-Instruct',1.73,'Llama/Yi/SmolLM dense'),('nvidia/Gemma-4-26B-A4B-NVFP4',1.65,'Gemma4 MoE'),('Qwen/Qwen3-30B-A3B-Instruct-2507',1.64,'Qwen3 MoE'),('google/gemma-3-270m',1.63,'Gemma3 dense'),('HuggingFaceTB/SmolLM2-135M-Instruct',1.61,'Llama/Yi/SmolLM dense'),('farbodtavakkoli/OTel-LLM-E4B-IT',1.57,'Gemma4 MoE'),('microsoft/phi-2',1.56,'Phi-2 dense'),('meta-llama/Llama-3.2-1B',1.55,'Llama/Yi/SmolLM dense'),('Qwen/Qwen2.5-Coder-32B-Instruct',1.47,'Qwen2/2.5 dense'),('JonathanColetti/Qwen3.8-27B-Uncensored-GGUF',1.46,'Qwen3.5/3.6 hybrid dense'),('Qwen/Qwen2-1.5B-Instruct',1.43,'Qwen2/2.5 dense'),('Qwen/Qwen2.5-Coder-32B-Instruct-AWQ',1.4,'Qwen2/2.5 dense'),('bigscience/bloomz-560m',1.38,'BLOOM dense'),('QuantTrio/Qwen3-VL-30B-A3B-Instruct-AWQ',1.37,'Qwen3 MoE'),('apple/OpenELM-1_1B-Instruct',1.35,'OpenELM dense'),('ibm-research/PowerMoE-3b',1.33,'PowerMoE'),('meta-llama/Meta-Llama-3-8B',1.32,'Llama/Yi/SmolLM dense'),('nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4',1.32,'Nemotron3 hybrid MoE'),('trl-internal-testing/tiny-Qwen3ForCausalLM',1.31,'Qwen3 dense'),('Qwen/Qwen2.5-Coder-14B-Instruct-AWQ',1.31,'Qwen2/2.5 dense'),('Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8',1.29,'Qwen3 MoE'),('nvidia/GLM-5.2-NVFP4',1.27,'GLM DSA MoE'),('sshleifer/tiny-gpt2',1.23,'GPT-2 dense'),('Qwen/Qwen3-1.7B-Base',1.22,'Qwen3 dense'),('Qwen/Qwen3-4B-Instruct-2507-FP8',1.19,'Qwen3 dense'),('mistralai/Mistral-7B-Instruct-v0.2',1.18,'Mistral dense'),('deepseek-ai/DeepSeek-V3.2',1.18,'DeepSeek V3/R1 MLA MoE'),('openai-community/gpt2-large',1.18,'GPT-2 dense'),('nvidia/Qwen3.6-27B-NVFP4',1.15,'Qwen3.5/3.6 hybrid dense'),('farbodtavakkoli/OTel-LLM-27B-IT',1.15,'Gemma4 dense'),('deepseek-ai/DeepSeek-R1-0528-Qwen3-8B',1.14,'Qwen3 dense'),('Qwen/Qwen3-4B-Base',1.11,'Qwen3 dense'),('Bahushruth/Qwen3.6-35B-A3B-abliterated-v4',1.08,'Qwen3.5/3.6 hybrid MoE'),('sakamakismile/Qwen3.6-27B-Text-NVFP4-MTP',1.07,'Qwen3.5/3.6 hybrid dense')]


def family_coverage() -> list[dict]:
    total=sum(v for _,v,_ in TOP90);agg=defaultdict(float);members=defaultdict(list)
    for repo,v,f in TOP90:agg[f]+=v;members[f].append(repo)
    rows=[];cum=0.0
    for rank,(f,v) in enumerate(sorted(agg.items(),key=lambda kv:-kv[1]),1):
        cum+=v;rows.append({'rank':rank,'family':f,'downloads_m':round(v,3),'share_pct':round(100*v/total,3),'cumulative_pct':round(100*cum/total,3),'included_90pct':cum-v < 0.90*total,'members':' | '.join(members[f])})
    return rows


def write_csvs() -> None:
    with TOP90_CSV.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['rank','repository','downloads_m','mapped_architecture_family'])
        for i,(repo,v,fam) in enumerate(TOP90,1):w.writerow([i,repo,v,fam])
    rows=family_coverage()
    with COVERAGE_CSV.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def overview_page(rows:list[dict]) -> Page:
    p=Page('00_覆盖口径与结构索引',3000,1900,None)
    header(p,'Open-weight LLM Block Architecture Atlas — coverage and topology index',
           'Source sample: current Hugging Face text-generation repositories sorted by downloads; top 90 repositories, total 335.49M displayed downloads. Quantized/fine-tuned/test variants are merged by block topology.')
    p.vertex('<b>Coverage rule</b><br>Families are sorted by summed downloads within the 90-repository sample. The strict 90% cutoff is reached after Gemma 3 at 91.60%. DeepSeek V3/R1 is also drawn as a high-impact supplement, raising drawn coverage to 93.45%.',25,130,930,90,NOTE_STYLE)
    x=25;y=250;rowh=54
    headers=['Rank','Architecture family','Downloads','Share','Cumulative','Atlas pages']
    widths=[70,420,130,100,120,800];cx=x
    for h,w in zip(headers,widths):p.vertex(f'<b>{h}</b>',cx,y,w,32,'rounded=0;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=10;');cx+=w
    page_map={
        'Qwen2/2.5 dense':'01','Qwen3 dense':'02','Llama/Yi/SmolLM dense':'03','Qwen3.5/3.6 hybrid MoE':'06–07','Qwen3 MoE':'04','GPT-2 dense':'08','OPT dense':'09','Qwen3.5/3.6 hybrid dense':'05A–05B','GPT-OSS MoE':'10A–10B','Gemma4 dense':'11A–11B','GLM DSA MoE':'12','DeepSeek V4 hybrid MoE':'13A–13C','Gemma3 dense':'14A–14B','DeepSeek V3/R1 MLA MoE':'15 (supplement)'}
    for i,r in enumerate(rows[:14]):
        yy=y+32+i*rowh;inc='yes' if r['included_90pct'] else ('supplement' if r['family']=='DeepSeek V3/R1 MLA MoE' else 'no')
        vals=[r['rank'],r['family'],f"{r['downloads_m']:.2f}M",f"{r['share_pct']:.2f}%",f"{r['cumulative_pct']:.2f}%",page_map.get(r['family'],'outside cutoff')]
        cx=x
        for j,(val,w) in enumerate(zip(vals,widths)):
            fill='#d5e8d4' if inc=='yes' else '#fff2cc' if inc=='supplement' else '#ffffff'
            p.vertex(str(val),cx,yy,w,rowh,f'rounded=0;whiteSpace=wrap;html=1;fillColor={fill};strokeColor=#b3b3b3;fontSize=9;align={"left" if j in (1,5) else "center"};spacing=4;');cx+=w
    p.vertex('<b>Color grammar</b><br>Blue: large matrix multiplication/projection suited to MAC arrays. Purple: normalization, nonlinear, elementwise, routing/top-k, mask, reshape, state/control. Green: cache/state. Red: weights. Orange/yellow: input/residual.',1780,250,1050,130,NOTE_STYLE)
    p.vertex('<b>Footprint grammar</b><br>All atlas pages use 1 px² = 4 KiB. Each matrix rectangle keeps the ratio of its output and input dimensions. Expert grids draw every routed expert rather than hiding them in one opaque box. Activations are logical named tensors, not a peak-liveness allocator result.',1780,410,1050,150,NOTE_STYLE)
    p.vertex('<b>Scope caveat</b><br>“Open LLM” here means publicly downloadable/open-weight model repositories. Download counters are a reproducible proxy, not unique users, deployed tokens, or market share. The separate revised Qwen file preserves the user reference scale of 1 px² = 100 bytes.',1780,590,1050,140,NOTE_STYLE)
    return p


def build_pages() -> list[Page]:
    rows=family_coverage();pages=[overview_page(rows)]
    specs={
      'qwen25':ModelSpec('qwen25','Qwen2/2.5 Dense','Qwen2/2.5 dense',1536,8960,12,2,128,norm='RMSNorm',mlp='SwiGLU',bias=True,equivalent='Qwen2 / Qwen2.5 dense sizes and coder/instruct/quantized variants; same block topology, dimensions differ.'),
      'qwen3':ModelSpec('qwen3','Qwen3 Dense','Qwen3 dense',2048,6144,16,8,128,norm='RMSNorm',mlp='SwiGLU',qk_norm=True,equivalent='Qwen3 0.6B/1.7B/4B/8B/14B/32B and dense coder/instruct/AWQ/FP8 variants.'),
      'llama':ModelSpec('llama','Llama/Yi/SmolLM Dense','Llama/Yi/SmolLM dense',2048,8192,32,8,64,norm='RMSNorm',mlp='SwiGLU',equivalent='Llama 3/3.1/3.2, TinyLlama, Yi-1.5 and SmolLM2 share the pre-norm RoPE + GQA/MHA + SwiGLU block; head counts and dimensions vary.'),
      'q3moe':ModelSpec('q3moe','Qwen3 MoE','Qwen3 MoE',2048,0,32,4,128,norm='RMSNorm',mlp='SwiGLU',qk_norm=True,E=128,K=8,expert_I=768,equivalent='Qwen3-30B-A3B, Qwen3-Coder-30B-A3B, their instruct/FP8/GGUF/AWQ variants; text blocks of Qwen3-VL-30B-A3B are isomorphic.'),
      'q35d_gdn':ModelSpec('q35d_gdn','Qwen3.5/3.6 Dense GDN','Qwen3.5/3.6 hybrid dense',2048,6144,16,16,128,norm='RMSNorm',mlp='SwiGLU',equivalent='Qwen3.5-2B, Ornith-1.0-9B, Bonsai/Ternary-Bonsai 27B, Qwen3.6/3.8 dense variants use the same GDN-vs-full-attention hybrid topology; dimensions differ.'),
      'q35d_fa':ModelSpec('q35d_fa','Qwen3.5/3.6 Dense Full Attention','Qwen3.5/3.6 hybrid dense',2048,6144,8,2,256,norm='RMSNorm',mlp='SwiGLU',qk_norm=True,q_gate=True,partial_rope=.25,equivalent='Same models as the GDN page; the stack normally interleaves 3 GDN blocks with 1 full-attention block.'),
      'q35m_gdn':ModelSpec('q35m_gdn','Qwen3.5/3.6 MoE GDN','Qwen3.5/3.6 hybrid MoE',2048,0,16,32,128,norm='RMSNorm',mlp='SwiGLU',E=256,K=8,expert_I=512,shared_experts=1,equivalent='Qwen3.5-35B-A3B, Qwen3.6-35B-A3B, Ornith-1.0-35B and coder-next/quantized variants.'),
      'q35m_fa':ModelSpec('q35m_fa','Qwen3.5/3.6 MoE Full Attention','Qwen3.5/3.6 hybrid MoE',2048,0,16,2,256,norm='RMSNorm',mlp='SwiGLU',qk_norm=True,q_gate=True,partial_rope=.25,E=256,K=8,expert_I=512,shared_experts=1,equivalent='Same models as the MoE-GDN page; 3:1 GDN/full-attention layer pattern.'),
      'gpt2':ModelSpec('gpt2','GPT-2 Dense','GPT-2 dense',768,3072,12,12,64,norm='LayerNorm',mlp='GELU',bias=True,equivalent='GPT-2 small/medium/large/XL, DistilGPT2 and tiny-gpt2 preserve the combined-QKV, pre-LN, absolute-position, GELU-MLP block topology.'),
      'opt':ModelSpec('opt','OPT Dense','OPT dense',768,3072,12,12,64,norm='LayerNorm',mlp='ReLU',bias=True,equivalent='OPT 125M through 175B keep the same learned-position, separate-QKV, pre-LN attention and ReLU FFN topology; dimensions differ.'),
      'gptoss_s':ModelSpec('gptoss_s','GPT-OSS Sliding Attention + MoE','GPT-OSS MoE',2880,0,64,8,64,attention='sliding',window=128,norm='RMSNorm',mlp='SwiGLU',bias=True,E=32,K=4,expert_I=2880,weight_dtype='BF16',expert_weight_dtype='MXFP4',equivalent='gpt-oss-20b and gpt-oss-120b share alternating sliding/full attention, learned attention sinks and top-4 MoE; layer count/expert dimensions differ.'),
      'gptoss_f':ModelSpec('gptoss_f','GPT-OSS Full Attention + MoE','GPT-OSS MoE',2880,0,64,8,64,attention='full',norm='RMSNorm',mlp='SwiGLU',bias=True,E=32,K=4,expert_I=2880,weight_dtype='BF16',expert_weight_dtype='MXFP4',equivalent='Same GPT-OSS family; this is the alternating full-attention block.'),
      'gemma4_s':ModelSpec('gemma4_s','Gemma 4 Sliding Attention Dense','Gemma4 dense',5376,21504,32,16,256,attention='sliding',window=1024,norm='RMSNorm',mlp='GeGLU',qk_norm=True,equivalent='Gemma-4-31B and OTel 31B/27B derivatives; five sliding blocks precede each full-attention block.',note='K=V'),
      'gemma4_f':ModelSpec('gemma4_f','Gemma 4 Full Attention Dense','Gemma4 dense',5376,21504,32,4,512,attention='full',norm='RMSNorm',mlp='GeGLU',qk_norm=True,partial_rope=.25,equivalent='Same Gemma 4 dense family; global/full block uses 4 KV heads, 512-d heads and partial rotary factor 0.25.',note='K=V'),
      'glm':ModelSpec('glm','GLM-5.2 DSA + MoE','GLM DSA MoE',6144,12288,64,64,256,norm='RMSNorm',mlp='SwiGLU',E=256,K=8,expert_I=2048,shared_experts=1,equivalent='GLM-5.2, GLM-5.2-FP8/NVFP4 and GLM-4.7-Flash derivatives use the DSA/MLA + sparse MoE family topology; exact layer/indexer schedules differ.'),
      'dsv4':ModelSpec('dsv4','DeepSeek V4 Hybrid + MoE','DeepSeek V4 hybrid MoE',4096,0,64,1,512,norm='RMSNorm',mlp='SwiGLU',E=256,K=6,expert_I=2048,shared_experts=1,weight_dtype='BF16',expert_weight_dtype='FP4',equivalent='DeepSeek-V4-Flash, DeepSeek-V4-Flash-0731 and GGUF/quantized derivatives. The stack mixes sliding-only, CSA and HCA blocks with mHC residual streams.'),
      'gemma3_s':ModelSpec('gemma3_s','Gemma 3 Sliding Attention Dense','Gemma3 dense',1152,6912,4,1,256,attention='sliding',window=512,norm='RMSNorm',mlp='GeGLU',qk_norm=True,equivalent='Gemma-3 270M/1B/4B/12B/27B share alternating 5 local sliding + 1 global full blocks; representative dimensions here use the 1B text model.'),
      'gemma3_f':ModelSpec('gemma3_f','Gemma 3 Full Attention Dense','Gemma3 dense',1152,6912,4,1,256,attention='full',norm='RMSNorm',mlp='GeGLU',qk_norm=True,equivalent='Same Gemma 3 family; global block differs in mask/rotary treatment rather than the FFN topology.'),
      'dsv3':ModelSpec('dsv3','DeepSeek V3 / R1 MLA + MoE','DeepSeek V3/R1 MLA MoE',7168,18432,128,128,192,norm='RMSNorm',mlp='SwiGLU',E=256,K=8,expert_I=2048,shared_experts=1,equivalent='DeepSeek-V3, V3.2 and DeepSeek-R1 share MLA plus 256-expert top-8 MoE; this supplemental family lifts drawn sample coverage from 91.60% to 93.45%.'),
    }
    # Standard families
    p=Page('01_Qwen2_Qwen2.5_Dense',4200,2850,specs['qwen25']);header(p,'Qwen2 / Qwen2.5 — dense decoder block','Representative: Qwen2.5-1.5B, H=1536, I=8960, 12 Q heads, 2 KV heads, d=128, T=1024',p.spec.equivalent);draw_standard_attention_flow(p,p.spec);standard_footprint(p,p.spec);pages.append(p)
    p=Page('02_Qwen3_Dense',4200,2850,specs['qwen3']);header(p,'Qwen3 — dense decoder block','Representative: Qwen3-1.7B, H=2048, I=6144, 16 Q heads, 8 KV heads, d=128, Q/K head norm',p.spec.equivalent);draw_standard_attention_flow(p,p.spec);standard_footprint(p,p.spec);pages.append(p)
    p=Page('03_Llama_Yi_SmolLM_Dense',4200,2850,specs['llama']);header(p,'Llama / Yi / SmolLM — dense decoder block','Representative: Llama-3.2-1B, H=2048, I=8192, 32 Q heads, 8 KV heads, d=64',p.spec.equivalent);draw_standard_attention_flow(p,p.spec);standard_footprint(p,p.spec);pages.append(p)
    p=Page('04_Qwen3_MoE',5200,4700,specs['q3moe']);header(p,'Qwen3 — full attention + routed MoE block','Representative: Qwen3-30B-A3B, H=2048, 32 Q / 4 KV heads, E=128, top-8, expert I=768',p.spec.equivalent);draw_standard_attention_flow(p,p.spec,moe=True);standard_footprint(p,p.spec,moe=True);pages.append(p)
    p=Page('05A_Qwen3.5_Dense_GDN',4600,3500,specs['q35d_gdn']);header(p,'Qwen3.5 / 3.6 dense — GDN block','Representative: H=2048, K/V heads=16/16, dK=dV=128, DWConv k=4, dense SwiGLU I=6144',p.spec.equivalent);draw_gdn_flow(p,p.spec,moe=False);gdn_footprint(p,p.spec,moe=False);pages.append(p)
    p=Page('05B_Qwen3.5_Dense_FullAttention',4300,3000,specs['q35d_fa']);header(p,'Qwen3.5 / 3.6 dense — gated full-attention block','Representative: H=2048, 8 Q / 2 KV heads, d=256, Q-gate, partial RoPE, dense SwiGLU I=6144',p.spec.equivalent);draw_standard_attention_flow(p,p.spec);standard_footprint(p,p.spec);pages.append(p)
    p=Page('06_Qwen3.5_MoE_GDN',6100,6100,specs['q35m_gdn']);header(p,'Qwen3.5 / 3.6 MoE — GDN block','Representative: H=2048, K/V heads=16/32, d=128, E=256, top-8, one shared expert, expert I=512',p.spec.equivalent);draw_gdn_flow(p,p.spec,moe=True);gdn_footprint(p,p.spec,moe=True);pages.append(p)
    p=Page('07_Qwen3.5_MoE_FullAttention',6100,5700,specs['q35m_fa']);header(p,'Qwen3.5 / 3.6 MoE — gated full-attention block','Representative: H=2048, 16 Q / 2 KV heads, d=256, E=256, top-8, one shared expert',p.spec.equivalent);draw_standard_attention_flow(p,p.spec,moe=True);standard_footprint(p,p.spec,moe=True);pages.append(p)
    p=Page('08_GPT2_Dense',4000,2450,specs['gpt2']);header(p,'GPT-2 — dense decoder block','Representative: GPT-2 small, H=768, 12 MHA heads, I=3072, learned absolute position, GELU FFN',p.spec.equivalent);draw_gpt2_opt_flow(p,p.spec,opt=False);gpt2_opt_footprint(p,p.spec,opt=False);pages.append(p)
    p=Page('09_OPT_Dense',4000,2450,specs['opt']);header(p,'OPT — dense decoder block','Representative: OPT-125M, H=768, 12 MHA heads, I=3072, learned absolute position, ReLU FFN',p.spec.equivalent);draw_gpt2_opt_flow(p,p.spec,opt=True);gpt2_opt_footprint(p,p.spec,opt=True);pages.append(p)
    for suf,key,attn in [('A','gptoss_s','sliding'),('B','gptoss_f','full')]:
        sp=specs[key];p=Page(f'10{suf}_GPT_OSS_{attn.title()}',5400,5000,sp);header(p,f'GPT-OSS — {attn} attention + top-4 MoE block',f'H=2880, 64 Q / 8 KV heads, d=64, E=32, top-4, expert I=2880, MXFP4 expert weights',sp.equivalent);draw_standard_attention_flow(p,sp,attention_sink=True,moe=True);standard_footprint(p,sp,moe=True,attention_sink=True);pages.append(p)
    for suf,key in [('A','gemma4_s'),('B','gemma4_f')]:
        sp=specs[key];p=Page(f'11{suf}_Gemma4_{sp.attention.title()}',5200,3600,sp);header(p,f'Gemma 4 — {sp.attention} attention dense block',f'H=5376, I=21504, Q heads=32, KV heads={sp.nkv}, head_dim={sp.D}, K=V shared projection',sp.equivalent);draw_gemma_flow(p,sp);gemma_footprint(p,sp,k_eq_v=True);pages.append(p)
    sp=specs['glm'];p=Page('12_GLM5.2_DSA_MoE',7600,7200,sp);header(p,'GLM-5.2 — DeepSeek Sparse Attention + MLA + MoE block','H=6144, Q LoRA rank=2048, KV latent rank=512, DSA indexer 32×128 top-2048, E=256 top-8 + shared expert',sp.equivalent);draw_glm_dsa_flow(p,sp);glm_footprint(p,sp);pages.append(p)
    for suf,mode in [('A','Sliding-only'),('B','CSA'),('C','HCA')]:
        sp=specs['dsv4'];p=Page(f'13{suf}_DeepSeekV4_{mode.replace("-","")}',7600,6900,sp);header(p,f'DeepSeek V4 — {mode} + mHC + MoE block',f'H=4096, 64 Q heads, shared K=V head d=512, Q/O LoRA rank=1024, E=256 top-6 + shared expert',sp.equivalent);draw_deepseek_v4_flow(p,sp,mode);deepseek_v4_footprint(p,sp,mode);pages.append(p)
    for suf,key in [('A','gemma3_s'),('B','gemma3_f')]:
        sp=specs[key];p=Page(f'14{suf}_Gemma3_{sp.attention.title()}',4400,3300,sp);header(p,f'Gemma 3 — {sp.attention} attention dense block',f'Representative 1B text block: H=1152, I=6912, 4 Q heads, 1 KV head, d=256',sp.equivalent);draw_gemma_flow(p,sp);gemma_footprint(p,sp,k_eq_v=False);pages.append(p)
    sp=specs['dsv3'];p=Page('15_DeepSeekV3_R1_MLA_MoE',7600,7000,sp);header(p,'DeepSeek V3 / R1 — Multi-head Latent Attention + MoE block','H=7168, Q LoRA rank=1536, KV latent rank=512, 128 heads, E=256 top-8 + one shared expert',sp.equivalent);draw_deepseek_v3_flow(p,sp);deepseek_v3_footprint(p,sp);pages.append(p)
    return pages


def write_drawio(pages:Sequence[Page])->None:
    root=ET.Element('mxfile',{'host':'Electron','modified':'2026-08-25T00:00:00.000Z','agent':'GPT-5.6 Pro','version':'24.7.17','type':'device'})
    for p in pages:
        d=ET.SubElement(root,'diagram',{'name':p.name,'id':str(uuid.uuid4())});d.append(p.model)
    ET.indent(root,space='  ');ET.ElementTree(root).write(OUT,encoding='utf-8',xml_declaration=False)


def validate(path:Path)->dict:
    root=ET.parse(path).getroot();res={'pages':0,'cells':0,'vertices':0,'edges':0,'bounds_ok':True,'red_weight_overlap_pairs':[],'pages_summary':{}}
    for d in root.findall('diagram'):
        res['pages']+=1;gm=d.find('mxGraphModel');pw=float(gm.get('pageWidth'));ph=float(gm.get('pageHeight'));mx=my=0.;red=[]
        for c in gm.find('root').findall('mxCell'):
            res['cells']+=1
            if c.get('vertex')=='1':
                res['vertices']+=1;g=c.find('mxGeometry');x=float(g.get('x',0));y=float(g.get('y',0));w=float(g.get('width',0));h=float(g.get('height',0));mx=max(mx,x+w);my=max(my,y+h)
                if x<0 or y<0 or x+w>pw+1 or y+h>ph+1:res['bounds_ok']=False
                if '#f8cecc' in c.get('style','') and w>1.5 and h>1.5:red.append((c.get('id'),x,y,w,h))
            if c.get('edge')=='1':res['edges']+=1
        # Overlap detection is restricted to weight rectangles. Borders/text do not count.
        for i,a in enumerate(red):
            for b in red[i+1:]:
                ix=min(a[1]+a[3],b[1]+b[3])-max(a[1],b[1]);iy=min(a[2]+a[4],b[2]+b[4])-max(a[2],b[2])
                if ix>0.75 and iy>0.75:res['red_weight_overlap_pairs'].append([d.get('name'),a[0],b[0],round(ix*iy,2)])
        res['pages_summary'][d.get('name')]={'extent':[round(mx,1),round(my,1)],'page':[pw,ph],'red_weights':len(red)}
    return res


def semantic_validate(path: Path) -> dict:
    root = ET.parse(path).getroot()
    values: list[str] = []
    cells: list[tuple[str, str]] = []
    for cell in root.iter('mxCell'):
        raw = html.unescape(cell.get('value', ''))
        text = __import__('re').sub(r'<[^>]+>', ' ', raw)
        text = ' '.join(text.replace('&#10;', ' ').split())
        if text:
            values.append(text)
        cells.append((text, cell.get('style', '')))
    joined = '\n'.join(values)

    def styles(label: str) -> list[str]:
        return [style for text, style in cells if label in text]

    def any_style(label: str, color: str) -> bool:
        return any(color in style for style in styles(label))

    blue = '#dae8fc'
    purple = '#e1d5e7'
    expected_pages = {
        '00_覆盖口径与结构索引', '01_Qwen2_Qwen2.5_Dense', '02_Qwen3_Dense',
        '03_Llama_Yi_SmolLM_Dense', '04_Qwen3_MoE', '05A_Qwen3.5_Dense_GDN',
        '05B_Qwen3.5_Dense_FullAttention', '06_Qwen3.5_MoE_GDN',
        '07_Qwen3.5_MoE_FullAttention', '08_GPT2_Dense', '09_OPT_Dense',
        '10A_GPT_OSS_Sliding', '10B_GPT_OSS_Full', '11A_Gemma4_Sliding',
        '11B_Gemma4_Full', '12_GLM5.2_DSA_MoE', '13A_DeepSeekV4_Slidingonly',
        '13B_DeepSeekV4_CSA', '13C_DeepSeekV4_HCA', '14A_Gemma3_Sliding',
        '14B_Gemma3_Full', '15_DeepSeekV3_R1_MLA_MoE',
    }
    actual_pages = {d.get('name', '') for d in root.findall('diagram')}
    checks = {
        'expected_22_pages_present': actual_pages == expected_pages,
        'no_sumEllipse_style': all('sumEllipse' not in style for _, style in cells),
        'no_1014_in_visible_labels': all('1014' not in text for text in values),
        'contains_1024_in_visible_labels': any('1024' in text for text in values),
        'ordinary_circle_plus_present': any(text == '+' and 'ellipse;' in style and 'sumEllipse' not in style for text, style in cells),
        'qk_gemm_blue': any_style('Q × Kᵀ', blue),
        'softmax_purple': any_style('Softmax FP32', purple),
        'router_projection_blue': any_style('Router projection', blue),
        'router_scoring_purple': any_style('Router scoring', purple),
        'dispatch_purple': any_style('Dispatch / gather', purple),
        'weighted_reduce_purple': any_style('Scatter / weighted reduce', purple),
        'expert_gate_proj_blue': any_style('gate_proj', blue),
        'expert_up_proj_blue': any_style('up_proj', blue),
        'expert_down_proj_blue': any_style('down_proj', blue),
        'expert_elementwise_purple': any_style('Elementwise gate', purple),
        'gdn_qkv_three_branches': all(label in joined for label in ('Q reshape', 'K reshape', 'V reshape')),
        'gdn_l2norm_explicit': all(label in joined for label in ('Q L2Norm', 'K L2Norm')),
        'gdn_chunk_rule_expanded': all(label in joined for label in ('Chunk Gated Delta Rule', 'K Kᵀ', 'Triangular solve', 'State read', 'State decay', 'Kᵀ U')),
        'complex_attention_families_expanded': all(label in joined for label in ('DeepSeek Sparse Attention indexer', 'MLA Q × Kᵀ', 'mHC Sinkhorn matrix')),
    }
    return {
        'checks': checks,
        'all_pass': all(checks.values()),
        'actual_page_names': sorted(actual_pages),
    }


def write_sources() -> None:
    text = '''# 来源、覆盖范围与结构合并原则

## 快照范围

- 快照日期：2026-08-25。
- 下载样本：Hugging Face `text-generation` 分类、按 displayed downloads 降序的前 90 个仓库。
- 样本总下载量：335.49M displayed downloads。
- 严格累计阈值：前 13 个结构家族达到 91.60%。
- 补充绘制：DeepSeek V3/R1 MLA MoE，使图集中已画家族达到 93.45%。
- “开放 LLM”在本交付中表示公开可下载权重或公开模型仓库，不等同于 OSI 定义的开源软件许可。

下载数会包含自动化测试、依赖缓存、量化副本、微调副本和重复拉取，因此这里只把它用作可复算的架构覆盖代理，不把它解释为唯一用户数、线上 token 份额或商业市场份额。

## 结构合并原则

只有以下条件同时成立时才合并到同一页：

1. 子层顺序和 residual 拓扑相同；
2. Attention/GDN/MLA/DSA 等状态语义相同；
3. Norm、激活、MoE 路由和专家数据流相同；
4. 差异主要是 H、I、head 数、expert 数、层数或量化位宽。

Sliding/Full Attention、GDN/Full Attention、Dense/MoE、MLA/DSA/HCA/CSA 等不是单纯维度差异，均分开绘制。

## 主要配置与实现依据

- Qwen2/Qwen2.5：`Qwen/Qwen2.5-1.5B/config.json`，以及 Qwen2 系列公开配置。
- Qwen3 Dense：`Qwen/Qwen3-1.7B/config.json`。
- Qwen3 MoE：`Qwen/Qwen3-30B-A3B/config.json`。
- Qwen3.5/Qwen3.6：Transformers 的 `modeling_qwen3_5.py`、`modeling_qwen3_5_moe.py` 和对应公开配置。
- Llama/Yi/SmolLM：各自公开配置及 Transformers 实现；合并的是 pre-norm RoPE + GQA/MHA + SwiGLU Block 拓扑。
- GPT-2：`openai-community/gpt2` 配置与 Transformers GPT-2 实现。
- OPT：`facebook/opt-125m` 配置与 Transformers OPT 实现。
- GPT-OSS：`openai/gpt-oss-20b/config.json` 与公开实现。
- Gemma 3：`google/gemma-3-1b-it/config.json` 与 Transformers Gemma 3 实现。
- Gemma 4：Gemma 4 公开配置及实现。
- GLM-5.2：`zai-org/GLM-5.2/config.json` 与公开实现。
- DeepSeek V4：`deepseek-ai/DeepSeek-V4-Flash/config.json` 与公开实现。
- DeepSeek V3/R1：`deepseek-ai/DeepSeek-R1/config.json`、DeepSeek V3/V3.2 公开配置与实现。

图中的权重面积按代表 checkpoint 的配置计算；同构模型只在页面顶部列出，不把不同尺寸的所有 checkpoint 重复画一遍。
'''
    (OUT_DIR / 'SOURCES_AND_SCOPE_CN.md').write_text(text, encoding='utf-8')


def write_readme(pages: Sequence[Page], rows: list[dict]) -> None:
    drawn_families = {
        'Qwen2/2.5 dense', 'Qwen3 dense', 'Llama/Yi/SmolLM dense',
        'Qwen3.5/3.6 hybrid MoE', 'Qwen3 MoE', 'GPT-2 dense', 'OPT dense',
        'Qwen3.5/3.6 hybrid dense', 'GPT-OSS MoE', 'Gemma4 dense',
        'GLM DSA MoE', 'DeepSeek V4 hybrid MoE', 'Gemma3 dense',
        'DeepSeek V3/R1 MLA MoE',
    }
    total = sum(v for _, v, _ in TOP90)
    drawn = sum(r['downloads_m'] for r in rows if r['family'] in drawn_families)
    strict = sum(r['downloads_m'] for r in rows if r['included_90pct'])

    page_rows = [
        ('01', 'Qwen2/Qwen2.5 Dense', 'Qwen2.5-1.5B', 'Qwen2、Qwen2.5 dense/coder/instruct/量化变体'),
        ('02', 'Qwen3 Dense', 'Qwen3-1.7B', 'Qwen3 0.6B–32B dense、coder/instruct/AWQ/FP8'),
        ('03', 'Llama/Yi/SmolLM Dense', 'Llama-3.2-1B', 'Llama 3/3.1/3.2、TinyLlama、Yi-1.5、SmolLM2'),
        ('04', 'Qwen3 MoE', 'Qwen3-30B-A3B', 'Qwen3 MoE/Coder/VL 文本 Block 及量化变体'),
        ('05A/05B', 'Qwen3.5/3.6 Dense Hybrid', 'Qwen3.5-2B', 'Ornith-9B、Bonsai-27B、Qwen3.6/3.8 dense；GDN 与 Full 分页'),
        ('06/07', 'Qwen3.5/3.6 MoE Hybrid', 'Qwen3.5-35B-A3B', 'Qwen3.6-35B-A3B、Ornith-35B、Coder-Next；GDN 与 Full 分页'),
        ('08', 'GPT-2 Dense', 'GPT-2 small', 'GPT-2 各尺寸、DistilGPT2、tiny-gpt2'),
        ('09', 'OPT Dense', 'OPT-125M', 'OPT 125M–175B'),
        ('10A/10B', 'GPT-OSS MoE', 'gpt-oss-20b', 'gpt-oss-20b/120b；Sliding 与 Full 分页'),
        ('11A/11B', 'Gemma 4 Dense', 'Gemma-4-31B', 'OTel 27B/31B 等衍生；Sliding 与 Full 分页'),
        ('12', 'GLM DSA MoE', 'GLM-5.2', 'GLM-5.2、GLM-4.7-Flash 及 FP8/NVFP4 变体'),
        ('13A/13B/13C', 'DeepSeek V4 Hybrid MoE', 'DeepSeek-V4-Flash', 'V4 Flash/0731/GGUF；Sliding-only、CSA、HCA 分页'),
        ('14A/14B', 'Gemma 3 Dense', 'Gemma-3-1B', 'Gemma-3 270M/1B/4B/12B/27B；Sliding 与 Full 分页'),
        ('15', 'DeepSeek V3/R1 MLA MoE', 'DeepSeek-R1', 'DeepSeek V3、V3.2、R1；作为 90% 阈值外补充'),
    ]

    lines = [
        '# 开放权重 LLM 单 Block 架构图集（B=1，T=1024）', '',
        '## 交付文件与统一绘图规则', '',
        '- 主图集：`open_llm_block_atlas_top90pct_1024.drawio`，22 页。',
        '- Qwen 精细修订：`qwen3_qwen35_blocks_1024_prefill_v3.drawio`，5 页。',
        '- Qwen 精细文件严格沿用参考图比例：`1 px² = 100 bytes`。',
        '- 跨模型图集为容纳 256-expert Block，统一使用：`1 px² = 4 KiB`。所有图集页面共享同一比例，不对大模型单独缩放。',
        '- 蓝色只表示可映射到大规模 MAC/GEMM/GEMV 的计算；紫色表示 Norm、非线性、逐元素、路由、Top-k、reshape、mask、归并、状态更新等非矩阵计算。',
        '- 绿色表示 cache/SRAM/recurrent state；红色表示权重；黄色/橙色表示 residual/input。',
        '- 红色权重矩形面积等于权重字节数，长宽比保留矩阵两维方向；MoE routed experts 按专家网格展开。',
        '- 激活面积为图中命名逻辑张量的累计体积，不等于峰值 live memory；FlashAttention、融合 kernel 或分块实现不必完整物化 S/P。', '',
        '## 本轮 Qwen 修订', '',
        '- GDN 的 `Split Q/K/V` 后使用三条独立连线；Q/K L2Norm 显式绘制。',
        '- `Chunk Gated Delta Rule` 展开为 chunk partition、decay matrix、KKᵀ、strict-lower system、triangular solve、QKᵀ、intra/state output、state decay 与 state update，并标注 token-equivalent recurrence。',
        '- Routed/shared expert 均展开 gate/up/activation/elementwise/down；Router projection、scoring、Top-k、dispatch、weighting 和 reduce 分开绘制。',
        '- residual 节点全部使用普通 Circle/Ellipse 内写 `+`，不再使用 `sumEllipse`。',
        '- `02_Qwen3.5-2B_GDN` 权重布局重排；红色权重矩形几何重叠数为 0。', '',
        '## 90% 下载覆盖口径', '',
        f'- 快照日期：2026-08-25；Hugging Face `text-generation` 前 90 个下载仓库，总计 {total:.2f}M displayed downloads。',
        f'- 严格阈值家族累计：{strict/total*100:.2f}%（在 Gemma 3 后超过 90%）。',
        f'- 加入 DeepSeek V3/R1 补充页后，已画家族覆盖：{drawn/total*100:.2f}%。',
        '- 量化、微调、测试 checkpoint 和同拓扑不同尺寸先归并到结构家族。下载数是架构覆盖代理，不是唯一用户数或线上 token 市场份额。',
        '- 这里的“开放”表示公开可下载权重/仓库，不保证满足 OSI 开源许可定义。', '',
        '## 页面与同构模型', '',
        '| 页码 | 结构家族 | 代表配置 | 同构/同拓扑模型 |',
        '|---|---|---|---|',
    ]
    lines.extend(f'| {idx} | {family} | {rep} | {equiv} |' for idx, family, rep, equiv in page_rows)
    lines += ['', '## 阈值外但出现在样本中的结构家族', '',
              '严格 90% 阈值之外还包括 GPT-NeoX/Pythia、Gemma 4 MoE、Kimi K3 Hybrid MoE、Granite 4 Hybrid、Qwen1、Phi-2、BLOOM、OpenELM、PowerMoE、Nemotron 3 Hybrid MoE 和 Mistral。它们合计约占该 90 仓库快照的 6.55%，本图集未宣称覆盖这部分结构。', '',
              '## 自动校验', '',
              '- draw.io XML 可解析，所有 vertex 均位于页面边界内。',
              '- 全部红色权重矩形执行几何重叠检查。',
              '- 禁止可见标签残留 `1014`，禁止 `shape=sumEllipse`。',
              '- 对 Router、Top-k、Dispatch、Expert GEMM、Weighted Reduce、GDN 三分支和 Chunk Delta Rule 执行语义/颜色门禁。',
              '- `top90_hf_text_generation_downloads_2026-08-25.csv` 保留原始仓库快照；`architecture_family_coverage.csv` 保留结构映射、份额和累计份额。', '',
              '## 重新生成', '',
              '```bash',
              'python generate_qwen_reference_style_v3.py',
              'python generate_open_llm_block_atlas.py',
              '```', '',
              '两个脚本和 Qwen 基础规格文件均包含在 ZIP 中，可在解压目录独立运行。', '']
    (OUT_DIR / 'README_CN.md').write_text('\n'.join(lines), encoding='utf-8')


def sha256(path:Path)->str:
    h=hashlib.sha256();
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def package() -> Path:
    files = [
        OUT,
        OUT_DIR / 'qwen3_qwen35_blocks_1024_prefill_v3.drawio',
        Path(__file__),
        OUT_DIR / 'generate_qwen_reference_style_v3.py',
        OUT_DIR / 'qwen_reference_style_base_v2.py',
        OUT_DIR / 'qwen_block_specs_base.py',
        TOP90_CSV,
        COVERAGE_CSV,
        VALIDATION_JSON,
        OUT_DIR / 'qwen_v3_validation.json',
        OUT_DIR / 'README_CN.md',
        OUT_DIR / 'SOURCES_AND_SCOPE_CN.md',
    ]
    sums = OUT_DIR / 'SHA256SUMS.txt'
    sums.write_text('\n'.join(f'{sha256(fp)}  {fp.name}' for fp in files if fp.exists()) + '\n', encoding='utf-8')
    files.append(sums)
    zip_path = OUT_DIR / 'open_llm_block_atlas_1024_package.zip'
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for fp in files:
            if fp.exists():
                zf.write(fp, arcname=fp.name)
    return zip_path


def main() -> None:
    write_csvs()
    rows = family_coverage()
    pages = build_pages()
    write_drawio(pages)
    val = validate(OUT)
    val['semantic_validation'] = semantic_validate(OUT)
    write_readme(pages, rows)
    write_sources()
    VALIDATION_JSON.write_text(json.dumps(val, ensure_ascii=False, indent=2), encoding='utf-8')
    if not val['bounds_ok']:
        raise SystemExit('out-of-bounds elements detected')
    if val['red_weight_overlap_pairs']:
        raise SystemExit(f'weight overlap detected: {val["red_weight_overlap_pairs"][:10]}')
    if not val['semantic_validation']['all_pass']:
        failed = [k for k, ok in val['semantic_validation']['checks'].items() if not ok]
        raise SystemExit(f'semantic validation failed: {failed}')
    z = package()
    print(OUT)
    print(z)
    print(json.dumps({k: v for k, v in val.items() if k != 'pages_summary'}, ensure_ascii=False))
    for page in pages:
        print(page.name, fmt_bytes(page.totals.weight_bytes), fmt_bytes(page.totals.activation_bytes))

if __name__=='__main__':main()

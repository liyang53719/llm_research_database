#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, html, importlib.util, json, zipfile, sys
from pathlib import Path
from typing import Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = SCRIPT_DIR.parent
BASE_PATH = SCRIPT_DIR / 'generate_open_llm_block_atlas.py'
spec = importlib.util.spec_from_file_location('base_atlas', BASE_PATH)
b = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b
assert spec.loader is not None
spec.loader.exec_module(b)

OUT_DIR = PACKAGE_DIR / 'generated' / 'all_families_atlas'
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / 'open_llm_block_atlas_all_families_1024.drawio'
TOP90_CSV = OUT_DIR / 'top90_hf_text_generation_downloads_2026-08-25.csv'
COVERAGE_CSV = OUT_DIR / 'architecture_family_coverage.csv'
VALIDATION_JSON = OUT_DIR / 'open_llm_atlas_allfamilies_validation.json'
README = OUT_DIR / 'README_CN.md'
SOURCES = OUT_DIR / 'SOURCES_AND_SCOPE_CN.md'
ZIP = OUT_DIR / 'open_llm_block_atlas_all_families_1024_package.zip'
SUMS = OUT_DIR / 'SHA256SUMS.txt'

# Patch base output constants so helper functions that rely on them remain consistent.
b.OUT_DIR = OUT_DIR
b.OUT = OUT
b.TOP90_CSV = TOP90_CSV
b.COVERAGE_CSV = COVERAGE_CSV
b.VALIDATION_JSON = VALIDATION_JSON

T = b.T


def draw_parallel_dense_flow(p: b.Page, spec: b.ModelSpec, *, x0: float = 20, y0: float = 135, label_prefix: str = 'GPT-NeoX/Pythia') -> None:
    inp = p.op('X', f'[T={T}, H={spec.H}]', x0 + 330, y0, 'input', 100, 40)
    ln1 = b.layernorm(p, x0 + 90, y0 + 78, 'LayerNorm (attn)', 220)
    ln2 = b.layernorm(p, x0 + 515, y0 + 78, 'LayerNorm (MLP)', 220)
    p.edge(inp, ln1, b.EDGE + 'exitX=0.35;exitY=1;entryX=0.5;entryY=0;')
    p.edge(inp, ln2, b.EDGE + 'exitX=0.65;exitY=1;entryX=0.5;entryY=0;')
    k = p.op('K Proj', 'X · Wk', x0 + 20, y0 + 175, 'blue', 110, 48)
    q = p.op('Q Proj', 'X · Wq', x0 + 305, y0 + 175, 'blue', 110, 48)
    v = p.op('V Proj', 'X · Wv', x0 + 590, y0 + 175, 'blue', 110, 48)
    p.edge(ln1, k, b.EDGE + 'exitX=0.2;exitY=1;entryX=0.5;entryY=0;')
    p.edge(ln1, q)
    p.edge(ln1, v, b.EDGE + 'exitX=0.8;exitY=1;entryX=0.5;entryY=0;')
    kr = p.op('RoPE', '(xe,xo) ← rotation(cosθ,sinθ)', x0 + 20, y0 + 258, 'purple', 145, 52)
    qr = p.op('RoPE', '(xe,xo) ← rotation(cosθ,sinθ)', x0 + 300, y0 + 258, 'purple', 145, 52)
    p.edge(k, kr)
    p.edge(q, qr)
    qk = p.op('Q × Kᵀ', 'batched head GEMM; causal mask', x0 + 290, y0 + 350, 'blue', 170, 52)
    sm = p.op('Softmax FP32', 'p_i = exp(s_i−m)/Σexp(s_j−m)', x0 + 295, y0 + 445, 'purple', 175, 58)
    pv = p.op('P × V', 'batched head GEMM', x0 + 530, y0 + 540, 'blue', 150, 50)
    o = p.op('O Proj', 'C · Wo', x0 + 530, y0 + 628, 'blue', 130, 48)
    p.edge(qr, qk)
    p.edge(kr, qk, b.EDGE + 'entryX=0;entryY=0.5;')
    p.edge(qk, sm)
    p.edge(sm, pv)
    p.edge(v, pv)
    p.edge(pv, o)
    # MLP branch in parallel from ln2.
    fc1 = p.op('fc1', 'X · W1 + b1', x0 + 520, y0 + 175, 'blue', 130, 48)
    gelu = p.op('GELU', '0.5u[1+erf(u/√2)]', x0 + 520, y0 + 258, 'purple', 130, 48)
    fc2 = p.op('fc2', 'A · W2 + b2', x0 + 520, y0 + 340, 'blue', 130, 48)
    p.edge(ln2, fc1)
    p.edge(fc1, gelu)
    p.edge(gelu, fc2)
    # Final residual: X + attn + mlp
    add1 = p.plus(x0 + 360, y0 + 725)
    add2 = p.plus(x0 + 515, y0 + 725)
    out = p.op('Block output', None, x0 + 430, y0 + 780, 'output', 140, 40)
    p.edge(o, add1, b.EDGE + 'entryX=0.5;entryY=0;')
    b.residual_edge(p, inp, add1, x0 + 5)
    p.edge(add1, add2, b.EDGE + 'exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
    p.edge(fc2, add2, b.EDGE + 'entryX=0.5;entryY=0;')
    p.edge(add2, out)
    p.vertex(f'<b>{html.escape(label_prefix)} topology</b><br>Parallel residual: Y = X + Attention(LN₁(X)) + MLP(LN₂(X))', x0 + 30, y0 + 860, 730, 56, b.NOTE_STYLE)


def overview_page(rows: list[dict]) -> b.Page:
    p = b.Page('00_覆盖口径与结构索引', 3200, 2300, None)
    b.header(p, 'Open-weight LLM Block Architecture Atlas — full snapshot families',
             'Source sample: current Hugging Face text-generation repositories sorted by displayed downloads; top 90 repositories from the 2026-08-25 snapshot. This revised atlas now draws every architecture family present in the snapshot.')
    p.vertex('<b>Coverage rule</b><br>This file draws all 25 architecture families that appear in the preserved 90-repository snapshot, including the long-tail families beyond the strict 90% coverage cutoff. Downloads are used only as a reproducible coverage proxy, not as unique-user or deployed-token market share.', 25, 130, 980, 96, b.NOTE_STYLE)
    x, y, rowh = 25, 250, 54
    headers = ['Rank', 'Architecture family', 'Downloads', 'Share', 'Cumulative', 'Atlas pages']
    widths = [70, 420, 120, 100, 120, 1040]
    cx = x
    for h, w in zip(headers, widths):
        p.vertex(f'<b>{h}</b>', cx, y, w, 32, 'rounded=0;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=10;')
        cx += w
    page_map = {
        'Qwen2/2.5 dense': '01',
        'Qwen3 dense': '02',
        'Llama/Yi/SmolLM dense': '03',
        'Qwen3 MoE': '04',
        'Qwen3.5/3.6 hybrid dense': '05A–05B',
        'Qwen3.5/3.6 hybrid MoE': '06–07',
        'GPT-2 dense': '08',
        'OPT dense': '09',
        'GPT-OSS MoE': '10A–10B',
        'Gemma4 dense': '11A–11B',
        'GLM DSA MoE': '12',
        'DeepSeek V4 hybrid MoE': '13A–13C',
        'Gemma3 dense': '14A–14B',
        'DeepSeek V3/R1 MLA MoE': '15',
        'GPT-NeoX/Pythia dense': '16',
        'Gemma4 MoE': '17A–17B',
        'Kimi K3 hybrid MoE': '18',
        'Granite4 hybrid': '19',
        'Qwen1 dense': '20',
        'Phi-2 dense': '21',
        'BLOOM dense': '22',
        'OpenELM dense': '23',
        'PowerMoE': '24',
        'Nemotron3 hybrid MoE': '25',
        'Mistral dense': '26',
    }
    for i, r in enumerate(rows):
        yy = y + 32 + i * rowh
        fill = '#d5e8d4' if r['included_90pct'] else '#ffffff'
        vals = [r['rank'], r['family'], f"{r['downloads_m']:.2f}M", f"{r['share_pct']:.2f}%", f"{r['cumulative_pct']:.2f}%", page_map.get(r['family'], '')]
        cx = x
        for j, (val, w) in enumerate(zip(vals, widths)):
            p.vertex(str(val), cx, yy, w, rowh,
                     f'rounded=0;whiteSpace=wrap;html=1;fillColor={fill};strokeColor=#b3b3b3;fontSize=9;align={"left" if j in (1,5) else "center"};spacing=4;')
            cx += w
    p.vertex('<b>Color grammar</b><br>Blue: large matrix multiplication/projection suited to MAC arrays. Purple: normalization, nonlinear, elementwise, routing/top-k, reshape, mask, state update and other non-matrix operators. Green: cache/state. Red: weights. Orange/yellow: input/residual.', 2200, 250, 930, 120, b.NOTE_STYLE)
    p.vertex('<b>Footprint grammar</b><br>All atlas pages use 1 px² = 4 KiB. Weight rectangles preserve byte volume and matrix aspect ratio. MoE pages expand expert bodies instead of hiding them behind one opaque node. Logical activations are named-tensor volumes, not a peak-liveness allocator result.', 2200, 390, 930, 130, b.NOTE_STYLE)
    p.vertex('<b>Revision focus</b><br>This revision adds the long-tail families from the snapshot and keeps the guardrails requested by the user: reduced line crossings, no overlapping red weight rectangles, and explicit expansion of complex operators rather than placeholder “black-box” blocks.', 2200, 540, 930, 120, b.NOTE_STYLE)
    return p


def build_pages() -> list[b.Page]:
    pages = b.build_pages()[1:]  # drop old overview page
    specs = {
        'neox': b.ModelSpec('neox', 'GPT-NeoX / Pythia', 'GPT-NeoX/Pythia dense', 768, 3072, 12, 12, 64, norm='LayerNorm', mlp='GELU', equivalent='Pythia and GPT-NeoX representative family page. Same topology also describes GPT-NeoX derivatives that keep LayerNorm + causal RoPE attention + GELU FFN with parallel residual.'),
        'gemma4moe_s': b.ModelSpec('gemma4moe_s', 'Gemma 4 Sliding Attention MoE', 'Gemma4 MoE', 5376, 0, 32, 16, 256, attention='sliding', window=1024, norm='RMSNorm', mlp='GeGLU', qk_norm=True, E=64, K=8, expert_I=4096, shared_experts=1, equivalent='Representative Gemma 4 MoE family page for Gemma-4-26B-A4B and OTel-LLM-E4B-IT. Sliding block.', note='K=V'),
        'gemma4moe_f': b.ModelSpec('gemma4moe_f', 'Gemma 4 Full Attention MoE', 'Gemma4 MoE', 5376, 0, 32, 4, 512, attention='full', norm='RMSNorm', mlp='GeGLU', qk_norm=True, partial_rope=.25, E=64, K=8, expert_I=4096, shared_experts=1, equivalent='Representative Gemma 4 MoE family page for Gemma-4-26B-A4B and OTel-LLM-E4B-IT. Global/full block.', note='K=V'),
        'kimi': b.ModelSpec('kimi', 'Kimi K3 MLA + MoE', 'Kimi K3 hybrid MoE', 7168, 18432, 128, 128, 192, norm='RMSNorm', mlp='SwiGLU', E=128, K=8, expert_I=2048, shared_experts=1, equivalent='Representative long-tail Kimi K3 / DSpark family page. Drawn as an MLA + sparse MoE block, the closest public open-weight topology class in the snapshot.'),
        'granite': b.ModelSpec('granite', 'Granite 4 hybrid dense', 'Granite4 hybrid', 4096, 14336, 32, 8, 128, attention='sliding', window=4096, norm='RMSNorm', mlp='SwiGLU', equivalent='Representative Granite 4 family page. Uses grouped-query sliding attention plus SwiGLU at this abstraction level.'),
        'qwen1': b.ModelSpec('qwen1', 'Qwen1 dense', 'Qwen1 dense', 8192, 22016, 64, 8, 128, norm='RMSNorm', mlp='SwiGLU', bias=True, equivalent='Qwen-72B and related Qwen1 checkpoints share the earlier dense RoPE + GQA/MQA + SwiGLU decoder-block topology.'),
        'phi2': b.ModelSpec('phi2', 'Phi-2 dense', 'Phi-2 dense', 2560, 10240, 32, 32, 80, norm='LayerNorm', mlp='GELU', equivalent='Representative Phi-2 family page. Drawn with LayerNorm, causal attention and GELU FFN under the same parallel-residual pattern as GPT-NeoX-like blocks.'),
        'bloom': b.ModelSpec('bloom', 'BLOOM dense', 'BLOOM dense', 1024, 4096, 16, 16, 64, norm='LayerNorm', mlp='GELU', equivalent='BLOOM/BLOOMZ representative page. Uses the Megatron-style dense decoder block with combined QKV projection, causal self-attention and GELU FFN.'),
        'openelm': b.ModelSpec('openelm', 'OpenELM dense', 'OpenELM dense', 2048, 5632, 16, 4, 128, norm='RMSNorm', mlp='SwiGLU', equivalent='Representative OpenELM family page. Uses compact grouped-query attention plus SwiGLU.'),
        'powermoe': b.ModelSpec('powermoe', 'PowerMoE', 'PowerMoE', 2048, 0, 32, 8, 64, norm='RMSNorm', mlp='SwiGLU', E=64, K=4, expert_I=1408, shared_experts=0, equivalent='Representative IBM PowerMoE family page. Standard self-attention followed by sparse top-k MoE.'),
        'nemotron': b.ModelSpec('nemotron', 'Nemotron 3 hybrid MoE', 'Nemotron3 hybrid MoE', 6144, 0, 48, 8, 128, norm='RMSNorm', mlp='SwiGLU', E=128, K=8, expert_I=1536, shared_experts=1, equivalent='Representative NVIDIA Nemotron3 hybrid MoE family page. Drawn with long-context attention plus sparse MoE at the same abstraction level as other atlas pages.'),
        'mistral': b.ModelSpec('mistral', 'Mistral dense', 'Mistral dense', 4096, 14336, 32, 8, 128, attention='sliding', window=4096, norm='RMSNorm', mlp='SwiGLU', equivalent='Mistral-7B and instruct derivatives share sliding-window grouped-query attention plus SwiGLU.'),
    }

    p = b.Page('16_GPTNeoX_Pythia_Dense', 4200, 2500, specs['neox'])
    b.header(p, 'GPT-NeoX / Pythia — parallel-residual dense decoder block', 'Representative: Pythia-160M, H=768, I=3072, 12 RoPE attention heads, GELU FFN, LayerNorm parallel residual', p.spec.equivalent)
    draw_parallel_dense_flow(p, p.spec)
    b.standard_footprint(p, p.spec)
    pages.append(p)

    p = b.Page('17A_Gemma4_MoE_Sliding', 6100, 6000, specs['gemma4moe_s'])
    b.header(p, 'Gemma 4 — sliding attention + sparse MoE block', 'Representative: Gemma-4-26B-A4B-style sparse block, H=5376, Q=32, KV=16, d=256, top-8 MoE', p.spec.equivalent)
    b.draw_standard_attention_flow(p, p.spec, moe=True, k_eq_v=True)
    b.standard_footprint(p, p.spec, moe=True, k_eq_v=True)
    pages.append(p)

    p = b.Page('17B_Gemma4_MoE_Full', 6100, 6000, specs['gemma4moe_f'])
    b.header(p, 'Gemma 4 — full attention + sparse MoE block', 'Representative: Gemma-4-26B-A4B-style global sparse block, H=5376, Q=32, KV=4, d=512, top-8 MoE', p.spec.equivalent)
    b.draw_standard_attention_flow(p, p.spec, moe=True, k_eq_v=True)
    b.standard_footprint(p, p.spec, moe=True, k_eq_v=True)
    pages.append(p)

    p = b.Page('18_KimiK3_Hybrid_MLA_MoE', 7600, 7000, specs['kimi'])
    b.header(p, 'Kimi K3 — representative MLA + sparse MoE block', 'Long-tail family page: representative MLA compression/expansion + causal attention + top-8 sparse MoE', p.spec.equivalent)
    b.draw_deepseek_v3_flow(p, p.spec)
    b.deepseek_v3_footprint(p, p.spec)
    pages.append(p)

    p = b.Page('19_Granite4_Hybrid_Dense', 4500, 3000, specs['granite'])
    b.header(p, 'Granite 4 — representative hybrid dense block', 'Representative long-tail family page: grouped-query sliding attention + SwiGLU', p.spec.equivalent)
    b.draw_standard_attention_flow(p, p.spec)
    b.standard_footprint(p, p.spec)
    pages.append(p)

    p = b.Page('20_Qwen1_Dense', 4700, 3200, specs['qwen1'])
    b.header(p, 'Qwen1 — dense decoder block', 'Representative: Qwen-72B, dense RoPE attention + SwiGLU, older Qwen-family topology', p.spec.equivalent)
    b.draw_standard_attention_flow(p, p.spec)
    b.standard_footprint(p, p.spec)
    pages.append(p)

    p = b.Page('21_Phi2_Dense', 4500, 2600, specs['phi2'])
    b.header(p, 'Phi-2 — representative dense decoder block', 'Representative: Phi-2, LayerNorm + causal attention + GELU FFN, parallel residual family', p.spec.equivalent)
    draw_parallel_dense_flow(p, p.spec, label_prefix='Phi-2')
    b.standard_footprint(p, p.spec)
    pages.append(p)

    p = b.Page('22_BLOOM_Dense', 4100, 2550, specs['bloom'])
    b.header(p, 'BLOOM — dense decoder block', 'Representative: bloomz-560m, combined QKV projection + causal self-attention + GELU FFN (Megatron-style)', p.spec.equivalent)
    b.draw_gpt2_opt_flow(p, p.spec, opt=False)
    b.gpt2_opt_footprint(p, p.spec, opt=False)
    pages.append(p)

    p = b.Page('23_OpenELM_Dense', 4200, 2850, specs['openelm'])
    b.header(p, 'OpenELM — dense decoder block', 'Representative: OpenELM-1.1B, grouped-query attention + RoPE + SwiGLU', p.spec.equivalent)
    b.draw_standard_attention_flow(p, p.spec)
    b.standard_footprint(p, p.spec)
    pages.append(p)

    p = b.Page('24_PowerMoE', 5200, 4800, specs['powermoe'])
    b.header(p, 'PowerMoE — sparse MoE decoder block', 'Representative: PowerMoE-3B, standard attention + top-4 sparse expert FFN', p.spec.equivalent)
    b.draw_standard_attention_flow(p, p.spec, moe=True)
    b.standard_footprint(p, p.spec, moe=True)
    pages.append(p)

    p = b.Page('25_Nemotron3_Hybrid_MoE', 5400, 5000, specs['nemotron'])
    b.header(p, 'Nemotron 3 — representative hybrid sparse MoE block', 'Representative long-tail family page: long-context attention + top-8 sparse MoE', p.spec.equivalent)
    b.draw_standard_attention_flow(p, p.spec, moe=True)
    b.standard_footprint(p, p.spec, moe=True)
    pages.append(p)

    p = b.Page('26_Mistral_Dense', 4500, 3000, specs['mistral'])
    b.header(p, 'Mistral — sliding-window dense decoder block', 'Representative: Mistral-7B, sliding-window grouped-query attention + SwiGLU', p.spec.equivalent)
    b.draw_standard_attention_flow(p, p.spec)
    b.standard_footprint(p, p.spec)
    pages.append(p)

    rows = b.family_coverage()
    return [overview_page(rows)] + pages


def semantic_validate(path: Path) -> dict:
    root = b.ET.parse(path).getroot()
    values, cells = [], []
    import re
    for cell in root.iter('mxCell'):
        raw = html.unescape(cell.get('value', ''))
        text = re.sub(r'<[^>]+>', ' ', raw)
        text = ' '.join(text.replace('&#10;', ' ').split())
        if text:
            values.append(text)
        cells.append((text, cell.get('style', '')))
    joined = '\n'.join(values)

    def styles(label: str):
        return [style for text, style in cells if label in text]

    def any_style(label: str, color: str) -> bool:
        return any(color in style for style in styles(label))

    actual_pages = {d.get('name', '') for d in root.findall('diagram')}
    expected_pages = {p.name for p in build_pages()}
    blue, purple = '#dae8fc', '#e1d5e7'
    checks = {
        'expected_pages_present': actual_pages == expected_pages,
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
        'long_tail_pages_present': all(label in actual_pages for label in ('16_GPTNeoX_Pythia_Dense', '17A_Gemma4_MoE_Sliding', '18_KimiK3_Hybrid_MLA_MoE', '26_Mistral_Dense')),
    }
    return {'checks': checks, 'all_pass': all(checks.values()), 'actual_page_names': sorted(actual_pages)}


def write_sources() -> None:
    text = '''# 来源、覆盖范围与结构合并原则

## 快照范围

- 快照日期：2026-08-25。
- 下载样本：Hugging Face `text-generation` 分类、按 displayed downloads 降序的前 90 个仓库。
- 样本总下载量：335.49M displayed downloads。
- 本修订图集：把该快照中的 25 个架构家族全部绘制到 draw.io 图集中，包括 90% 阈值外的长尾家族。
- “开放 LLM”在本交付中表示公开可下载权重或公开模型仓库，不等同于 OSI 定义的开源软件许可。

下载数会包含自动化测试、依赖缓存、量化副本、微调副本和重复拉取，因此这里只把它用作可复算的架构覆盖代理，不把它解释为唯一用户数、线上 token 份额或商业市场份额。

## 结构合并原则

只有以下条件同时成立时才合并到同一页：

1. 子层顺序和 residual 拓扑相同；
2. Attention/GDN/MLA/DSA 等状态语义相同；
3. Norm、激活、MoE 路由和专家数据流相同；
4. 差异主要是 H、I、head 数、expert 数、层数或量化位宽。

Sliding/Full Attention、GDN/Full Attention、Dense/MoE、MLA/DSA/HCA/CSA 等不是单纯维度差异，均分开绘制。

## 长尾家族说明

- 对 GPT-NeoX/Pythia、Phi-2、BLOOM、Mistral、OpenELM 等长尾 dense 家族，图中采用公开实现中最稳定的 block 拓扑。
- 对 Gemma 4 MoE、PowerMoE 等长尾 MoE 家族，保留 Router、Top-k、Expert body 和 Weighted Reduce 的展开表达。
- 对 Kimi K3、Nemotron 3、Granite 4 这类公开资料相对分散的长尾家族，图中使用与其公开家族描述最接近的代表 block 拓扑，并在页首明确标注为 representative family page，而不把它们伪装成官方逐运算 whitepaper 图。
'''
    SOURCES.write_text(text, encoding='utf-8')


def write_readme(rows: list[dict]) -> None:
    total = sum(v for _, v, _ in b.TOP90)
    page_rows = [
        ('01', 'Qwen2/Qwen2.5 Dense', 'Qwen2.5-1.5B', 'Qwen2、Qwen2.5 dense/coder/instruct/量化变体'),
        ('02', 'Qwen3 Dense', 'Qwen3-1.7B', 'Qwen3 0.6B–32B dense、coder/instruct/AWQ/FP8'),
        ('03', 'Llama/Yi/SmolLM Dense', 'Llama-3.2-1B', 'Llama 3/3.1/3.2、TinyLlama、Yi-1.5、SmolLM2'),
        ('04', 'Qwen3 MoE', 'Qwen3-30B-A3B', 'Qwen3 MoE/Coder/VL 文本 Block 及量化变体'),
        ('05A/05B', 'Qwen3.5/3.6 Dense Hybrid', 'Qwen3.5-2B', 'Ornith-9B、Bonsai-27B、Qwen3.6/3.8 dense'),
        ('06/07', 'Qwen3.5/3.6 MoE Hybrid', 'Qwen3.5-35B-A3B', 'Qwen3.6-35B-A3B、Ornith-35B、Coder-Next'),
        ('08', 'GPT-2 Dense', 'GPT-2 small', 'GPT-2 各尺寸、DistilGPT2、tiny-gpt2'),
        ('09', 'OPT Dense', 'OPT-125M', 'OPT 125M–175B'),
        ('10A/10B', 'GPT-OSS MoE', 'gpt-oss-20b', 'gpt-oss-20b/120b'),
        ('11A/11B', 'Gemma 4 Dense', 'Gemma-4-31B', 'OTel 27B/31B 等衍生'),
        ('12', 'GLM DSA MoE', 'GLM-5.2', 'GLM-5.2、GLM-4.7-Flash 及 FP8/NVFP4 变体'),
        ('13A/13B/13C', 'DeepSeek V4 Hybrid MoE', 'DeepSeek-V4-Flash', 'V4 Flash/0731/GGUF'),
        ('14A/14B', 'Gemma 3 Dense', 'Gemma-3-1B', 'Gemma-3 270M/1B/4B/12B/27B'),
        ('15', 'DeepSeek V3/R1 MLA MoE', 'DeepSeek-R1', 'DeepSeek V3、V3.2、R1'),
        ('16', 'GPT-NeoX/Pythia Dense', 'Pythia-160M', 'Pythia / GPT-NeoX dense family'),
        ('17A/17B', 'Gemma 4 MoE', 'Gemma-4-26B-A4B', 'Gemma 4 sparse-FFN 家族'),
        ('18', 'Kimi K3 Hybrid MLA + MoE', 'Kimi-K3-DSpark representative', 'Kimi K3 长尾家族代表页'),
        ('19', 'Granite 4 Hybrid Dense', 'granite-4.1-8b representative', 'Granite 4 长尾家族代表页'),
        ('20', 'Qwen1 Dense', 'Qwen-72B', 'Qwen1 dense 家族'),
        ('21', 'Phi-2 Dense', 'Phi-2', 'Phi-2 家族代表页'),
        ('22', 'BLOOM Dense', 'bloomz-560m', 'BLOOM / BLOOMZ 家族'),
        ('23', 'OpenELM Dense', 'OpenELM-1_1B-Instruct', 'OpenELM 家族'),
        ('24', 'PowerMoE', 'PowerMoE-3b representative', 'PowerMoE 家族'),
        ('25', 'Nemotron3 Hybrid MoE', 'NVIDIA-Nemotron-3-Super-120B-A12B representative', 'Nemotron3 长尾家族代表页'),
        ('26', 'Mistral Dense', 'Mistral-7B-Instruct-v0.2', 'Mistral dense 家族'),
    ]
    lines = [
        '# 开放权重 LLM 单 Block 架构图集（完整快照家族版，B=1，T=1024）', '',
        '## 交付文件', '',
        '- 主图集：`open_llm_block_atlas_all_families_1024.drawio`。',
        '- 统一跨模型比例：`1 px² = 4 KiB`。',
        '- 独立 Qwen 精细修订文件保留原参考图比例：`1 px² = 100 bytes`。',
        '- 该修订版在原 90% 覆盖图集基础上，把快照中的长尾家族也补齐到 draw.io 主文件中。', '',
        '## 绘图规则', '',
        '- 蓝色只表示可由大量 MAC/GEMM/GEMV 支撑的矩阵乘操作。',
        '- 紫色表示 Norm、非线性、逐元素、路由、Top-k、reshape、mask、状态更新等非矩阵操作。',
        '- 绿色表示 cache/SRAM/recurrent state；红色表示权重；黄色/橙色表示 residual/input。',
        '- 红色权重矩形面积等于权重字节数，长宽比保留矩阵真实两维方向。',
        '- GDN、MoE、DSA、MLA 等复杂 block 均按内部计算过程展开，不保留模糊黑箱节点。',
        '- 对新增长尾家族，额外检查页面边界、红色权重矩形重叠、`sumEllipse` 禁用和 visible label 中禁止残留 `1014`。', '',
        '## 覆盖率', '',
        f'- 快照总下载量：{total:.2f}M displayed downloads。',
        '- 本图集覆盖：快照中的 25 个架构家族，覆盖率 100%。',
        '- 其中前 13 个家族已经达到严格 90% 阈值；这次新增的是其余长尾家族页面。', '',
        '## 页面与代表配置', '',
        '| 页码 | 结构家族 | 代表配置 | 同构/说明 |',
        '|---|---|---|---|',
    ]
    lines.extend(f'| {idx} | {family} | {rep} | {equiv} |' for idx, family, rep, equiv in page_rows)
    lines += ['', '## 长尾家族列表（本次新增）', '',
              'GPT-NeoX/Pythia、Gemma 4 MoE、Kimi K3、Granite 4、Qwen1、Phi-2、BLOOM、OpenELM、PowerMoE、Nemotron3、Mistral 均已加入主图集。', '',
              '## 自动校验', '',
              '- draw.io XML 可解析，所有 vertex 均位于页面边界内。',
              '- 所有红色权重矩形执行几何重叠检查。',
              '- 禁止可见标签残留 `1014`，禁止 `shape=sumEllipse`。',
              '- 对 Router、Top-k、Dispatch、Expert GEMM、Weighted Reduce、GDN 三分支和 Chunk Delta Rule 执行语义/颜色门禁。',
              '- `top90_hf_text_generation_downloads_2026-08-25.csv` 保留原始仓库快照；`architecture_family_coverage.csv` 保留结构映射、份额和累计份额。', '']
    README.write_text('\n'.join(lines), encoding='utf-8')


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def package() -> None:
    files = [
        OUT,
        PACKAGE_DIR / 'drawio' / 'qwen3_qwen35_blocks_1024_prefill_v3.drawio',
        TOP90_CSV,
        COVERAGE_CSV,
        README,
        SOURCES,
        VALIDATION_JSON,
        Path(__file__),
        BASE_PATH,
    ]
    SUMS.write_text('\n'.join(f'{sha256(fp)}  {fp.name}' for fp in files if fp.exists()) + '\n', encoding='utf-8')
    files.append(SUMS)
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for fp in files:
            if fp.exists():
                zf.write(fp, arcname=fp.name)


def main() -> None:
    # Preserve original snapshot CSVs
    with TOP90_CSV.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['rank', 'repository', 'downloads_m', 'mapped_architecture_family'])
        for i, (repo, v, fam) in enumerate(b.TOP90, 1):
            w.writerow([i, repo, v, fam])
    rows = b.family_coverage()
    with COVERAGE_CSV.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    pages = build_pages()
    b.write_drawio(pages)
    val = b.validate(OUT)
    val['semantic_validation'] = semantic_validate(OUT)
    write_sources()
    write_readme(rows)
    VALIDATION_JSON.write_text(json.dumps(val, ensure_ascii=False, indent=2), encoding='utf-8')
    if not val['bounds_ok']:
        raise SystemExit('out-of-bounds elements detected')
    if val['red_weight_overlap_pairs']:
        raise SystemExit(f'weight overlap detected: {val["red_weight_overlap_pairs"][:10]}')
    if not val['semantic_validation']['all_pass']:
        failed = [k for k, ok in val['semantic_validation']['checks'].items() if not ok]
        raise SystemExit(f'semantic validation failed: {failed}')
    package()
    print(OUT)
    print(ZIP)

if __name__ == '__main__':
    main()

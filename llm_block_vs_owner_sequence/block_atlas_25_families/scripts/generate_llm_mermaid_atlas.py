#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import html
import json
import math
import re
import shutil
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

PACKAGE_DIR = Path(__file__).resolve().parent.parent
SRC_DRAWIO = PACKAGE_DIR / 'drawio' / 'open_llm_block_atlas_all_families_1024.drawio'
SRC_COVERAGE = PACKAGE_DIR / 'metadata' / 'architecture_family_coverage.csv'
OUT_DIR = PACKAGE_DIR / 'generated' / 'mermaid_atlas'
MMD_DIR = OUT_DIR / 'mmd'
README = OUT_DIR / 'README_CN.md'
MANIFEST = OUT_DIR / 'manifest.csv'
VALIDATION = OUT_DIR / 'validation.json'
COMBINED_MD = OUT_DIR / 'all_25_families_mermaid.md'
ZIP_PATH = OUT_DIR / 'llm_block_mermaid_25families_1024_package.zip'
SHA_FILE = OUT_DIR / 'SHA256SUMS.txt'

FAMILIES: list[dict] = [
    {'rank': 1, 'slug': 'qwen2_qwen2_5_dense', 'title': 'Qwen2 / Qwen2.5 Dense', 'pages': ['01_Qwen2_Qwen2.5_Dense']},
    {'rank': 2, 'slug': 'qwen3_dense', 'title': 'Qwen3 Dense', 'pages': ['02_Qwen3_Dense']},
    {'rank': 3, 'slug': 'llama_yi_smollm_dense', 'title': 'Llama / Yi / SmolLM Dense', 'pages': ['03_Llama_Yi_SmolLM_Dense']},
    {'rank': 4, 'slug': 'qwen3_5_qwen3_6_hybrid_moe', 'title': 'Qwen3.5 / Qwen3.6 Hybrid MoE', 'pages': ['06_Qwen3.5_MoE_GDN', '07_Qwen3.5_MoE_FullAttention']},
    {'rank': 5, 'slug': 'qwen3_moe', 'title': 'Qwen3 MoE', 'pages': ['04_Qwen3_MoE']},
    {'rank': 6, 'slug': 'gpt2_dense', 'title': 'GPT-2 Dense', 'pages': ['08_GPT2_Dense']},
    {'rank': 7, 'slug': 'opt_dense', 'title': 'OPT Dense', 'pages': ['09_OPT_Dense']},
    {'rank': 8, 'slug': 'qwen3_5_qwen3_6_hybrid_dense', 'title': 'Qwen3.5 / Qwen3.6 Hybrid Dense', 'pages': ['05A_Qwen3.5_Dense_GDN', '05B_Qwen3.5_Dense_FullAttention']},
    {'rank': 9, 'slug': 'gpt_oss_moe', 'title': 'GPT-OSS MoE', 'pages': ['10A_GPT_OSS_Sliding', '10B_GPT_OSS_Full']},
    {'rank': 10, 'slug': 'gemma4_dense', 'title': 'Gemma 4 Dense', 'pages': ['11A_Gemma4_Sliding', '11B_Gemma4_Full']},
    {'rank': 11, 'slug': 'glm_dsa_moe', 'title': 'GLM DSA MoE', 'pages': ['12_GLM5.2_DSA_MoE']},
    {'rank': 12, 'slug': 'deepseek_v4_hybrid_moe', 'title': 'DeepSeek V4 Hybrid MoE', 'pages': ['13A_DeepSeekV4_Slidingonly', '13B_DeepSeekV4_CSA', '13C_DeepSeekV4_HCA']},
    {'rank': 13, 'slug': 'gemma3_dense', 'title': 'Gemma 3 Dense', 'pages': ['14A_Gemma3_Sliding', '14B_Gemma3_Full']},
    {'rank': 14, 'slug': 'deepseek_v3_r1_mla_moe', 'title': 'DeepSeek V3 / R1 MLA MoE', 'pages': ['15_DeepSeekV3_R1_MLA_MoE']},
    {'rank': 15, 'slug': 'gpt_neox_pythia_dense', 'title': 'GPT-NeoX / Pythia Dense', 'pages': ['16_GPTNeoX_Pythia_Dense']},
    {'rank': 16, 'slug': 'gemma4_moe', 'title': 'Gemma 4 MoE', 'pages': ['17A_Gemma4_MoE_Sliding', '17B_Gemma4_MoE_Full']},
    {'rank': 17, 'slug': 'kimi_k3_hybrid_moe', 'title': 'Kimi K3 Hybrid MoE', 'pages': ['18_KimiK3_Hybrid_MLA_MoE']},
    {'rank': 18, 'slug': 'granite4_hybrid', 'title': 'Granite 4 Hybrid', 'pages': ['19_Granite4_Hybrid_Dense']},
    {'rank': 19, 'slug': 'qwen1_dense', 'title': 'Qwen1 Dense', 'pages': ['20_Qwen1_Dense']},
    {'rank': 20, 'slug': 'phi2_dense', 'title': 'Phi-2 Dense', 'pages': ['21_Phi2_Dense']},
    {'rank': 21, 'slug': 'bloom_dense', 'title': 'BLOOM Dense', 'pages': ['22_BLOOM_Dense']},
    {'rank': 22, 'slug': 'openelm_dense', 'title': 'OpenELM Dense', 'pages': ['23_OpenELM_Dense']},
    {'rank': 23, 'slug': 'powermoe', 'title': 'PowerMoE', 'pages': ['24_PowerMoE']},
    {'rank': 24, 'slug': 'nemotron3_hybrid_moe', 'title': 'Nemotron 3 Hybrid MoE', 'pages': ['25_Nemotron3_Hybrid_MoE']},
    {'rank': 25, 'slug': 'mistral_dense', 'title': 'Mistral Dense', 'pages': ['26_Mistral_Dense']},
]

VARIANT_LABELS = {
    '01_Qwen2_Qwen2.5_Dense': 'Dense decoder block',
    '02_Qwen3_Dense': 'Dense decoder block with Q/K head RMSNorm',
    '03_Llama_Yi_SmolLM_Dense': 'Pre-norm GQA / SwiGLU block',
    '04_Qwen3_MoE': 'Full attention + routed MoE block',
    '05A_Qwen3.5_Dense_GDN': 'GDN + dense SwiGLU block',
    '05B_Qwen3.5_Dense_FullAttention': 'Gated full-attention + dense SwiGLU block',
    '06_Qwen3.5_MoE_GDN': 'GDN + routed/shared MoE block',
    '07_Qwen3.5_MoE_FullAttention': 'Gated full-attention + routed/shared MoE block',
    '08_GPT2_Dense': 'GPT-2 pre-norm dense block',
    '09_OPT_Dense': 'OPT pre-norm dense block',
    '10A_GPT_OSS_Sliding': 'Sliding-attention + top-4 MoE block',
    '10B_GPT_OSS_Full': 'Full-attention + top-4 MoE block',
    '11A_Gemma4_Sliding': 'Sliding-attention dense block',
    '11B_Gemma4_Full': 'Full-attention dense block',
    '12_GLM5.2_DSA_MoE': 'DSA / MLA + routed/shared MoE block',
    '13A_DeepSeekV4_Slidingonly': 'Sliding-only + mHC + MoE block',
    '13B_DeepSeekV4_CSA': 'Compressed Sparse Attention + mHC + MoE block',
    '13C_DeepSeekV4_HCA': 'Hierarchical Compressed Attention + mHC + MoE block',
    '14A_Gemma3_Sliding': 'Sliding-attention dense block',
    '14B_Gemma3_Full': 'Full-attention dense block',
    '15_DeepSeekV3_R1_MLA_MoE': 'MLA + routed/shared MoE block',
    '16_GPTNeoX_Pythia_Dense': 'Parallel-residual dense block',
    '17A_Gemma4_MoE_Sliding': 'Sliding-attention + sparse MoE block',
    '17B_Gemma4_MoE_Full': 'Full-attention + sparse MoE block',
    '18_KimiK3_Hybrid_MLA_MoE': 'Representative MLA + sparse MoE block',
    '19_Granite4_Hybrid_Dense': 'Representative grouped-query hybrid dense block',
    '20_Qwen1_Dense': 'Earlier Qwen dense decoder block',
    '21_Phi2_Dense': 'Parallel-residual dense block',
    '22_BLOOM_Dense': 'Megatron-style dense decoder block',
    '23_OpenELM_Dense': 'Compact GQA + SwiGLU block',
    '24_PowerMoE': 'Attention + sparse MoE block',
    '25_Nemotron3_Hybrid_MoE': 'Representative long-context sparse MoE block',
    '26_Mistral_Dense': 'Sliding-window GQA + SwiGLU block',
}

INIT_LINE = "%%{init: {\"flowchart\": {\"defaultRenderer\": \"elk\", \"curve\": \"stepAfter\", \"htmlLabels\": true, \"nodeSpacing\": 36, \"rankSpacing\": 48, \"useMaxWidth\": false}, \"theme\": \"base\"}}%%"

CLASS_DEFS = [
    'classDef mac fill:#dae8fc,stroke:#6c8ebf,stroke-width:1.5px,color:#1f1f1f;',
    'classDef other fill:#e1d5e7,stroke:#9673a6,stroke-width:1.5px,color:#1f1f1f;',
    'classDef state fill:#d5e8d4,stroke:#82b366,stroke-width:1.5px,color:#1f1f1f;',
    'classDef output fill:#d5e8d4,stroke:#82b366,stroke-width:1.5px,color:#1f1f1f;',
    'classDef input fill:#fff2cc,stroke:#d6b656,stroke-width:1.5px,color:#1f1f1f;',
    'classDef input2 fill:#ffe6cc,stroke:#d79b00,stroke-width:1.5px,color:#1f1f1f;',
    'classDef weight fill:#f8cecc,stroke:#b85450,stroke-width:1.5px,color:#1f1f1f;',
    'classDef plus fill:#ffffff,stroke:#333333,stroke-width:2px,color:#111111,font-weight:bold;',
    'classDef note fill:#ffffff,stroke:#b3b3b3,stroke-width:1px,stroke-dasharray:5 3,color:#555555;',
    'classDef neutral fill:#ffffff,stroke:#777777,stroke-width:1.2px,color:#333333;',
]


@dataclass
class Cell:
    id: str
    value: str
    style: str
    x: float
    y: float
    w: float
    h: float
    source: str | None = None
    target: str | None = None
    is_vertex: bool = False
    is_edge: bool = False

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2


@dataclass
class Group:
    cell: Cell
    children: list['Group'] = field(default_factory=list)
    nodes: list[Cell] = field(default_factory=list)
    parent: 'Group | None' = None


def geom(cell: ET.Element) -> tuple[float, float, float, float]:
    g = cell.find('mxGeometry')
    if g is None:
        return 0.0, 0.0, 0.0, 0.0
    return tuple(float(g.get(k, '0')) for k in ('x', 'y', 'width', 'height'))


def parse_page(diagram: ET.Element) -> tuple[dict[str, Cell], list[Cell]]:
    graph_root = diagram.find('mxGraphModel/root')
    if graph_root is None:
        raise ValueError(f'Missing graph root: {diagram.get("name")}')
    cells: dict[str, Cell] = {}
    edges: list[Cell] = []
    for c in graph_root.findall('mxCell'):
        x, y, w, h = geom(c)
        cc = Cell(
            id=c.get('id', ''), value=c.get('value', ''), style=c.get('style', ''),
            x=x, y=y, w=w, h=h, source=c.get('source'), target=c.get('target'),
            is_vertex=c.get('vertex') == '1', is_edge=c.get('edge') == '1'
        )
        cells[cc.id] = cc
        if cc.is_edge:
            edges.append(cc)
    return cells, edges


def contains(outer: Cell, inner: Cell, pad: float = 1.0) -> bool:
    return (
        inner.cx >= outer.x - pad and inner.cx <= outer.x + outer.w + pad and
        inner.cy >= outer.y - pad and inner.cy <= outer.y + outer.h + pad
    )


def is_group(c: Cell) -> bool:
    return c.is_vertex and 'strokeColor=#999999' in c.style and 'dashed=1' in c.style


def is_note(c: Cell) -> bool:
    return c.is_vertex and 'strokeColor=#b3b3b3' in c.style and 'dashed=1' in c.style


def clean_plain(raw: str) -> str:
    s = raw.replace('&#10;', '\n')
    s = re.sub(r'(?i)<br\s*/?>', '\n', s)
    s = re.sub(r'(?i)</?(?:b|strong|i|em|font|span)(?:\s+[^>]*)?>', '', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = html.unescape(s)
    lines = [' '.join(line.split()) for line in s.replace('\r', '').split('\n')]
    lines = [line for line in lines if line]
    return '\n'.join(lines)


def mermaid_label(raw: str) -> str:
    plain = clean_plain(raw)
    if not plain:
        plain = ' '
    escaped_lines = []
    for line in plain.split('\n'):
        escaped = html.escape(line, quote=True)
        escaped_lines.append(escaped)
    return '<br/>'.join(escaped_lines)


def safe_comment(raw: str) -> str:
    return clean_plain(raw).replace('\n', ' | ').replace('%%', '% %')


def node_class(c: Cell) -> str:
    s = c.style
    if clean_plain(c.value).strip() == '+' and 'ellipse' in s:
        return 'plus'
    if 'shape=cylinder3' in s:
        return 'state'
    if '#dae8fc' in s:
        return 'mac'
    if '#e1d5e7' in s:
        return 'other'
    if '#d5e8d4' in s:
        return 'output'
    if '#fff2cc' in s:
        return 'input'
    if '#ffe6cc' in s:
        return 'input2'
    if '#f8cecc' in s:
        return 'weight'
    if is_note(c):
        return 'note'
    return 'neutral'


def node_syntax(node_id: str, c: Cell) -> str:
    label = mermaid_label(c.value)
    cls = node_class(c)
    if cls == 'plus':
        return f'{node_id}((+)):::{cls}'
    if cls == 'state':
        return f'{node_id}[("{label}")]:::{cls}'
    if cls == 'other':
        return f'{node_id}("{label}"):::{cls}'
    return f'{node_id}["{label}"]:::{cls}'


def group_direction(g: Cell) -> str:
    if g.w > g.h * 1.6:
        return 'LR'
    return 'TB'


def sanitize_id(s: str) -> str:
    s = re.sub(r'[^A-Za-z0-9_]', '_', s)
    if not s or not re.match(r'[A-Za-z_]', s):
        s = 'n_' + s
    return s


def extract_flow(diagram: ET.Element, page_index: int) -> dict:
    cells, edges = parse_page(diagram)
    connected: set[str] = set()
    for e in edges:
        if e.source:
            connected.add(e.source)
        if e.target:
            connected.add(e.target)

    flow_nodes = [cells[cid] for cid in connected if cid in cells and cells[cid].is_vertex]
    groups = [c for c in cells.values() if is_group(c) and c.y >= 120 and any(contains(c, n) for n in flow_nodes)]

    # Notes in the flow area are retained when they are inside a group or are left-side algorithm notes.
    notes: list[Cell] = []
    for c in cells.values():
        if not is_note(c) or c.y < 120:
            continue
        if any(contains(g, c) for g in groups) or c.x < 850:
            notes.append(c)

    all_nodes_by_id = {c.id: c for c in flow_nodes + notes}
    # Build group hierarchy based on geometric containment.
    group_objs = [Group(c) for c in groups]
    for g in group_objs:
        containers = [other for other in group_objs if other is not g and contains(other.cell, g.cell)]
        if containers:
            parent = min(containers, key=lambda z: z.cell.w * z.cell.h)
            g.parent = parent
            parent.children.append(g)

    for n in all_nodes_by_id.values():
        containers = [g for g in group_objs if contains(g.cell, n)]
        if containers:
            inner = min(containers, key=lambda z: z.cell.w * z.cell.h)
            inner.nodes.append(n)

    grouped_node_ids = {n.id for g in group_objs for n in g.nodes}
    root_nodes = [n for n in all_nodes_by_id.values() if n.id not in grouped_node_ids]
    root_groups = [g for g in group_objs if g.parent is None]

    # Only keep edges whose two endpoints belong to the computation graph.
    edge_list = [e for e in edges if e.source in all_nodes_by_id and e.target in all_nodes_by_id]

    # Extract title/equivalent note from top of the page.
    top_notes = [c for c in cells.values() if is_note(c) and c.y < 120]
    equivalent = safe_comment(top_notes[0].value) if top_notes else ''

    prefix = f'p{page_index:02d}'
    id_map = {cid: f'{prefix}_n{i:03d}' for i, cid in enumerate(sorted(all_nodes_by_id), 1)}
    group_id_map = {g.cell.id: f'{prefix}_g{i:02d}' for i, g in enumerate(sorted(group_objs, key=lambda x: (x.cell.y, x.cell.x)), 1)}

    return {
        'name': diagram.get('name', ''),
        'equivalent': equivalent,
        'nodes': all_nodes_by_id,
        'root_nodes': root_nodes,
        'root_groups': root_groups,
        'groups': group_objs,
        'edges': edge_list,
        'id_map': id_map,
        'group_id_map': group_id_map,
    }


def render_group(g: Group, data: dict, indent: str, lines: list[str], subgraph_styles: list[str]) -> None:
    gid = data['group_id_map'][g.cell.id]
    label = mermaid_label(g.cell.value)
    lines.append(f'{indent}subgraph {gid}["{label}"]')
    lines.append(f'{indent}  direction {group_direction(g.cell)}')
    for child in sorted(g.children, key=lambda z: (z.cell.y, z.cell.x)):
        render_group(child, data, indent + '  ', lines, subgraph_styles)
    for n in sorted(g.nodes, key=lambda z: (z.y, z.x)):
        lines.append(f'{indent}  {node_syntax(data["id_map"][n.id], n)}')
    lines.append(f'{indent}end')
    subgraph_styles.append(f'style {gid} fill:#ffffff,stroke:#999999,stroke-width:1px,stroke-dasharray:6 4;')


def edge_arrow(e: Cell) -> tuple[str, str | None]:
    st = e.style
    if '#82b366' in st:
        return '-.->', 'green'
    if '#6c8ebf' in st and 'dashed=1' in st:
        return '-.->', 'blue'
    if '#777777' in st:
        return '-->', 'gray'
    if 'dashed=1' in st:
        return '-.->', 'dashed'
    return '-->', None


def render_family(family: dict, page_data: dict[str, dict]) -> tuple[str, dict]:
    lines: list[str] = [INIT_LINE]
    lines.append(f'%% Family rank {family["rank"]}: {family["title"]}')
    for p in family['pages']:
        eq = page_data[p]['equivalent']
        if eq:
            lines.append(f'%% {p}: {eq}')
    lines.append('flowchart TB')
    family_id = f'family_{family["rank"]:02d}'
    lines.append(f'  subgraph {family_id}["{html.escape(family["title"], quote=True)}"]')
    lines.append('    direction TB')

    subgraph_styles: list[str] = []
    link_indices: dict[str, list[int]] = {'green': [], 'blue': [], 'gray': [], 'dashed': []}
    edge_index = 0
    node_count = 0
    edge_count = 0
    variant_ids: list[str] = []

    for vi, page_name in enumerate(family['pages'], 1):
        data = page_data[page_name]
        variant_id = f'variant_{family["rank"]:02d}_{vi:02d}'
        variant_ids.append(variant_id)
        variant_label = VARIANT_LABELS.get(page_name, page_name)
        lines.append(f'    subgraph {variant_id}["{html.escape(variant_label, quote=True)}"]')
        lines.append('      direction TB')
        for g in sorted(data['root_groups'], key=lambda z: (z.cell.y, z.cell.x)):
            render_group(g, data, '      ', lines, subgraph_styles)
        for n in sorted(data['root_nodes'], key=lambda z: (z.y, z.x)):
            lines.append(f'      {node_syntax(data["id_map"][n.id], n)}')
        node_count += len(data['nodes'])
        # Put edges inside the variant subgraph. This helps Mermaid keep each block self-contained.
        for e in data['edges']:
            arrow, kind = edge_arrow(e)
            src = data['id_map'][e.source]
            dst = data['id_map'][e.target]
            lines.append(f'      {src} {arrow} {dst}')
            if kind:
                link_indices[kind].append(edge_index)
            edge_index += 1
            edge_count += 1
        lines.append('    end')
        subgraph_styles.append(f'style {variant_id} fill:#ffffff,stroke:#666666,stroke-width:1.5px,stroke-dasharray:4 3;')

    lines.append('  end')
    lines.append(f'style {family_id} fill:#fafafa,stroke:#333333,stroke-width:2px;')
    lines.extend(subgraph_styles)
    lines.append('')
    lines.extend(CLASS_DEFS)
    lines.append('linkStyle default stroke:#333333,stroke-width:1.2px;')
    if link_indices['green']:
        lines.append(f'linkStyle {",".join(map(str, link_indices["green"]))} stroke:#82b366,stroke-width:1.5px,stroke-dasharray:5 3;')
    if link_indices['blue']:
        lines.append(f'linkStyle {",".join(map(str, link_indices["blue"]))} stroke:#6c8ebf,stroke-width:1.4px,stroke-dasharray:5 3;')
    if link_indices['gray']:
        lines.append(f'linkStyle {",".join(map(str, link_indices["gray"]))} stroke:#777777,stroke-width:1.3px;')
    if link_indices['dashed']:
        lines.append(f'linkStyle {",".join(map(str, link_indices["dashed"]))} stroke:#777777,stroke-width:1.2px,stroke-dasharray:5 3;')
    lines.append('')
    text = '\n'.join(lines)
    return text, {
        'rank': family['rank'], 'family': family['title'], 'variants': len(family['pages']),
        'pages': family['pages'], 'nodes': node_count, 'edges': edge_count,
    }


def static_validate(path: Path) -> dict:
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines()
    node_re = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:\[|\(|\{)')
    edge_re = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s+(-->|-\.->|~~~)\s+([A-Za-z_][A-Za-z0-9_]*)\s*$')
    subgraph_re = re.compile(r'^\s*subgraph\s+([A-Za-z_][A-Za-z0-9_]*)\b')
    nodes: set[str] = set()
    duplicates: list[str] = []
    edges: list[tuple[str, str]] = []
    subgraphs = 0
    ends = 0
    for line in lines:
        sm = subgraph_re.match(line)
        if sm:
            subgraphs += 1
            continue
        if line.strip() == 'end':
            ends += 1
            continue
        em = edge_re.match(line)
        if em:
            edges.append((em.group(1), em.group(3)))
            continue
        nm = node_re.match(line)
        if nm and not line.lstrip().startswith(('classDef', 'style', 'linkStyle')):
            nid = nm.group(1)
            if nid in nodes:
                duplicates.append(nid)
            nodes.add(nid)
    missing = sorted({n for e in edges for n in e if n not in nodes})
    required_colors = ['#dae8fc', '#e1d5e7', '#d5e8d4', '#fff2cc', '#f8cecc']
    checks = {
        'starts_with_init': bool(lines and lines[0].startswith('%%{init:')),
        'has_flowchart': any(line.strip() == 'flowchart TB' for line in lines),
        'subgraph_balance': subgraphs == ends,
        'no_duplicate_node_ids': not duplicates,
        'all_edge_endpoints_defined': not missing,
        'no_1014': '1014' not in text,
        'contains_1024': '1024' in text,
        'ordinary_circle_plus': '((+)):::plus' in text,
        'required_colors_present': all(c in text for c in required_colors),
        'has_class_defs': all(name in text for name in ('classDef mac', 'classDef other', 'classDef state', 'classDef plus')),
    }
    return {
        'file': path.name, 'nodes': len(nodes), 'edges': len(edges), 'subgraphs': subgraphs,
        'duplicates': duplicates, 'missing_edge_nodes': missing,
        'checks': checks, 'all_pass': all(checks.values()),
    }


def load_coverage() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with SRC_COVERAGE.open(encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            rows[row['family']] = row
    return rows


def write_readme(manifest_rows: list[dict], coverage: dict[str, dict]) -> None:
    family_to_coverage = {
        'Qwen2 / Qwen2.5 Dense': 'Qwen2/2.5 dense',
        'Qwen3 Dense': 'Qwen3 dense',
        'Llama / Yi / SmolLM Dense': 'Llama/Yi/SmolLM dense',
        'Qwen3.5 / Qwen3.6 Hybrid MoE': 'Qwen3.5/3.6 hybrid MoE',
        'Qwen3 MoE': 'Qwen3 MoE',
        'GPT-2 Dense': 'GPT-2 dense',
        'OPT Dense': 'OPT dense',
        'Qwen3.5 / Qwen3.6 Hybrid Dense': 'Qwen3.5/3.6 hybrid dense',
        'GPT-OSS MoE': 'GPT-OSS MoE',
        'Gemma 4 Dense': 'Gemma4 dense',
        'GLM DSA MoE': 'GLM DSA MoE',
        'DeepSeek V4 Hybrid MoE': 'DeepSeek V4 hybrid MoE',
        'Gemma 3 Dense': 'Gemma3 dense',
        'DeepSeek V3 / R1 MLA MoE': 'DeepSeek V3/R1 MLA MoE',
        'GPT-NeoX / Pythia Dense': 'GPT-NeoX/Pythia dense',
        'Gemma 4 MoE': 'Gemma4 MoE',
        'Kimi K3 Hybrid MoE': 'Kimi K3 hybrid MoE',
        'Granite 4 Hybrid': 'Granite4 hybrid',
        'Qwen1 Dense': 'Qwen1 dense',
        'Phi-2 Dense': 'Phi-2 dense',
        'BLOOM Dense': 'BLOOM dense',
        'OpenELM Dense': 'OpenELM dense',
        'PowerMoE': 'PowerMoE',
        'Nemotron 3 Hybrid MoE': 'Nemotron3 hybrid MoE',
        'Mistral Dense': 'Mistral dense',
    }
    lines = [
        '# 25 个开放权重 LLM 架构家族 Mermaid 计算流程图', '',
        '本包由当前 `open_llm_block_atlas_all_families_1024.drawio` 自动抽取计算节点和真实依赖边生成。右侧权重/激活面积图没有转换到 Mermaid；本包只表达单 Block 的计算流程。', '',
        '## 统一视觉语义', '',
        '- 蓝色矩形：大规模矩阵乘、Projection、QKᵀ、PV，可由 MAC/GEMM/GEMV 单元承担。',
        '- 紫色圆角矩形：Norm、Softmax、激活、逐元素计算、路由、Top-k、reshape、mask、状态更新等非矩阵操作。',
        '- 绿色圆柱：KV cache、recurrent state 等持久状态；绿色矩形表示输出。',
        '- 黄色矩形：输入或 residual 数据；白色圆形 `+` 表示 residual add。',
        '- 虚线边：状态、cache 或映射关系；灰色边：residual bypass。',
        '- 虚线分组框：GDN core、MoE expert body、DSA indexer 等内部算法区域。', '',
        '所有文件默认请求 Mermaid ELK renderer，并采用 `stepAfter` 折线、较大的 node/rank spacing，以降低连线交叉和节点覆盖。实际最终布局仍取决于使用方 Mermaid 版本。', '',
        '## 文件清单', '',
        '| 排名 | 架构家族 | MMD 文件 | 变体 | 节点 | 边 | 快照占比 |',
        '|---:|---|---|---:|---:|---:|---:|',
    ]
    for row in manifest_rows:
        cov = coverage.get(family_to_coverage[row['family']], {})
        share = cov.get('share_pct', '')
        share_s = f'{float(share):.3f}%' if share else ''
        lines.append(f"| {row['rank']} | {row['family']} | `mmd/{row['filename']}` | {row['variants']} | {row['nodes']} | {row['edges']} | {share_s} |")
    lines += ['', '## 使用方式', '', '每个 `.mmd` 文件都是一个独立 Mermaid 图：', '', '```bash', 'mmdc -i mmd/01_qwen2_qwen2_5_dense.mmd -o qwen2.svg', '```', '',
              '`all_25_families_mermaid.md` 将 25 个 Mermaid 源码按 Markdown fenced block 汇总，便于在支持 Mermaid 的 Markdown 编辑器中逐图查看。', '',
              '## 验证边界', '',
              '- 已执行 25 文件数量、节点 ID 唯一性、边端点完整性、subgraph/end 配对、颜色类、1024-token 标签和 residual 圆形 `+` 的静态检查。',
              '- 当前沙箱未安装官方 `@mermaid-js/mermaid-cli`，因此没有伪称完成 `mmdc` SVG 渲染回归。生成器保留在包内，可在本地安装 Mermaid CLI 后逐文件渲染。',
              '- Kimi K3、Granite 4、Nemotron 3 等页面继续继承当前 draw.io 图集中已经标注的 representative-family 抽象，不额外引入新的微架构断言。', '']
    README.write_text('\n'.join(lines), encoding='utf-8')


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    if not SRC_DRAWIO.exists():
        raise SystemExit(f'Missing source draw.io: {SRC_DRAWIO}')
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    MMD_DIR.mkdir(parents=True)

    root = ET.parse(SRC_DRAWIO).getroot()
    diagrams = {d.get('name', ''): d for d in root.findall('diagram')}
    required_pages = {p for fam in FAMILIES for p in fam['pages']}
    missing_pages = sorted(required_pages - diagrams.keys())
    if missing_pages:
        raise SystemExit(f'Missing source pages: {missing_pages}')

    page_data: dict[str, dict] = {}
    for idx, page_name in enumerate(sorted(required_pages), 1):
        page_data[page_name] = extract_flow(diagrams[page_name], idx)

    manifest_rows: list[dict] = []
    validations: list[dict] = []
    combined_lines = ['# 25 个开放权重 LLM 架构家族 Mermaid 计算流程图', '']

    for family in FAMILIES:
        text, meta = render_family(family, page_data)
        filename = f"{family['rank']:02d}_{family['slug']}.mmd"
        path = MMD_DIR / filename
        path.write_text(text, encoding='utf-8')
        validation = static_validate(path)
        validations.append(validation)
        meta['filename'] = filename
        meta['sha256'] = sha256(path)
        manifest_rows.append(meta)
        combined_lines += [f"## {family['rank']:02d}. {family['title']}", '', '```mermaid', text, '```', '']

    COMBINED_MD.write_text('\n'.join(combined_lines), encoding='utf-8')
    coverage = load_coverage()
    write_readme(manifest_rows, coverage)

    with MANIFEST.open('w', encoding='utf-8-sig', newline='') as f:
        fields = ['rank', 'family', 'filename', 'variants', 'nodes', 'edges', 'pages', 'sha256']
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in manifest_rows:
            out = dict(row)
            out['pages'] = ' | '.join(row['pages'])
            w.writerow(out)

    summary = {
        'source_drawio': str(SRC_DRAWIO),
        'family_count': len(FAMILIES),
        'mmd_file_count': len(list(MMD_DIR.glob('*.mmd'))),
        'total_nodes': sum(r['nodes'] for r in manifest_rows),
        'total_edges': sum(r['edges'] for r in manifest_rows),
        'all_static_checks_pass': all(v['all_pass'] for v in validations),
        'files': validations,
        'mermaid_cli_rendered': False,
        'render_note': 'Official @mermaid-js/mermaid-cli is not installed in the sandbox; static graph validation was executed instead.',
    }
    VALIDATION.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    if not summary['all_static_checks_pass']:
        failed = [v['file'] for v in validations if not v['all_pass']]
        raise SystemExit(f'Static Mermaid validation failed: {failed}')
    if summary['mmd_file_count'] != 25:
        raise SystemExit(f'Expected 25 mmd files, got {summary["mmd_file_count"]}')

    files = [README, MANIFEST, VALIDATION, COMBINED_MD, Path(__file__)] + sorted(MMD_DIR.glob('*.mmd'))
    SHA_FILE.write_text('\n'.join(f'{sha256(p)}  {p.relative_to(OUT_DIR) if p.is_relative_to(OUT_DIR) else p.name}' for p in files) + '\n', encoding='utf-8')
    files.append(SHA_FILE)

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in files:
            arc = p.relative_to(OUT_DIR) if p.is_relative_to(OUT_DIR) else Path(p.name)
            zf.write(p, arcname=str(arc))

    # ZIP CRC check.
    with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
        bad = zf.testzip()
        if bad is not None:
            raise SystemExit(f'ZIP CRC failure: {bad}')

    print(json.dumps({
        'out_dir': str(OUT_DIR), 'mmd_files': 25,
        'nodes': summary['total_nodes'], 'edges': summary['total_edges'],
        'zip': str(ZIP_PATH), 'zip_sha256': sha256(ZIP_PATH)
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

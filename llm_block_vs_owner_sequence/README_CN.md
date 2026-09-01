# llm27_13owner_sequence_v6

- 27 architecture families, 32 single-decoder-Block variant `sequenceDiagram` files.
- Qwen3.5/Qwen3.6 GDN and gated full-attention are separate files.
- Every file contains DDR + the same 13 first-level owners.
- Operator names/source-node IDs remain tied to the single-block atlas; model-level PLE prologue nodes are listed separately and excluded.
- Current implementation basis is split into the 0830 architecture review and the latest main confirmation.
- Static validation: `True`.

Directories:

- `sequence_existing_25/`: original 25-family atlas, with split Qwen3.5 variants.
- `new_families/sequence/`: Qwen3.8-Flash-Next and GLM-5.3-Flash.
- `block_qwen35_split/`, `new_families/block/`: corrected single-block DAGs from v5.1.
- `REVIEW_0830_CURRENT_MAIN_CORRECTION_CN.md`: theory/owner conflict review.
- `operator_execution_map_v6.csv`: single-decoder-Block operator mapping.
- `excluded_nonblock_operator_nodes_v6.csv`: Qwen3.8 PLE prologue nodes intentionally excluded from Block timing.
- `render_all_mmd_to_png.sh`: fixed-version Mermaid batch renderer supplied by the user.

## Render validation

- The fixed-version renderer was executed recursively on all 46 Mermaid files.
- Rendering completed with 46 PNG files and 0 failures; outputs are stored under `png/`.
- All 37 sequence diagrams use `mirrorActors: true` so participant lifelines reach the bottom actor row.
- Source-level validation remains PASS; the latest render status is recorded in `render_smoke/render_validation_v6.json`.

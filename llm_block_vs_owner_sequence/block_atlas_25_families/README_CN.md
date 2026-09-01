# 25 个 LLM Block 架构家族图集

## 目录

- `mmd/`：25 个 Mermaid block-atlas 源文件。
- `png/`：与 `mmd/` 文件名一一对应的 25 张 PNG。
- `scripts/`：Draw.io 图集生成、Draw.io 转 Mermaid、Mermaid 批量渲染脚本。
- `drawio/`：完整图集与 Qwen 精细参考图。
- `metadata/`：覆盖率、manifest、验证结果和下载快照。
- `docs/`：详细说明、来源边界和合并版 Mermaid 文档。

## 批量渲染

```bash
./scripts/render_all_mmd_to_png.sh
```

默认使用 Mermaid 11.17.2、Mermaid CLI 11.16.0，将 `mmd/` 输出到 `png/`。本次验证结果为 25/25 成功。

## 重新生成

- `scripts/llm_block_atlas_allfamilies_1024_generate.py`：生成完整 Draw.io 图集。
- `scripts/generate_open_llm_block_atlas.py`：完整生成器依赖的基础图集实现，也可独立运行。
- `scripts/generate_llm_mermaid_atlas.py`：从完整 Draw.io 图集生成 25 个 Mermaid 文件。

生成脚本只使用仓库内相对资源，输出放在本目录的 `generated/` 下。

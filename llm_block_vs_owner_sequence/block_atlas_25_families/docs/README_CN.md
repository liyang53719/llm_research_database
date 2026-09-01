# 开放权重 LLM 单 Block 架构图集（完整快照家族版，B=1，T=1024）

## 交付文件

- 主图集：`open_llm_block_atlas_all_families_1024.drawio`。
- 统一跨模型比例：`1 px² = 4 KiB`。
- 独立 Qwen 精细修订文件保留原参考图比例：`1 px² = 100 bytes`。
- 该修订版在原 90% 覆盖图集基础上，把快照中的长尾家族也补齐到 draw.io 主文件中。

## 绘图规则

- 蓝色只表示可由大量 MAC/GEMM/GEMV 支撑的矩阵乘操作。
- 紫色表示 Norm、非线性、逐元素、路由、Top-k、reshape、mask、状态更新等非矩阵操作。
- 绿色表示 cache/SRAM/recurrent state；红色表示权重；黄色/橙色表示 residual/input。
- 红色权重矩形面积等于权重字节数，长宽比保留矩阵真实两维方向。
- GDN、MoE、DSA、MLA 等复杂 block 均按内部计算过程展开，不保留模糊黑箱节点。
- 对新增长尾家族，额外检查页面边界、红色权重矩形重叠、`sumEllipse` 禁用和 visible label 中禁止残留 `1014`。

## 覆盖率

- 快照总下载量：335.49M displayed downloads。
- 本图集覆盖：快照中的 25 个架构家族，覆盖率 100%。
- 其中前 13 个家族已经达到严格 90% 阈值；这次新增的是其余长尾家族页面。

## 页面与代表配置

| 页码 | 结构家族 | 代表配置 | 同构/说明 |
|---|---|---|---|
| 01 | Qwen2/Qwen2.5 Dense | Qwen2.5-1.5B | Qwen2、Qwen2.5 dense/coder/instruct/量化变体 |
| 02 | Qwen3 Dense | Qwen3-1.7B | Qwen3 0.6B–32B dense、coder/instruct/AWQ/FP8 |
| 03 | Llama/Yi/SmolLM Dense | Llama-3.2-1B | Llama 3/3.1/3.2、TinyLlama、Yi-1.5、SmolLM2 |
| 04 | Qwen3 MoE | Qwen3-30B-A3B | Qwen3 MoE/Coder/VL 文本 Block 及量化变体 |
| 05A/05B | Qwen3.5/3.6 Dense Hybrid | Qwen3.5-2B | Ornith-9B、Bonsai-27B、Qwen3.6/3.8 dense |
| 06/07 | Qwen3.5/3.6 MoE Hybrid | Qwen3.5-35B-A3B | Qwen3.6-35B-A3B、Ornith-35B、Coder-Next |
| 08 | GPT-2 Dense | GPT-2 small | GPT-2 各尺寸、DistilGPT2、tiny-gpt2 |
| 09 | OPT Dense | OPT-125M | OPT 125M–175B |
| 10A/10B | GPT-OSS MoE | gpt-oss-20b | gpt-oss-20b/120b |
| 11A/11B | Gemma 4 Dense | Gemma-4-31B | OTel 27B/31B 等衍生 |
| 12 | GLM DSA MoE | GLM-5.2 | GLM-5.2、GLM-4.7-Flash 及 FP8/NVFP4 变体 |
| 13A/13B/13C | DeepSeek V4 Hybrid MoE | DeepSeek-V4-Flash | V4 Flash/0731/GGUF |
| 14A/14B | Gemma 3 Dense | Gemma-3-1B | Gemma-3 270M/1B/4B/12B/27B |
| 15 | DeepSeek V3/R1 MLA MoE | DeepSeek-R1 | DeepSeek V3、V3.2、R1 |
| 16 | GPT-NeoX/Pythia Dense | Pythia-160M | Pythia / GPT-NeoX dense family |
| 17A/17B | Gemma 4 MoE | Gemma-4-26B-A4B | Gemma 4 sparse-FFN 家族 |
| 18 | Kimi K3 Hybrid MLA + MoE | Kimi-K3-DSpark representative | Kimi K3 长尾家族代表页 |
| 19 | Granite 4 Hybrid Dense | granite-4.1-8b representative | Granite 4 长尾家族代表页 |
| 20 | Qwen1 Dense | Qwen-72B | Qwen1 dense 家族 |
| 21 | Phi-2 Dense | Phi-2 | Phi-2 家族代表页 |
| 22 | BLOOM Dense | bloomz-560m | BLOOM / BLOOMZ 家族 |
| 23 | OpenELM Dense | OpenELM-1_1B-Instruct | OpenELM 家族 |
| 24 | PowerMoE | PowerMoE-3b representative | PowerMoE 家族 |
| 25 | Nemotron3 Hybrid MoE | NVIDIA-Nemotron-3-Super-120B-A12B representative | Nemotron3 长尾家族代表页 |
| 26 | Mistral Dense | Mistral-7B-Instruct-v0.2 | Mistral dense 家族 |

## 长尾家族列表（本次新增）

GPT-NeoX/Pythia、Gemma 4 MoE、Kimi K3、Granite 4、Qwen1、Phi-2、BLOOM、OpenELM、PowerMoE、Nemotron3、Mistral 均已加入主图集。

## 自动校验

- draw.io XML 可解析，所有 vertex 均位于页面边界内。
- 所有红色权重矩形执行几何重叠检查。
- 禁止可见标签残留 `1014`，禁止 `shape=sumEllipse`。
- 对 Router、Top-k、Dispatch、Expert GEMM、Weighted Reduce、GDN 三分支和 Chunk Delta Rule 执行语义/颜色门禁。
- `top90_hf_text_generation_downloads_2026-08-25.csv` 保留原始仓库快照；`architecture_family_coverage.csv` 保留结构映射、份额和累计份额。

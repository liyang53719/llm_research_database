# 来源、覆盖范围与结构合并原则

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

# 0830 最新 13-owner 报告与当前 main 的交叉复核

## 审计基线

- 0830 报告：`381d85219d6feec9b10345e2800ac74d4185e5a0`，冻结通用 SLX `94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945`。
- 当前 main：`0db7eed1e80610083ecc40b1c5982f60db5bda40`，当前 q128 SLX `33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379`。
- 当前 main 仍使用 `prefill_partition_manifest v6.6`，13 个一级 owner 与 34 个声明 payload edge 未改变。
- 8/31 的 SharedMatrix shared-accumulator 与 token-dot gating 是 owner 内部实现优化，不改变 Attention 计算归属。

## 最终执行归属

| 算子/事务 | 当前执行 owner | 关键说明 |
|---|---|---|
| Q/K/V/OProj/FFN/GDN projection | SharedMatrixCore | 唯一 128×32 Matrix MAC；4096-element tile 仅 owner 内部。 |
| Q×Kᵀ | SequenceCore | `ScoreCore/QKProduct + QKBeatSum`；6 attention lanes。 |
| Softmax | SequenceCore | Online M/L recurrence。 |
| P×V | SequenceCore | `BetaTimesV + AlphaTimesO + OAdd`；不物化完整 P。 |
| Q/K HeadNorm | NormCore | 必须经 ActivationTileBuffer 的 HeadNormTileBuffer transaction。 |
| Qwen3.5 output gate | SequenceCore | Tail 捕获/服务 gate；QTileAttentionCore 执行 sigmoid 与 O scaling。 |
| Dense current SiLU/Gate×Up | SharedMatrixCore | 当前 fused `MlpSiluLane32Core`；FeedForwardCore 负责 phase/state。 |
| GDN/KDA recurrence arithmetic | SequenceCore | KVStateCore 只拥有持久 state/conv-history 生命周期。 |
| OProj buffer/request/grant | TailMatrixClientCore | OProj 数值乘法仍在 SharedMatrixCore。 |

## 与此前理论冲突的位置

1. `Q×Kᵀ/P×V 在 SequenceCore` 的结论保持成立；需要撤销的是把蓝色节点等价于 SharedMatrix 的图例解释。
2. v5 直接画 `SharedMatrix→Norm` 的 head-norm 路径与最新 SLX 不符，必须经 `ActivationTileBufferCore`。
3. v5 把 Qwen3.5 Q gate sigmoid/context gate 放入 ElementwiseTransformCore，与 `AttentionGateBufferCore + AttentionOutputGateCore` 的当前实现冲突。
4. v5 把 GDN Q/K L2Norm放在 Elementwise；最新 builder 使用 sole shared Norm service。
5. v5 把 V projection直接写 KV；当前固定边是 Matrix→Elementwise→KV。
6. v5 把当前 Dense SwiGLU 的 SiLU/Gate×Up画在 FeedForward；实际算术实体在 SharedMatrix 的 fused MLP lane。
7. v5 将 Tail输出描述为“residual input”；当前 residual是 NormCore 捕获流，Tail只提供 OProj commit metadata/data collection。

## 仍需保留的规格警告

0830报告已指出 `generate_prefill_partition_manifests` 可以分类出 `E_MATRIX_TO_ACTBUF_HEAD_NORM`、`E_ACTBUF_TO_NORM_HEAD`、`E_ACTBUF_TO_TRANSFORM`，但 v6.6 声明列表尚未包含。这批图按当前 SLX真实服务路径绘制，并标成 `HEAD/POST-NORM SERVICE`，没有伪称它们已进入冻结34-edge列表。

## v6 图集最终范围与额外修正

- 27 个家族对应 32 个单 Decoder-Block 变体；Qwen3.5 GDN/Full-Attention、Qwen3.8 GDN/QSA、GLM KDA/DSA 分文件。
- Qwen3.8 PLE 是特定层/模型级 prologue，不属于普通 Decoder Block；18 个 PLE source-node 已从时序图中排除并单独登记。
- 所有 Norm→Matrix、Norm→FFN、Norm→Elementwise 数值路径均改为先经过 ActivationTileBufferCore；低秩 Projection 后 Norm 也采用同一服务路径。
- Qwen3.8 GDN 的 Chunk partition 与 Decay matrix Γ 归 SequenceCore；Q/K L2Norm 经 ActivationTileBuffer→Norm→ActivationTileBuffer。
- GLM KDA 的 Q/K L2Norm、recurrent state commit、Gated RMSNorm 和 Tail 交接按现有 GDN owner 合同映射；均标成 future edge，不冒充当前 SLX 已实现。

# Qwen3.8-Flash-Next 与 GLM-5.3-Flash 时序图 v6

- 13-owner review: `381d85219d6feec9b10345e2800ac74d4185e5a0` / SLX `94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945`
- current main: `0db7eed1e80610083ecc40b1c5982f60db5bda40` / SLX `33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379`
- owner manifest: `6.6`

## 26a_qwen3_8_flash_next_gdn_moe_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 26: Qwen3.8-Flash-Next Hybrid MoE
%% Source block-atlas file: 26_qwen3_8_flash_next_hybrid_moe.mmd
%% Sequence file: 26a_qwen3_8_flash_next_gdn_moe_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% New-family diagrams are architecture-to-owner mappings, not claims that the current SLX already implements these operators.
sequenceDiagram
  autonumber
  participant DDR as DDR / External Memory
  participant C as ControlCore
  participant A as ActivationReadDmaCore
  participant P as ParamReadDmaCore
  participant N as NormCore
  participant B as ActivationTileBufferCore
  participant W as WeightReadDmaCore
  participant M as SharedMatrixCore
  participant E as ElementwiseTransformCore
  participant K as KVStateCore
  participant S as SequenceCore
  participant T as TailMatrixClientCore
  participant F as FeedForwardCore
  participant O as OutputCommitCore
  Note over DDR,O: Colors follow the block atlas — yellow=input, red=params/weights, blue=MAC-heavy arithmetic, purple=non-matrix, green=state/output, white=residual, gray=hardware/control
  Note over C,O: Blue means MAC-heavy math; the participant lifeline is the actual execution owner.
  Note over C,O: Current fixed payload transfers follow manifest v6.6; future-only edges are explicitly labelled [FUTURE EDGE].
  Note over C,O: Single GDN decoder Block only; PLE, vision tower, MTP and cross-layer recipe are outside this file.

  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_GR_GDN_MOE — GR read mix → GDN → GR write → MoE → GR write
  end
  loop autonomous token / chunk / recurrent-state loop
  rect rgba(255, 242, 204, 0.24)
    A-->>DDR: [HW] AXI read request — 4 residual streams
  end
  %% source-node f26v01_n010 | owner=ActivationReadDmaCore | class=input | macro=OP_GR_GDN_MOE
  rect rgba(255, 242, 204, 0.24)
    DDR->>A: 4 residual streams
  end
  rect rgba(245, 245, 245, 0.18)
    A-->>B: [HW] residual-stream staging
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>DDR: [HW] parameter read — Attention-site Gated Residual norm / low-rank gates
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] Attention-site Gated Residual parameters
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [HW] Attention-site 4-stream grouped input
  end
  %% source-node f26v01_n011 | owner=NormCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: Attention-site Gated Residual grouped RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] Attention-site normalized 4-stream tensor
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>M: [EDGE E_ACTBUF_TO_MATRIX] resident normalized 4-stream tile
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — Attention-site input_mix_weight_down / input_mix_weight_up / block_inject_weight
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] Attention-site Gated Residual projection weights
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] Attention-site Gated Residual weights
  end
  %% source-node f26v01_n012 | owner=SharedMatrixCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Attention-site input_mix_weight_down
  end
  %% source-node f26v01_n013 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site SiLU / hc_count
  end
  %% source-node f26v01_n014 | owner=SharedMatrixCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Attention-site input_mix_weight_up
  end
  %% source-node f26v01_n015 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site Sigmoid read gate
  end
  %% source-node f26v01_n016 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site 4-stream weighted mean
  end
  %% source-node f26v01_n017 | owner=SharedMatrixCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Attention-site block_inject_weight
  end
  %% source-node f26v01_n018 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site 2 × Sigmoid write gate
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>B: [FUTURE EDGE] collapsed attention-site input staging
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [FUTURE EDGE] collapsed attention-site input to shared Norm service
  end
  %% source-node f26v01_n019 | owner=NormCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] normalized GDN input
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — in_proj_qkv / in_proj_z / in_proj_a / in_proj_b / out_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] GDN projection weights
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] GDN weight tiles
  end
  %% source-node f26v01_n020 | owner=SharedMatrixCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: in_proj_qkv
  end
  %% source-node f26v01_n021 | owner=SharedMatrixCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: in_proj_z
  end
  %% source-node f26v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: in_proj_a
  end
  %% source-node f26v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: in_proj_b
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>M: [FUTURE GDN STATE EDGE] conv-history response
  end

  %% source-node f26v01_n024 | owner=SharedMatrixCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Depthwise Conv1D
  end
  rect rgba(213, 232, 212, 0.24)
    M-->>K: [FUTURE GDN STATE EDGE] updated conv-history commit
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] GDN projected / convolved stream
  end
  %% source-node f26v01_n025 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: SiLU
  end
  %% source-node f26v01_n026 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Split Q / K / V
  end
  %% source-node f26v01_n027 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Q reshape
  end
  %% source-node f26v01_n028 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: K reshape
  end
  %% source-node f26v01_n029 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: V reshape
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>B: [EDGE E_TRANSFORM_GDN_HEAD_TO_ACTBUF] Q/K/V head tiles
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [GDN HEAD-NORM SERVICE] Q/K L2Norm request / 32-lane replay
  end
  %% source-node f26v01_n030 | owner=NormCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: Q L2Norm
  end
  %% source-node f26v01_n031 | owner=NormCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: K L2Norm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [GDN HEAD-NORM SERVICE] normalized Q/K response
  end
  rect rgba(245, 245, 245, 0.18)
    K-->>S: [HW] recurrent state read
  end
  %% source-node f26v01_n032 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Decay preactivation
  end
  %% source-node f26v01_n033 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Decay factor
  end
  %% source-node f26v01_n034 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Update gate
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>B: [EDGE E_TRANSFORM_GDN_HEAD_TO_ACTBUF] Z/A/B + decay/update streams
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>S: [EDGE E_ACTBUF_GDN_VZAB_TO_SEQUENCE] normalized Q/K + V/Z/A/B tiles
  end
  %% source-node f26v01_n035 | owner=SequenceCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    S->>S: Chunk partition
  end
  %% source-node f26v01_n036 | owner=SequenceCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    S->>S: Decay matrix Γ
  end
  %% source-node f26v01_n037 | owner=SequenceCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    S->>S: K Kᵀ
  end
  %% source-node f26v01_n038 | owner=SequenceCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    S->>S: Build strict-lower L
  end
  %% source-node f26v01_n039 | owner=SequenceCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    S->>S: Triangular solve
  end
  %% source-node f26v01_n040 | owner=SequenceCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q Kᵀ
  end
  %% source-node f26v01_n041 | owner=SequenceCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    S->>S: Intra-chunk output
  end
  %% source-node f26v01_n042 | owner=SequenceCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    S->>S: State read
  end
  %% source-node f26v01_n043 | owner=SequenceCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    S->>S: Output combine
  end
  %% source-node f26v01_n044 | owner=SequenceCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    S->>S: Kᵀ U
  end
  %% source-node f26v01_n045 | owner=SequenceCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    S->>S: State decay
  end
  %% source-node f26v01_n046 | owner=KVStateCore | class=state | macro=OP_GR_GDN_MOE
  rect rgba(213, 232, 212, 0.24)
    S-->>K: [GDN STATE COMMIT] updated recurrent state S
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>N: [FUTURE GDN NORM SERVICE] GDN output + gate request
  end
  %% source-node f26v01_n047 | owner=NormCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNormGated
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>S: [FUTURE GDN NORM SERVICE] normalized/gated GDN response
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [FUTURE GDN TAIL EDGE] gated GDN output + tags
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>M: [HW] out_proj request
  end
  %% source-node f26v01_n048 | owner=SharedMatrixCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: out_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>T: [EDGE E_MATRIX_TO_TAIL] out_proj result tile
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>O: [EDGE E_MATRIX_TO_COMMIT] OProj result stream128
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>E: [HW] Attention-site sublayer output + GR injection metadata
  end
  %% source-node f26v01_n049 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site write-gate injection into 4 residual branches
  end
  %% source-node f26v01_n050 | owner=OutputCommitCore | class=state | macro=OP_GR_GDN_MOE
  rect rgba(213, 232, 212, 0.24)
    O->>O: Attention-site 4-branch residual-state commit
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>DDR: [HW] parameter read — MLP-site Gated Residual norm / low-rank gates
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] MLP-site Gated Residual parameters
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [HW] MLP-site 4-stream grouped input
  end
  %% source-node f26v01_n051 | owner=NormCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: MLP-site Gated Residual grouped RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] MLP-site normalized 4-stream tensor
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>M: [EDGE E_ACTBUF_TO_MATRIX] resident normalized 4-stream tile
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — MLP-site input_mix_weight_down / input_mix_weight_up / block_inject_weight
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] MLP-site Gated Residual projection weights
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] MLP-site Gated Residual weights
  end
  %% source-node f26v01_n052 | owner=SharedMatrixCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: MLP-site input_mix_weight_down
  end
  %% source-node f26v01_n053 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: MLP-site SiLU / hc_count
  end
  %% source-node f26v01_n054 | owner=SharedMatrixCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: MLP-site input_mix_weight_up
  end
  %% source-node f26v01_n055 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: MLP-site Sigmoid read gate
  end
  %% source-node f26v01_n056 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: MLP-site 4-stream weighted mean
  end
  %% source-node f26v01_n057 | owner=SharedMatrixCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: MLP-site block_inject_weight
  end
  %% source-node f26v01_n058 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: MLP-site 2 × Sigmoid write gate
  end
  rect rgba(245, 245, 245, 0.18)
    O-->>B: [HW] updated residual / MLP input staging
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [HW] MLP input stream
  end
  %% source-node f26v01_n059 | owner=NormCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] normalized FFN input
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [EDGE E_ACTBUF_TO_FFN] normalized FFN input
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — Router + 512 routed experts + shared expert
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] MoE weights
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] router / expert weight tiles
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Router projection request
  end
  %% source-node f26v01_n060 | owner=SharedMatrixCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] router logits
  end
  %% source-node f26v01_n061 | owner=FeedForwardCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Sigmoid router scoring
  end
  %% source-node f26v01_n062 | owner=FeedForwardCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Top-10 + renorm
  end
  %% source-node f26v01_n063 | owner=FeedForwardCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Dispatch / gather
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>B: [HW] expert token queues
  end
  loop active routed experts — 10 selected of 512
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] selected expert token batch
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Routed Expert gate_up_proj request
  end
  %% source-node f26v01_n064 | owner=SharedMatrixCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Routed Expert gate_up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] routed gate/up result
  end
  %% source-node f26v01_n065 | owner=FeedForwardCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: SiLU × up
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Routed Expert down_proj request
  end
  %% source-node f26v01_n066 | owner=SharedMatrixCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Routed Expert down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] routed expert output
  end
  %% source-node f26v01_n067 | owner=FeedForwardCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Expert weighting
  end
  end
  par Shared Expert
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Shared Expert gate_proj / up_proj request
  end
  %% source-node f26v01_n068 | owner=SharedMatrixCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared Expert gate_proj
  end
  %% source-node f26v01_n069 | owner=SharedMatrixCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared Expert up_proj
  end
  %% source-node f26v01_n070 | owner=FeedForwardCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Shared Expert SiLU × up
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Shared Expert down_proj request
  end
  %% source-node f26v01_n071 | owner=SharedMatrixCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared Expert down_proj
  end
  and Shared Expert gate
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Shared Expert gate projection request
  end
  %% source-node f26v01_n072 | owner=SharedMatrixCore | class=mac | macro=OP_GR_GDN_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared Expert gate projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] shared gate scalar
  end
  %% source-node f26v01_n073 | owner=FeedForwardCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Shared Expert gate Sigmoid
  end
  end
  %% source-node f26v01_n074 | owner=FeedForwardCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Scatter / weighted reduce
  end
  %% source-node f26v01_n075 | owner=FeedForwardCore | class=plus | macro=OP_GR_GDN_MOE
  rect rgba(255, 255, 255, 0.28)
    F->>F: Routed + Shared Expert sum
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>E: [HW] MLP-site sublayer output + GR injection metadata
  end
  %% source-node f26v01_n076 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_GDN_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: MLP-site write-gate injection into 4 residual branches
  end
  %% source-node f26v01_n077 | owner=OutputCommitCore | class=state | macro=OP_GR_GDN_MOE
  rect rgba(213, 232, 212, 0.24)
    O->>O: MLP-site 4-branch residual-state commit
  end
  rect rgba(213, 232, 212, 0.24)
    O-->>DDR: [HW] write updated 4 residual streams
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_GR_GDN_MOE done
  end

```

## 26b_qwen3_8_flash_next_qsa_moe_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 26: Qwen3.8-Flash-Next Hybrid MoE
%% Source block-atlas file: 26_qwen3_8_flash_next_hybrid_moe.mmd
%% Sequence file: 26b_qwen3_8_flash_next_qsa_moe_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% New-family diagrams are architecture-to-owner mappings, not claims that the current SLX already implements these operators.
sequenceDiagram
  autonumber
  participant DDR as DDR / External Memory
  participant C as ControlCore
  participant A as ActivationReadDmaCore
  participant P as ParamReadDmaCore
  participant N as NormCore
  participant B as ActivationTileBufferCore
  participant W as WeightReadDmaCore
  participant M as SharedMatrixCore
  participant E as ElementwiseTransformCore
  participant K as KVStateCore
  participant S as SequenceCore
  participant T as TailMatrixClientCore
  participant F as FeedForwardCore
  participant O as OutputCommitCore
  Note over DDR,O: Colors follow the block atlas — yellow=input, red=params/weights, blue=MAC-heavy arithmetic, purple=non-matrix, green=state/output, white=residual, gray=hardware/control
  Note over C,O: Blue means MAC-heavy math; the participant lifeline is the actual execution owner.
  Note over C,O: Current fixed payload transfers follow manifest v6.6; future-only edges are explicitly labelled [FUTURE EDGE].

  Note over C,O: Single QSA decoder Block only; PLE, vision tower, MTP and cross-layer recipe are outside this file.
  Note over C,O: QSA uses a compressed micro-block indexer: 4 Q index heads, 1 K head, budget 512 blocks / 2048 tokens.
  Note over C,O: Main attention uses 24 Q heads, 2 KV heads, head_dim 256 and partial interleaved MRoPE.
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_GR_QSA_MOE — GR read mix → QSA sparse attention → GR write → MoE → GR write
  end
  loop autonomous token / micro-block / sparse-attention loop
  rect rgba(255, 242, 204, 0.24)
    A-->>DDR: [HW] AXI read request — 4 residual streams
  end
  %% source-node f26v02_n010 | owner=ActivationReadDmaCore | class=input | macro=OP_GR_QSA_MOE
  rect rgba(255, 242, 204, 0.24)
    DDR->>A: 4 residual streams
  end
  rect rgba(245, 245, 245, 0.18)
    A-->>B: [HW] residual-stream staging
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>DDR: [HW] parameter read — Attention-site Gated Residual norm / low-rank gates
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] Attention-site Gated Residual parameters
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [HW] Attention-site 4-stream grouped input
  end
  %% source-node f26v02_n011 | owner=NormCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: Attention-site Gated Residual grouped RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] Attention-site normalized 4-stream tensor
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>M: [EDGE E_ACTBUF_TO_MATRIX] resident normalized 4-stream tile
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — Attention-site input_mix_weight_down / input_mix_weight_up / block_inject_weight
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] Attention-site Gated Residual projection weights
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] Attention-site Gated Residual weights
  end
  %% source-node f26v02_n012 | owner=SharedMatrixCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Attention-site input_mix_weight_down
  end
  %% source-node f26v02_n013 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site SiLU / hc_count
  end
  %% source-node f26v02_n014 | owner=SharedMatrixCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Attention-site input_mix_weight_up
  end
  %% source-node f26v02_n015 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site Sigmoid read gate
  end
  %% source-node f26v02_n016 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site 4-stream weighted mean
  end
  %% source-node f26v02_n017 | owner=SharedMatrixCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Attention-site block_inject_weight
  end
  %% source-node f26v02_n018 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site 2 × Sigmoid write gate
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>B: [FUTURE EDGE] collapsed QSA input staging
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [FUTURE EDGE] collapsed QSA input to shared Norm service
  end
  %% source-node f26v02_n019 | owner=NormCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] normalized QSA input
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — Q/K/V/O + QSA indexer projections
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] QSA / indexer weights
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] QSA / indexer weight tiles
  end
  %% source-node f26v02_n020 | owner=SharedMatrixCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: K Proj
  end
  %% source-node f26v02_n021 | owner=SharedMatrixCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: V Proj
  end
  %% source-node f26v02_n022 | owner=SharedMatrixCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q Proj + gate
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>T: [EDGE E_MATRIX_TO_TAIL_Q_GATE_SPLIT] Q/gate split; K projection continues through head-norm staging
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>B: [EDGE E_TAIL_TO_ACTBUF_Q_QUERY] Q query stream
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>S: [EDGE E_TAIL_TO_SEQUENCE_Q_GATE] Q gate stream
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>B: [HEAD-NORM STAGING] K head stream
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [HEAD-NORM SERVICE] Q/K Head RMSNorm request / 32-lane replay
  end

  %% source-node f26v02_n023 | owner=NormCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: K Head RMSNorm
  end
  %% source-node f26v02_n024 | owner=NormCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: Q Head RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HEAD-NORM SERVICE] normalized Q/K head response
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>E: [HEAD-NORM REPLAY] normalized Q/K heads to partial interleaved MRoPE
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V projection bypass/dispatch stream
  end
  %% source-node f26v02_n025 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Partial interleaved MRoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [EDGE E_TRANSFORM_TO_KV] rotated K + V-bypass cache-write streams
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>S: [EDGE E_TRANSFORM_TO_SEQUENCE] rotated Q stream
  end
  %% source-node f26v02_n026 | owner=KVStateCore | class=state | macro=OP_GR_QSA_MOE
  rect rgba(213, 232, 212, 0.24)
    K->>K: QSA K/V cache
  end
  %% source-node f26v02_n027 | owner=SharedMatrixCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: index_qk_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>B: [HEAD-NORM STAGING] Indexer Q/K head streams
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [HEAD-NORM SERVICE] Indexer Q/K RMSNorm request / 32-lane replay
  end
  %% source-node f26v02_n028 | owner=NormCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: Indexer Q RMSNorm
  end
  %% source-node f26v02_n029 | owner=NormCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: Indexer K RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HEAD-NORM SERVICE] normalized indexer Q/K response
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>S: [FUTURE QSA EDGE] normalized indexer Q/K vectors
  end
  %% source-node f26v02_n030 | owner=SequenceCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    S->>S: Micro-block mean pool ×4
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>E: [HW] pooled index K
  end
  %% source-node f26v02_n031 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Indexer K RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>S: [HW] rotated pooled index K
  end
  %% source-node f26v02_n032 | owner=SequenceCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    S->>S: Indexer Q × pooled Kᵀ
  end
  %% source-node f26v02_n033 | owner=SequenceCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    S->>S: ReLU + index-head sum
  end
  %% source-node f26v02_n034 | owner=SequenceCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    S->>S: Top-512 micro-blocks / 2048 tokens
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>K: [HW] selected token indices + local tail
  end
  %% source-node f26v02_n035 | owner=KVStateCore | class=state | macro=OP_GR_QSA_MOE
  rect rgba(213, 232, 212, 0.24)
    K->>K: Selected K/V gather + local tail
  end
  rect rgba(245, 245, 245, 0.18)
    K-->>S: [HW] selected K/V vectors
  end
  %% source-node f26v02_n036 | owner=SequenceCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    S->>S: Sparse Q × Kᵀ
  end
  %% source-node f26v02_n037 | owner=SequenceCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f26v02_n038 | owner=SequenceCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    S->>S: Sparse P × V / Online O recurrence (selected V)
  end
  %% source-node f26v02_n039 | owner=SequenceCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    S->>S: Sigmoid output gate (AttentionOutputGateCore)
  end
  %% source-node f26v02_n040 | owner=SequenceCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    S->>S: Context gating (scale final O)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [EDGE E_SEQUENCE_TO_TAIL] gated attention context + tags
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>M: [HW] O Proj request
  end
  %% source-node f26v02_n041 | owner=SharedMatrixCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: O Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>T: [EDGE E_MATRIX_TO_TAIL] O Proj result tile
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>O: [EDGE E_MATRIX_TO_COMMIT] OProj result stream128
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>E: [HW] Attention-site sublayer output + GR injection metadata
  end
  %% source-node f26v02_n042 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site write-gate injection into 4 residual branches
  end
  %% source-node f26v02_n043 | owner=OutputCommitCore | class=state | macro=OP_GR_QSA_MOE
  rect rgba(213, 232, 212, 0.24)
    O->>O: Attention-site 4-branch residual-state commit
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>DDR: [HW] parameter read — MLP-site Gated Residual norm / low-rank gates
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] MLP-site Gated Residual parameters
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [HW] MLP-site 4-stream grouped input
  end
  %% source-node f26v02_n044 | owner=NormCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: MLP-site Gated Residual grouped RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] MLP-site normalized 4-stream tensor
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>M: [EDGE E_ACTBUF_TO_MATRIX] resident normalized 4-stream tile
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — MLP-site input_mix_weight_down / input_mix_weight_up / block_inject_weight
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] MLP-site Gated Residual projection weights
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] MLP-site Gated Residual weights
  end
  %% source-node f26v02_n045 | owner=SharedMatrixCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: MLP-site input_mix_weight_down
  end
  %% source-node f26v02_n046 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: MLP-site SiLU / hc_count
  end
  %% source-node f26v02_n047 | owner=SharedMatrixCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: MLP-site input_mix_weight_up
  end
  %% source-node f26v02_n048 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: MLP-site Sigmoid read gate
  end
  %% source-node f26v02_n049 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: MLP-site 4-stream weighted mean
  end
  %% source-node f26v02_n050 | owner=SharedMatrixCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: MLP-site block_inject_weight
  end
  %% source-node f26v02_n051 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: MLP-site 2 × Sigmoid write gate
  end
  rect rgba(245, 245, 245, 0.18)
    O-->>B: [HW] updated residual / MLP input staging
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [HW] MLP input stream
  end
  %% source-node f26v02_n052 | owner=NormCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] normalized FFN input
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [EDGE E_ACTBUF_TO_FFN] normalized FFN input
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — Router + 512 routed experts + shared expert
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] MoE weights
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] router / expert weight tiles
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Router projection request
  end
  %% source-node f26v02_n053 | owner=SharedMatrixCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] router logits
  end
  %% source-node f26v02_n054 | owner=FeedForwardCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Sigmoid router scoring
  end
  %% source-node f26v02_n055 | owner=FeedForwardCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Top-10 + renorm
  end
  %% source-node f26v02_n056 | owner=FeedForwardCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Dispatch / gather
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>B: [HW] expert token queues
  end
  loop active routed experts — 10 selected of 512
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] selected expert token batch
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Routed Expert gate_up_proj request
  end
  %% source-node f26v02_n057 | owner=SharedMatrixCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Routed Expert gate_up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] routed gate/up result
  end
  %% source-node f26v02_n058 | owner=FeedForwardCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: SiLU × up
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Routed Expert down_proj request
  end
  %% source-node f26v02_n059 | owner=SharedMatrixCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Routed Expert down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] routed expert output
  end
  %% source-node f26v02_n060 | owner=FeedForwardCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Expert weighting
  end
  end
  par Shared Expert
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Shared Expert gate_proj / up_proj request
  end
  %% source-node f26v02_n061 | owner=SharedMatrixCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared Expert gate_proj
  end
  %% source-node f26v02_n062 | owner=SharedMatrixCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared Expert up_proj
  end
  %% source-node f26v02_n063 | owner=FeedForwardCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Shared Expert SiLU × up
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Shared Expert down_proj request
  end
  %% source-node f26v02_n064 | owner=SharedMatrixCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared Expert down_proj
  end
  and Shared Expert gate
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Shared Expert gate projection request
  end
  %% source-node f26v02_n065 | owner=SharedMatrixCore | class=mac | macro=OP_GR_QSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared Expert gate projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] shared gate scalar
  end
  %% source-node f26v02_n066 | owner=FeedForwardCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Shared Expert gate Sigmoid
  end
  end
  %% source-node f26v02_n067 | owner=FeedForwardCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Scatter / weighted reduce
  end
  %% source-node f26v02_n068 | owner=FeedForwardCore | class=plus | macro=OP_GR_QSA_MOE
  rect rgba(255, 255, 255, 0.28)
    F->>F: Routed + Shared Expert sum
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>E: [HW] MLP-site sublayer output + GR injection metadata
  end
  %% source-node f26v02_n069 | owner=ElementwiseTransformCore | class=other | macro=OP_GR_QSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: MLP-site write-gate injection into 4 residual branches
  end
  %% source-node f26v02_n070 | owner=OutputCommitCore | class=state | macro=OP_GR_QSA_MOE
  rect rgba(213, 232, 212, 0.24)
    O->>O: MLP-site 4-branch residual-state commit
  end
  rect rgba(213, 232, 212, 0.24)
    O-->>DDR: [HW] write updated 4 residual streams
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_GR_QSA_MOE done
  end

```

## 27a_glm5_3_flash_kda_dense_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 27: GLM-5.3-Flash Hybrid MoE
%% Source block-atlas file: 27_glm5_3_flash_hybrid_moe.mmd
%% Sequence file: 27a_glm5_3_flash_kda_dense_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% New-family diagrams are architecture-to-owner mappings, not claims that the current SLX already implements these operators.
sequenceDiagram
  autonumber
  participant DDR as DDR / External Memory
  participant C as ControlCore
  participant A as ActivationReadDmaCore
  participant P as ParamReadDmaCore
  participant N as NormCore
  participant B as ActivationTileBufferCore
  participant W as WeightReadDmaCore
  participant M as SharedMatrixCore
  participant E as ElementwiseTransformCore
  participant K as KVStateCore
  participant S as SequenceCore
  participant T as TailMatrixClientCore
  participant F as FeedForwardCore
  participant O as OutputCommitCore
  Note over DDR,O: Colors follow the block atlas — yellow=input, red=params/weights, blue=MAC-heavy arithmetic, purple=non-matrix, green=state/output, white=residual, gray=hardware/control
  Note over C,O: Blue means MAC-heavy math; the participant lifeline is the actual execution owner.
  Note over C,O: Current fixed payload transfers follow manifest v6.6; future-only edges are explicitly labelled [FUTURE EDGE].

  Note over C,O: Single KDA decoder Block only; cross-layer KDA/DSA ratio is outside this file.
  Note over C,O: KDA is Kimi-style delta attention with Q/K L2Norm, depthwise Conv1D, forget/input gates and recurrent state.
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_MHC_KDA_DENSE — mHC → KDA → mHC → Dense SwiGLU → mHC
  end
  loop autonomous token / chunk / recurrent-state loop
  rect rgba(255, 242, 204, 0.24)
    A-->>DDR: [HW] AXI read request — 4 residual streams
  end
  %% source-node f27v01_n001 | owner=ActivationReadDmaCore | class=input | macro=OP_MHC_KDA_DENSE
  rect rgba(255, 242, 204, 0.24)
    DDR->>A: 4 residual streams
  end
  rect rgba(245, 245, 245, 0.18)
    A-->>B: [HW] residual-stream staging
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [HW] Attention-site 4 residual streams
  end
  %% source-node f27v01_n002 | owner=NormCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    N->>N: Attention-site mHC input RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] Attention-site normalized flattened 4-stream tensor
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>M: [EDGE E_ACTBUF_TO_MATRIX] resident normalized 4-stream tile
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — Attention-site mHC fn/base/scale
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] Attention-site mHC parameters
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] Attention-site mHC projection weights
  end
  %% source-node f27v01_n003 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_DENSE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Attention-site mHC F.linear(fn)
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Attention-site pre/post/comb logits
  end
  %% source-node f27v01_n004 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site Sigmoid pre weights
  end
  %% source-node f27v01_n005 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site 2 × Sigmoid post weights
  end
  %% source-node f27v01_n006 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site Softmax + Sinkhorn combine matrix
  end
  %% source-node f27v01_n007 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site 4-stream collapse
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>B: [FUTURE EDGE] collapsed KDA input staging
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [FUTURE EDGE] collapsed KDA input to shared Norm service
  end
  %% source-node f27v01_n008 | owner=NormCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    N->>N: Input RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] normalized KDA input
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — Q/K/V, forget/input/output gates, O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] KDA weights
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] KDA weight tiles
  end
  %% source-node f27v01_n009 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_DENSE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q Proj
  end
  %% source-node f27v01_n010 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_DENSE
  rect rgba(218, 232, 252, 0.24)
    M->>M: K Proj
  end
  %% source-node f27v01_n011 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_DENSE
  rect rgba(218, 232, 252, 0.24)
    M->>M: V Proj
  end
  %% source-node f27v01_n012 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_DENSE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Depthwise Conv1D
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] convolved Q/K/V stream
  end
  %% source-node f27v01_n013 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    E->>E: SiLU
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>B: [FUTURE KDA HEAD STAGING] convolved Q/K/V head streams
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [FUTURE KDA NORM SERVICE] Q/K L2Norm request / 32-lane replay
  end
  %% source-node f27v01_n014 | owner=NormCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    N->>N: Q L2Norm
  end
  %% source-node f27v01_n015 | owner=NormCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    N->>N: K L2Norm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [FUTURE KDA NORM SERVICE] normalized Q/K response
  end
  %% source-node f27v01_n016 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_DENSE
  rect rgba(218, 232, 252, 0.24)
    M->>M: f_a_proj
  end
  %% source-node f27v01_n017 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_DENSE
  rect rgba(218, 232, 252, 0.24)
    M->>M: f_b_proj
  end
  %% source-node f27v01_n018 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_DENSE
  rect rgba(218, 232, 252, 0.24)
    M->>M: b_proj
  end
  %% source-node f27v01_n019 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_DENSE
  rect rgba(218, 232, 252, 0.24)
    M->>M: g_a_proj
  end
  %% source-node f27v01_n020 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_DENSE
  rect rgba(218, 232, 252, 0.24)
    M->>M: g_b_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] forget/input/output gate projections
  end
  %% source-node f27v01_n021 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    E->>E: dt_bias + A_log
  end
  %% source-node f27v01_n022 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Exp forget decay
  end
  %% source-node f27v01_n023 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Safe lower-bound clamp
  end
  %% source-node f27v01_n024 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Sigmoid input gate β
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>B: [FUTURE KDA STAGING] V + forget decay + β + output-gate projection
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>S: [FUTURE KDA EDGE] normalized Q/K + V + decay + β
  end
  rect rgba(245, 245, 245, 0.18)
    K-->>S: [HW] KDA recurrent state read
  end
  %% source-node f27v01_n025 | owner=SequenceCore | class=mac | macro=OP_MHC_KDA_DENSE
  rect rgba(218, 232, 252, 0.24)
    S->>S: Kimi Delta Attention — chunk / recurrent
  end
  %% source-node f27v01_n026 | owner=SequenceCore | class=state | macro=OP_MHC_KDA_DENSE
  rect rgba(213, 232, 212, 0.24)
    S->>S: KDA recurrent state update
  end
  rect rgba(213, 232, 212, 0.24)
    S-->>K: [FUTURE KDA STATE COMMIT] updated recurrent state
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>N: [FUTURE KDA NORM SERVICE] KDA core output + output-gate request
  end
  %% source-node f27v01_n027 | owner=NormCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    N->>N: Gated RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>S: [FUTURE KDA NORM SERVICE] normalized/gated KDA response
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [FUTURE KDA TAIL EDGE] final KDA output + tags
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>M: [HW] O Proj request
  end
  %% source-node f27v01_n028 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_DENSE
  rect rgba(218, 232, 252, 0.24)
    M->>M: O Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>T: [EDGE E_MATRIX_TO_TAIL] O Proj result tile
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>O: [EDGE E_MATRIX_TO_COMMIT] OProj result stream128
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>E: [HW] Attention-site sublayer output
  end
  %% source-node f27v01_n029 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site post × output + combᵀ × residual streams
  end
  %% source-node f27v01_n030 | owner=OutputCommitCore | class=state | macro=OP_MHC_KDA_DENSE
  rect rgba(213, 232, 212, 0.24)
    O->>O: Attention-site 4-stream residual commit
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [HW] FFN-site 4 residual streams
  end
  %% source-node f27v01_n031 | owner=NormCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    N->>N: FFN-site mHC input RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] FFN-site normalized flattened 4-stream tensor
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>M: [EDGE E_ACTBUF_TO_MATRIX] resident normalized 4-stream tile
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — FFN-site mHC fn/base/scale
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] FFN-site mHC parameters
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] FFN-site mHC projection weights
  end
  %% source-node f27v01_n032 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_DENSE
  rect rgba(218, 232, 252, 0.24)
    M->>M: FFN-site mHC F.linear(fn)
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] FFN-site pre/post/comb logits
  end
  %% source-node f27v01_n033 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    E->>E: FFN-site Sigmoid pre weights
  end
  %% source-node f27v01_n034 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    E->>E: FFN-site 2 × Sigmoid post weights
  end
  %% source-node f27v01_n035 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    E->>E: FFN-site Softmax + Sinkhorn combine matrix
  end
  %% source-node f27v01_n036 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    E->>E: FFN-site 4-stream collapse
  end
  rect rgba(245, 245, 245, 0.18)
    O-->>B: [HW] updated residual / dense FFN input staging
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [HW] FFN input stream
  end
  %% source-node f27v01_n037 | owner=NormCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] normalized FFN input
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [EDGE E_ACTBUF_TO_FFN] normalized FFN input
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — gate_proj / up_proj / down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] dense FFN weights
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] dense FFN weight tiles
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] gate_proj / up_proj request
  end
  %% source-node f27v01_n038 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_DENSE
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  %% source-node f27v01_n039 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_DENSE
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] gate/up result
  end
  %% source-node f27v01_n040 | owner=FeedForwardCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Clamp gate≤10 / up∈[-10,10]
  end
  %% source-node f27v01_n041 | owner=FeedForwardCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    F->>F: SiLU
  end
  %% source-node f27v01_n042 | owner=FeedForwardCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Elementwise gate
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] down_proj request
  end
  %% source-node f27v01_n043 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_DENSE
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] dense FFN output
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>E: [HW] FFN-site sublayer output
  end
  %% source-node f27v01_n044 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_DENSE
  rect rgba(225, 213, 231, 0.24)
    E->>E: FFN-site post × output + combᵀ × residual streams
  end
  %% source-node f27v01_n045 | owner=OutputCommitCore | class=state | macro=OP_MHC_KDA_DENSE
  rect rgba(213, 232, 212, 0.24)
    O->>O: FFN-site 4-stream residual commit
  end
  rect rgba(213, 232, 212, 0.24)
    O-->>DDR: [HW] write 4 residual streams
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_MHC_KDA_DENSE done
  end

```

## 27b_glm5_3_flash_kda_moe_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 27: GLM-5.3-Flash Hybrid MoE
%% Source block-atlas file: 27_glm5_3_flash_hybrid_moe.mmd
%% Sequence file: 27b_glm5_3_flash_kda_moe_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% New-family diagrams are architecture-to-owner mappings, not claims that the current SLX already implements these operators.
sequenceDiagram
  autonumber
  participant DDR as DDR / External Memory
  participant C as ControlCore
  participant A as ActivationReadDmaCore
  participant P as ParamReadDmaCore
  participant N as NormCore
  participant B as ActivationTileBufferCore
  participant W as WeightReadDmaCore
  participant M as SharedMatrixCore
  participant E as ElementwiseTransformCore
  participant K as KVStateCore
  participant S as SequenceCore
  participant T as TailMatrixClientCore
  participant F as FeedForwardCore
  participant O as OutputCommitCore
  Note over DDR,O: Colors follow the block atlas — yellow=input, red=params/weights, blue=MAC-heavy arithmetic, purple=non-matrix, green=state/output, white=residual, gray=hardware/control
  Note over C,O: Blue means MAC-heavy math; the participant lifeline is the actual execution owner.
  Note over C,O: Current fixed payload transfers follow manifest v6.6; future-only edges are explicitly labelled [FUTURE EDGE].

  Note over C,O: Single KDA decoder Block only; cross-layer KDA/DSA ratio is outside this file.
  Note over C,O: KDA is Kimi-style delta attention with Q/K L2Norm, depthwise Conv1D, forget/input gates and recurrent state.
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_MHC_KDA_MOE — mHC → KDA → mHC → Top-8 Routed/Shared MoE → mHC
  end
  loop autonomous token / chunk / recurrent-state loop
  rect rgba(255, 242, 204, 0.24)
    A-->>DDR: [HW] AXI read request — 4 residual streams
  end
  %% source-node f27v02_n001 | owner=ActivationReadDmaCore | class=input | macro=OP_MHC_KDA_MOE
  rect rgba(255, 242, 204, 0.24)
    DDR->>A: 4 residual streams
  end
  rect rgba(245, 245, 245, 0.18)
    A-->>B: [HW] residual-stream staging
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [HW] Attention-site 4 residual streams
  end
  %% source-node f27v02_n002 | owner=NormCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: Attention-site mHC input RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] Attention-site normalized flattened 4-stream tensor
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>M: [EDGE E_ACTBUF_TO_MATRIX] resident normalized 4-stream tile
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — Attention-site mHC fn/base/scale
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] Attention-site mHC parameters
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] Attention-site mHC projection weights
  end
  %% source-node f27v02_n003 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Attention-site mHC F.linear(fn)
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Attention-site pre/post/comb logits
  end
  %% source-node f27v02_n004 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site Sigmoid pre weights
  end
  %% source-node f27v02_n005 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site 2 × Sigmoid post weights
  end
  %% source-node f27v02_n006 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site Softmax + Sinkhorn combine matrix
  end
  %% source-node f27v02_n007 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site 4-stream collapse
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>B: [FUTURE EDGE] collapsed KDA input staging
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [FUTURE EDGE] collapsed KDA input to shared Norm service
  end
  %% source-node f27v02_n008 | owner=NormCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: Input RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] normalized KDA input
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — Q/K/V, forget/input/output gates, O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] KDA weights
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] KDA weight tiles
  end
  %% source-node f27v02_n009 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q Proj
  end
  %% source-node f27v02_n010 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: K Proj
  end
  %% source-node f27v02_n011 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: V Proj
  end
  %% source-node f27v02_n012 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Depthwise Conv1D
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] convolved Q/K/V stream
  end
  %% source-node f27v02_n013 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: SiLU
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>B: [FUTURE KDA HEAD STAGING] convolved Q/K/V head streams
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [FUTURE KDA NORM SERVICE] Q/K L2Norm request / 32-lane replay
  end
  %% source-node f27v02_n014 | owner=NormCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: Q L2Norm
  end
  %% source-node f27v02_n015 | owner=NormCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: K L2Norm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [FUTURE KDA NORM SERVICE] normalized Q/K response
  end
  %% source-node f27v02_n016 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: f_a_proj
  end
  %% source-node f27v02_n017 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: f_b_proj
  end
  %% source-node f27v02_n018 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: b_proj
  end
  %% source-node f27v02_n019 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: g_a_proj
  end
  %% source-node f27v02_n020 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: g_b_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] forget/input/output gate projections
  end
  %% source-node f27v02_n021 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: dt_bias + A_log
  end
  %% source-node f27v02_n022 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Exp forget decay
  end
  %% source-node f27v02_n023 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Safe lower-bound clamp
  end
  %% source-node f27v02_n024 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Sigmoid input gate β
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>B: [FUTURE KDA STAGING] V + forget decay + β + output-gate projection
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>S: [FUTURE KDA EDGE] normalized Q/K + V + decay + β
  end
  rect rgba(245, 245, 245, 0.18)
    K-->>S: [HW] KDA recurrent state read
  end
  %% source-node f27v02_n025 | owner=SequenceCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    S->>S: Kimi Delta Attention — chunk / recurrent
  end
  %% source-node f27v02_n026 | owner=SequenceCore | class=state | macro=OP_MHC_KDA_MOE
  rect rgba(213, 232, 212, 0.24)
    S->>S: KDA recurrent state update
  end
  rect rgba(213, 232, 212, 0.24)
    S-->>K: [FUTURE KDA STATE COMMIT] updated recurrent state
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>N: [FUTURE KDA NORM SERVICE] KDA core output + output-gate request
  end
  %% source-node f27v02_n027 | owner=NormCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: Gated RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>S: [FUTURE KDA NORM SERVICE] normalized/gated KDA response
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [FUTURE KDA TAIL EDGE] final KDA output + tags
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>M: [HW] O Proj request
  end
  %% source-node f27v02_n028 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: O Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>T: [EDGE E_MATRIX_TO_TAIL] O Proj result tile
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>O: [EDGE E_MATRIX_TO_COMMIT] OProj result stream128
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>E: [HW] Attention-site sublayer output
  end
  %% source-node f27v02_n029 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site post × output + combᵀ × residual streams
  end
  %% source-node f27v02_n030 | owner=OutputCommitCore | class=state | macro=OP_MHC_KDA_MOE
  rect rgba(213, 232, 212, 0.24)
    O->>O: Attention-site 4-stream residual commit
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [HW] FFN-site 4 residual streams
  end
  %% source-node f27v02_n031 | owner=NormCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: FFN-site mHC input RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] FFN-site normalized flattened 4-stream tensor
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>M: [EDGE E_ACTBUF_TO_MATRIX] resident normalized 4-stream tile
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — FFN-site mHC fn/base/scale
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] FFN-site mHC parameters
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] FFN-site mHC projection weights
  end
  %% source-node f27v02_n032 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: FFN-site mHC F.linear(fn)
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] FFN-site pre/post/comb logits
  end
  %% source-node f27v02_n033 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: FFN-site Sigmoid pre weights
  end
  %% source-node f27v02_n034 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: FFN-site 2 × Sigmoid post weights
  end
  %% source-node f27v02_n035 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: FFN-site Softmax + Sinkhorn combine matrix
  end
  %% source-node f27v02_n036 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: FFN-site 4-stream collapse
  end
  rect rgba(245, 245, 245, 0.18)
    O-->>B: [HW] updated residual / MLP input staging
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [HW] MLP input stream
  end
  %% source-node f27v02_n037 | owner=NormCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] normalized FFN input
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [EDGE E_ACTBUF_TO_FFN] normalized FFN input
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — Router + 288 routed experts + shared expert
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] MoE weights
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] router / expert weight tiles
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Router projection request
  end
  %% source-node f27v02_n038 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] router logits
  end
  %% source-node f27v02_n039 | owner=FeedForwardCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Sigmoid router scoring
  end
  %% source-node f27v02_n040 | owner=FeedForwardCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Top-8 + renorm
  end
  %% source-node f27v02_n041 | owner=FeedForwardCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Dispatch / gather
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>B: [HW] expert token queues
  end
  loop active routed experts — 8 selected of 288
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] selected expert token batch
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Routed Expert gate_up_proj request
  end
  %% source-node f27v02_n042 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Routed Expert gate_up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] routed gate/up result
  end
  %% source-node f27v02_n043 | owner=FeedForwardCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Clamp gate≤10 / up∈[-10,10]
  end
  %% source-node f27v02_n044 | owner=FeedForwardCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: SiLU × up
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Routed Expert down_proj request
  end
  %% source-node f27v02_n045 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Routed Expert down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] routed expert output
  end
  %% source-node f27v02_n046 | owner=FeedForwardCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Expert weighting
  end
  end
  par Shared Expert
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Shared Expert gate_proj / up_proj request
  end
  %% source-node f27v02_n047 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared Expert gate_proj
  end
  %% source-node f27v02_n048 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared Expert up_proj
  end
  %% source-node f27v02_n049 | owner=FeedForwardCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Clamp gate≤10 / up∈[-10,10]
  end
  %% source-node f27v02_n050 | owner=FeedForwardCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Shared Expert SiLU × up
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Shared Expert down_proj request
  end
  %% source-node f27v02_n051 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared Expert down_proj
  end
  and Shared Expert gate
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Shared Expert gate projection request
  end
  %% source-node f27v02_n052 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_KDA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared Expert gate projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] shared gate scalar
  end
  %% source-node f27v02_n053 | owner=FeedForwardCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Shared Expert gate Sigmoid
  end
  end
  %% source-node f27v02_n054 | owner=FeedForwardCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Scatter / weighted reduce
  end
  %% source-node f27v02_n055 | owner=FeedForwardCore | class=plus | macro=OP_MHC_KDA_MOE
  rect rgba(255, 255, 255, 0.28)
    F->>F: Routed + Shared Expert sum
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>E: [HW] FFN-site sublayer output
  end
  %% source-node f27v02_n056 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_KDA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: FFN-site post × output + combᵀ × residual streams
  end
  %% source-node f27v02_n057 | owner=OutputCommitCore | class=state | macro=OP_MHC_KDA_MOE
  rect rgba(213, 232, 212, 0.24)
    O->>O: FFN-site 4-stream residual commit
  end
  rect rgba(213, 232, 212, 0.24)
    O-->>DDR: [HW] write 4 residual streams
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_MHC_KDA_MOE done
  end

```

## 27c_glm5_3_flash_dsa_moe_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 27: GLM-5.3-Flash Hybrid MoE
%% Source block-atlas file: 27_glm5_3_flash_hybrid_moe.mmd
%% Sequence file: 27c_glm5_3_flash_dsa_moe_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% New-family diagrams are architecture-to-owner mappings, not claims that the current SLX already implements these operators.
sequenceDiagram
  autonumber
  participant DDR as DDR / External Memory
  participant C as ControlCore
  participant A as ActivationReadDmaCore
  participant P as ParamReadDmaCore
  participant N as NormCore
  participant B as ActivationTileBufferCore
  participant W as WeightReadDmaCore
  participant M as SharedMatrixCore
  participant E as ElementwiseTransformCore
  participant K as KVStateCore
  participant S as SequenceCore
  participant T as TailMatrixClientCore
  participant F as FeedForwardCore
  participant O as OutputCommitCore
  Note over DDR,O: Colors follow the block atlas — yellow=input, red=params/weights, blue=MAC-heavy arithmetic, purple=non-matrix, green=state/output, white=residual, gray=hardware/control
  Note over C,O: Blue means MAC-heavy math; the participant lifeline is the actual execution owner.
  Note over C,O: Current fixed payload transfers follow manifest v6.6; future-only edges are explicitly labelled [FUTURE EDGE].

  Note over C,O: Single NoPE MLA/DSA decoder Block only; cross-layer KDA/DSA ratio is outside this file.
  Note over C,O: This DSA block uses a full/shared indexer schedule, KPool-16 compressed keys and Top-2048 selected tokens.
  Note over C,O: All Q×Kᵀ and P×V-equivalent sparse sequence arithmetic is mapped to SequenceCore; low-rank projections remain in SharedMatrixCore.
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_MHC_DSA_MOE — mHC → NoPE MLA/DSA → mHC → MoE → mHC
  end
  loop autonomous token / compressed-index / sparse-attention loop
  rect rgba(255, 242, 204, 0.24)
    A-->>DDR: [HW] AXI read request — 4 residual streams
  end
  %% source-node f27v03_n001 | owner=ActivationReadDmaCore | class=input | macro=OP_MHC_DSA_MOE
  rect rgba(255, 242, 204, 0.24)
    DDR->>A: 4 residual streams
  end
  rect rgba(245, 245, 245, 0.18)
    A-->>B: [HW] residual-stream staging
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [HW] Attention-site 4 residual streams
  end
  %% source-node f27v03_n002 | owner=NormCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: Attention-site mHC input RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] Attention-site normalized flattened 4-stream tensor
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>M: [EDGE E_ACTBUF_TO_MATRIX] resident normalized 4-stream tile
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — Attention-site mHC fn/base/scale
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] Attention-site mHC parameters
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] Attention-site mHC projection weights
  end
  %% source-node f27v03_n003 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_DSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Attention-site mHC F.linear(fn)
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Attention-site pre/post/comb logits
  end
  %% source-node f27v03_n004 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site Sigmoid pre weights
  end
  %% source-node f27v03_n005 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site 2 × Sigmoid post weights
  end
  %% source-node f27v03_n006 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site Softmax + Sinkhorn combine matrix
  end
  %% source-node f27v03_n007 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site 4-stream collapse
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>B: [FUTURE EDGE] collapsed DSA input staging
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [FUTURE EDGE] collapsed DSA input to shared Norm service
  end
  %% source-node f27v03_n008 | owner=NormCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: Input RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] normalized DSA input
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — Q/KV low-rank, indexer, O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] DSA / MLA weights
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] DSA / MLA weight tiles
  end
  %% source-node f27v03_n009 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_DSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q low-rank A
  end
  %% source-node f27v03_n010 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_DSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q low-rank B
  end
  %% source-node f27v03_n011 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_DSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: KV compression
  end
  %% source-node f27v03_n012 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_DSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: KV expansion
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>B: [HEAD/POST-NORM STAGING] Q/KV low-rank intermediates
  end
  %% source-node f27v03_n013 | owner=NormCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: Q low-rank RMSNorm
  end
  %% source-node f27v03_n014 | owner=NormCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: KV latent RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HEAD/POST-NORM SERVICE] normalized low-rank Q/KV
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>E: [HEAD/POST-NORM REPLAY] normalized low-rank Q/KV
  end
  %% source-node f27v03_n015 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Split Q/K/V — NoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] latent KV commit
  end
  %% source-node f27v03_n016 | owner=KVStateCore | class=state | macro=OP_MHC_DSA_MOE
  rect rgba(213, 232, 212, 0.24)
    K->>K: Latent KV cache
  end
  %% source-node f27v03_n017 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_DSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: DSA Indexer Q/K projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>S: [HW] indexer Q/K vectors
  end
  %% source-node f27v03_n018 | owner=SequenceCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    S->>S: KPool-16 compressed key mean
  end
  alt Indexer mode = full
  %% source-node f27v03_n019 | owner=SequenceCore | class=mac | macro=OP_MHC_DSA_MOE
  rect rgba(218, 232, 252, 0.24)
    S->>S: Indexer Q × pooled Kᵀ
  end
  %% source-node f27v03_n020 | owner=SequenceCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    S->>S: ReLU + index-head reduce
  end
  %% source-node f27v03_n021 | owner=SequenceCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    S->>S: Top-2048 select
  end
  else Indexer mode = shared
  %% source-node f27v03_n022 | owner=KVStateCore | class=state | macro=OP_MHC_DSA_MOE
  rect rgba(213, 232, 212, 0.24)
    K->>K: Reuse previous full-layer Top-k selection
  end
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>K: [HW] selected indices
  end
  %% source-node f27v03_n023 | owner=KVStateCore | class=state | macro=OP_MHC_DSA_MOE
  rect rgba(213, 232, 212, 0.24)
    K->>K: Selected latent/token gather + incomplete tail
  end
  rect rgba(245, 245, 245, 0.18)
    K-->>S: [HW] selected latent K/V
  end
  %% source-node f27v03_n024 | owner=SequenceCore | class=mac | macro=OP_MHC_DSA_MOE
  rect rgba(218, 232, 252, 0.24)
    S->>S: Selected sparse MLA Q × Kᵀ
  end
  %% source-node f27v03_n025 | owner=SequenceCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f27v03_n026 | owner=SequenceCore | class=mac | macro=OP_MHC_DSA_MOE
  rect rgba(218, 232, 252, 0.24)
    S->>S: Sparse P × V / Online O recurrence (selected V)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] sparse MLA output
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>M: [HW] O Proj request
  end
  %% source-node f27v03_n027 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_DSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: O Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>T: [EDGE E_MATRIX_TO_TAIL] O Proj result tile
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>O: [EDGE E_MATRIX_TO_COMMIT] OProj result stream128
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>E: [HW] Attention-site sublayer output
  end
  %% source-node f27v03_n028 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: Attention-site post × output + combᵀ × residual streams
  end
  %% source-node f27v03_n029 | owner=OutputCommitCore | class=state | macro=OP_MHC_DSA_MOE
  rect rgba(213, 232, 212, 0.24)
    O->>O: Attention-site 4-stream residual commit
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [HW] FFN-site 4 residual streams
  end
  %% source-node f27v03_n030 | owner=NormCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: FFN-site mHC input RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] FFN-site normalized flattened 4-stream tensor
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>M: [EDGE E_ACTBUF_TO_MATRIX] resident normalized 4-stream tile
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — FFN-site mHC fn/base/scale
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] FFN-site mHC parameters
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] FFN-site mHC projection weights
  end
  %% source-node f27v03_n031 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_DSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: FFN-site mHC F.linear(fn)
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] FFN-site pre/post/comb logits
  end
  %% source-node f27v03_n032 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: FFN-site Sigmoid pre weights
  end
  %% source-node f27v03_n033 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: FFN-site 2 × Sigmoid post weights
  end
  %% source-node f27v03_n034 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: FFN-site Softmax + Sinkhorn combine matrix
  end
  %% source-node f27v03_n035 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: FFN-site 4-stream collapse
  end
  rect rgba(245, 245, 245, 0.18)
    O-->>B: [HW] updated residual / MLP input staging
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>N: [HW] MLP input stream
  end
  %% source-node f27v03_n036 | owner=NormCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] normalized FFN input
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [EDGE E_ACTBUF_TO_FFN] normalized FFN input
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>DDR: [HW] weight read — Router + 288 routed experts + shared expert
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] MoE weights
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] router / expert weight tiles
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Router projection request
  end
  %% source-node f27v03_n037 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_DSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] router logits
  end
  %% source-node f27v03_n038 | owner=FeedForwardCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Sigmoid router scoring
  end
  %% source-node f27v03_n039 | owner=FeedForwardCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Top-8 + renorm
  end
  %% source-node f27v03_n040 | owner=FeedForwardCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Dispatch / gather
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>B: [HW] expert token queues
  end
  loop active routed experts — 8 selected of 288
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] selected expert token batch
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Routed Expert gate_up_proj request
  end
  %% source-node f27v03_n041 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_DSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Routed Expert gate_up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] routed gate/up result
  end
  %% source-node f27v03_n042 | owner=FeedForwardCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Clamp gate≤10 / up∈[-10,10]
  end
  %% source-node f27v03_n043 | owner=FeedForwardCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: SiLU × up
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Routed Expert down_proj request
  end
  %% source-node f27v03_n044 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_DSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Routed Expert down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] routed expert output
  end
  %% source-node f27v03_n045 | owner=FeedForwardCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Expert weighting
  end
  end
  par Shared Expert
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Shared Expert gate_proj / up_proj request
  end
  %% source-node f27v03_n046 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_DSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared Expert gate_proj
  end
  %% source-node f27v03_n047 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_DSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared Expert up_proj
  end
  %% source-node f27v03_n048 | owner=FeedForwardCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Clamp gate≤10 / up∈[-10,10]
  end
  %% source-node f27v03_n049 | owner=FeedForwardCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Shared Expert SiLU × up
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Shared Expert down_proj request
  end
  %% source-node f27v03_n050 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_DSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared Expert down_proj
  end
  and Shared Expert gate
  rect rgba(245, 245, 245, 0.18)
    F-->>M: [HW] Shared Expert gate projection request
  end
  %% source-node f27v03_n051 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_DSA_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared Expert gate projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] shared gate scalar
  end
  %% source-node f27v03_n052 | owner=FeedForwardCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Shared Expert gate Sigmoid
  end
  end
  %% source-node f27v03_n053 | owner=FeedForwardCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Scatter / weighted reduce
  end
  %% source-node f27v03_n054 | owner=FeedForwardCore | class=plus | macro=OP_MHC_DSA_MOE
  rect rgba(255, 255, 255, 0.28)
    F->>F: Routed + Shared Expert sum
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>E: [HW] FFN-site sublayer output
  end
  %% source-node f27v03_n055 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_DSA_MOE
  rect rgba(225, 213, 231, 0.24)
    E->>E: FFN-site post × output + combᵀ × residual streams
  end
  %% source-node f27v03_n056 | owner=OutputCommitCore | class=state | macro=OP_MHC_DSA_MOE
  rect rgba(213, 232, 212, 0.24)
    O->>O: FFN-site 4-stream residual commit
  end
  rect rgba(213, 232, 212, 0.24)
    O-->>DDR: [HW] write 4 residual streams
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_MHC_DSA_MOE done
  end

```

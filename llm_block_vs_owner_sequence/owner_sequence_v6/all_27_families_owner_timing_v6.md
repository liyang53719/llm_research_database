# 27 个架构家族 / 32 个 Block 变体的 13-Owner 时序图 v6

- 13-owner review: `381d85219d6feec9b10345e2800ac74d4185e5a0` / SLX `94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945`
- current main: `0db7eed1e80610083ecc40b1c5982f60db5bda40` / SLX `33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379`
- owner manifest: `6.6`

## 01_qwen2_qwen2_5_dense_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 1: Qwen2 / Qwen2.5 Dense
%% Source block-atlas file: 01_qwen2_qwen2_5_dense.mmd
%% Sequence file: 01_qwen2_qwen2_5_dense_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
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
  Note over C,O: Colors follow the block atlas — yellow=input, red=params/weights, blue=MAC-heavy arithmetic, purple=non-matrix, green=state/output, white=residual, gray=hardware/control
  Note over C,O: Blue means MAC-heavy math; the participant lifeline is the actual execution owner.
  Note over C,O: Current fixed payload transfers follow manifest v6.6; future-only edges are explicitly labelled [FUTURE EDGE].

  Note over C,O: OP_K_PROJ — DDR read → RMSNorm 1 → K Proj → RoPE → K cache → DDR write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_K_PROJ
  end
  loop OP_K_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — K-pass activation / residual
  end
  %% source-node f01v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_K_PROJ
  rect rgba(255, 242, 204, 0.24)
    DDR->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm gamma / K bias / RoPE profile
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm gamma / K bias / RoPE profile
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm gamma / K bias / RoPE profile
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>M: [HW] RMSNorm gamma / K bias / RoPE profile
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm gamma / K bias / RoPE profile
  end
  %% source-node f01v01_n020 | owner=NormCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] normalized 32-lane stream
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident 128-lane tile
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f01v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_K_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: K Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] K projection stream
  end
  %% source-node f01v01_n025 | owner=ElementwiseTransformCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] transformed K stream
  end
  %% source-node f01v01_n027 | owner=KVStateCore | class=state | macro=OP_K_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: K cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] K-cache write
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_K_PROJ done
  end
  Note over C,O: OP_V_PROJ — DDR read → RMSNorm 1 replay → V Proj → V cache → DDR write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_V_PROJ
  end
  loop OP_V_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — V-pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] V-pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm gamma / V bias
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm gamma / V bias
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm gamma / V bias
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>M: [HW] RMSNorm gamma / V bias
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=V
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] normalized 32-lane stream
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident 128-lane tile
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f01v01_n024 | owner=SharedMatrixCore | class=mac | macro=OP_V_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: V Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V projection stream → projection-result dispatch
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
  end
  %% source-node f01v01_n028 | owner=KVStateCore | class=state | macro=OP_V_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: V cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] V-cache write
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_V_PROJ done
  end
  Note over C,O: OP_Q_ATTN_OPROJ — Q projection + RoPE → tiled attention → OProj → residual DDR commit
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_Q_ATTN_OPROJ
  end
  loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile phase
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — Q-pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] Q-pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm gamma / Q bias / RoPE profile
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm gamma / Q bias / RoPE profile
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm gamma / Q bias / RoPE profile
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>M: [HW] RMSNorm gamma / Q bias / RoPE profile
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm gamma / Q bias / RoPE profile
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=Q
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] normalized 32-lane stream
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident 128-lane tile
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f01v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Q projection stream
  end
  %% source-node f01v01_n026 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>S: [HW] Q tile write / query stream
  end
  end
  Note over C,O: Same macro-op, attention/OProj phase. Q projection may resume between OProj grants; SharedMatrix owner remains mutually exclusive.
  loop OP_Q_ATTN_OPROJ Q-block / KV-tile phase
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] K/V history read request
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] K/V history tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] independent K/V response channels
  end
  %% source-node f01v01_n029 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: K head repeat ×6
  end
  %% source-node f01v01_n030 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: V head repeat ×6
  end
  %% source-node f01v01_n031 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q × Kᵀ
  end
  %% source-node f01v01_n032 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f01v01_n033 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] finalized attention O block + q-block/token/head tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] OProj request / urgent / grant
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f01v01_n034 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: O Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>T: [EDGE E_MATRIX_TO_TAIL] tagged OProj result tile
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>O: [EDGE E_MATRIX_TO_COMMIT] OProj result stream128
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>O: [EDGE E_TAIL_TO_COMMIT] OProj commit metadata / token-layout control
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f01v01_n035 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f01v01_n036 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    O->>DDR: X + Attention
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_Q_ATTN_OPROJ done
  end
  Note over C,O: OP_FFN — DDR read → RMSNorm 2 → gate/up → SiLU×up → down → residual DDR commit
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_FFN
  end
  loop OP_FFN token/chunk/weight-tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-attention residual / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-attention residual / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 2 gamma / FFN bias profile
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 2 gamma / FFN bias profile
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 2 gamma / FFN bias profile
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>M: [HW] RMSNorm 2 gamma / FFN bias profile
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] RMSNorm 2 gamma / FFN bias profile
  end
  %% source-node f01v01_n037 | owner=NormCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] normalized FFN stream
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] resident FFN tile
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f01v01_n039 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M->>M: [HW] gate tile held locally for fused SwiGLU
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f01v01_n040 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M->>M: [HW] up tile held locally for fused SwiGLU
  end
  %% source-node f01v01_n041 | owner=SharedMatrixCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    M->>M: SiLU (current fused MlpSiluLane32Core)
  end
  %% source-node f01v01_n042 | owner=SharedMatrixCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    M->>M: Elementwise gate (current fused Gate×Up)
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [EDGE E_MATRIX_TO_FFN] fused activation ready / down-phase event
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f01v01_n043 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj partial/result
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] FFN final vector / residual input
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f01v01_n044 | owner=OutputCommitCore | class=plus | macro=OP_FFN
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f01v01_n045 | owner=OutputCommitCore | class=output | macro=OP_FFN
  rect rgba(213, 232, 212, 0.24)
    O->>DDR: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_FFN done
  end

```

## 02_qwen3_dense_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 2: Qwen3 Dense
%% Source block-atlas file: 02_qwen3_dense.mmd
%% Sequence file: 02_qwen3_dense_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: Variant 1 — Dense decoder block with Q/K head RMSNorm
  Note over C,O: OP_K_PROJ — RMSNorm 1 → K Proj → K Head RMSNorm → RoPE → K cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_K_PROJ
  end
  loop OP_K_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — K pass activation / residual
  end
  %% source-node f02v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_K_PROJ
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% source-node f02v01_n020 | owner=NormCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — K pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f02v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_K_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: K Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>B: [HEAD/POST-NORM STAGING] K Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [HEAD/POST-NORM SERVICE] K Head RMSNorm request / 32-lane replay
  end
  %% source-node f02v01_n025 | owner=NormCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: K Head RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HEAD/POST-NORM SERVICE] K Head RMSNorm output response
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
  end
  %% source-node f02v01_n027 | owner=ElementwiseTransformCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] RoPE output
  end
  %% source-node f02v01_n029 | owner=KVStateCore | class=state | macro=OP_K_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: K cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write K cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_K_PROJ done
  end
  Note over C,O: OP_V_PROJ — RMSNorm 1 → V Proj → V cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_V_PROJ
  end
  loop OP_V_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=V pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — V pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — V pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f02v01_n024 | owner=SharedMatrixCore | class=mac | macro=OP_V_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: V Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V Proj result → projection-result dispatch
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
  end
  %% source-node f02v01_n030 | owner=KVStateCore | class=state | macro=OP_V_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: V cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write V cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_V_PROJ done
  end
  Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: RMSNorm 1 → Q Proj → Q Head RMSNorm → RoPE
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_Q_ATTN_OPROJ
  end
  loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=Q pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — Q pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — Q pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f02v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>B: [HEAD/POST-NORM STAGING] Q Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [HEAD/POST-NORM SERVICE] Q Head RMSNorm request / 32-lane replay
  end
  %% source-node f02v01_n026 | owner=NormCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: Q Head RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HEAD/POST-NORM SERVICE] Q Head RMSNorm output response
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
  end
  %% source-node f02v01_n028 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>S: [HW] RoPE output
  end
  rect rgba(213, 232, 212, 0.24)
    E-->>S: [HW] commit Q tile / query stream
  end
  rect rgba(213, 232, 212, 0.24)
    S->>S: [HW] Q tile resident for subsequent sequence op
  end
  end
  Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → O Proj → residual commit
  loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read K/V state / history
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] K/V state tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] K/V state response
  end
  %% source-node f02v01_n031 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: K head repeat ×2
  end
  %% source-node f02v01_n032 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: V head repeat ×2
  end
  %% source-node f02v01_n033 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q × Kᵀ
  end
  %% source-node f02v01_n034 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f02v01_n035 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] sequence output block + tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] tail projection request / grant
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f02v01_n036 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
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
    T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f02v01_n037 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f02v01_n038 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    O->>O: X + Attention
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_Q_ATTN_OPROJ done
  end
  Note over C,O: OP_FFN — DDR read → RMSNorm 2 → dense FFN → residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_FFN
  end
  loop OP_FFN token/chunk/weight-tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] RMSNorm 2 / activation parameters
  end
  %% source-node f02v01_n039 | owner=NormCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 2 output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] FFN resident activation tile
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f02v01_n041 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M->>M: [HW] gate tile held locally for fused SwiGLU
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f02v01_n042 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M->>M: [HW] up tile held locally for fused SwiGLU
  end
  %% source-node f02v01_n043 | owner=SharedMatrixCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    M->>M: SiLU (current fused MlpSiluLane32Core)
  end
  %% source-node f02v01_n044 | owner=SharedMatrixCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    M->>M: Elementwise gate (current fused Gate×Up)
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [EDGE E_MATRIX_TO_FFN] fused activation ready / down-phase event
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f02v01_n045 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] FFN result / residual input
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f02v01_n046 | owner=OutputCommitCore | class=plus | macro=OP_FFN
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f02v01_n047 | owner=OutputCommitCore | class=output | macro=OP_FFN
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_FFN done
  end

```

## 03_llama_yi_smollm_dense_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 3: Llama / Yi / SmolLM Dense
%% Source block-atlas file: 03_llama_yi_smollm_dense.mmd
%% Sequence file: 03_llama_yi_smollm_dense_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: Variant 1 — Pre-norm GQA / SwiGLU block
  Note over C,O: OP_K_PROJ — RMSNorm 1 → K Proj → RoPE → K cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_K_PROJ
  end
  loop OP_K_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — K pass activation / residual
  end
  %% source-node f03v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_K_PROJ
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% source-node f03v01_n020 | owner=NormCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — K pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f03v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_K_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: K Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] K Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for RoPE
  end
  %% source-node f03v01_n025 | owner=ElementwiseTransformCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] RoPE output
  end
  %% source-node f03v01_n027 | owner=KVStateCore | class=state | macro=OP_K_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: K cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write K cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_K_PROJ done
  end
  Note over C,O: OP_V_PROJ — RMSNorm 1 → V Proj → V cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_V_PROJ
  end
  loop OP_V_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=V pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — V pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — V pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f03v01_n024 | owner=SharedMatrixCore | class=mac | macro=OP_V_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: V Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V Proj result → projection-result dispatch
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
  end
  %% source-node f03v01_n028 | owner=KVStateCore | class=state | macro=OP_V_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: V cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write V cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_V_PROJ done
  end
  Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: RMSNorm 1 → Q Proj → RoPE
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_Q_ATTN_OPROJ
  end
  loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=Q pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — Q pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — Q pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f03v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Q Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for RoPE
  end
  %% source-node f03v01_n026 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>S: [HW] RoPE output
  end
  rect rgba(213, 232, 212, 0.24)
    E-->>S: [HW] commit Q tile / query stream
  end
  rect rgba(213, 232, 212, 0.24)
    S->>S: [HW] Q tile resident for subsequent sequence op
  end
  end
  Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → O Proj → residual commit
  loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read K/V state / history
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] K/V state tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] K/V state response
  end
  %% source-node f03v01_n029 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: K head repeat ×4
  end
  %% source-node f03v01_n030 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: V head repeat ×4
  end
  %% source-node f03v01_n031 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q × Kᵀ
  end
  %% source-node f03v01_n032 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f03v01_n033 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] sequence output block + tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] tail projection request / grant
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f03v01_n034 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
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
    T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f03v01_n035 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f03v01_n036 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    O->>O: X + Attention
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_Q_ATTN_OPROJ done
  end
  Note over C,O: OP_FFN — DDR read → RMSNorm 2 → dense FFN → residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_FFN
  end
  loop OP_FFN token/chunk/weight-tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] RMSNorm 2 / activation parameters
  end
  %% source-node f03v01_n037 | owner=NormCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 2 output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] FFN resident activation tile
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f03v01_n039 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M->>M: [HW] gate tile held locally for fused SwiGLU
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f03v01_n040 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M->>M: [HW] up tile held locally for fused SwiGLU
  end
  %% source-node f03v01_n041 | owner=SharedMatrixCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    M->>M: SiLU (current fused MlpSiluLane32Core)
  end
  %% source-node f03v01_n042 | owner=SharedMatrixCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    M->>M: Elementwise gate (current fused Gate×Up)
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [EDGE E_MATRIX_TO_FFN] fused activation ready / down-phase event
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f03v01_n043 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] FFN result / residual input
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f03v01_n044 | owner=OutputCommitCore | class=plus | macro=OP_FFN
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f03v01_n045 | owner=OutputCommitCore | class=output | macro=OP_FFN
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_FFN done
  end

```

## 04a_qwen3_5_qwen3_6_hybrid_moe_gdn_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 4: Qwen3.5 / Qwen3.6 Hybrid MoE
%% Source block-atlas file: 04_qwen3_5_qwen3_6_hybrid_moe.mmd
%% Sequence file: 04a_qwen3_5_qwen3_6_hybrid_moe_gdn_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Split variant a: GDN + routed/shared MoE block
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: OP_GDN_MIXER — DDR read → projections / vector transforms → Chunk Gated Delta Rule → recurrent-state write → out_proj / residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_GDN_MIXER
  end
  loop OP_GDN_MIXER token/chunk/state loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — GDN block input
  end
  %% source-node f04v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_GDN_MIXER
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm / beta / decay / gate parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm / beta / decay / gate parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm / beta / decay / gate parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm / beta / decay / gate parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [EDGE E_PARAM_GDN_STATIC_TO_TRANSFORM] RoPE/GDN static parameters
  end
  %% source-node f04v01_n020 | owner=NormCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] GDN projection input tile
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] input tile for in_proj_qkv
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — in_proj_qkv
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — in_proj_qkv
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_GDN_MIXER
  rect rgba(218, 232, 252, 0.24)
    M->>M: in_proj_qkv
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] in_proj_qkv result
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] input tile for in_proj_z
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — in_proj_z
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — in_proj_z
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_GDN_MIXER
  rect rgba(218, 232, 252, 0.24)
    M->>M: in_proj_z
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] in_proj_z result
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] input tile for in_proj_a
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — in_proj_a
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — in_proj_a
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v01_n024 | owner=SharedMatrixCore | class=mac | macro=OP_GDN_MIXER
  rect rgba(218, 232, 252, 0.24)
    M->>M: in_proj_a
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] in_proj_a result
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] input tile for in_proj_b
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — in_proj_b
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — in_proj_b
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v01_n025 | owner=SharedMatrixCore | class=mac | macro=OP_GDN_MIXER
  rect rgba(218, 232, 252, 0.24)
    M->>M: in_proj_b
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] in_proj_b result
  end
  %% source-node f04v01_n026 | owner=SharedMatrixCore | class=other | macro=OP_GDN_MIXER
  rect rgba(213, 232, 212, 0.24)
    K-->>M: [EDGE E_STATE_GDN_CONV_HISTORY_TO_MATRIX] conv-history response
  end
  rect rgba(225, 213, 231, 0.24)
    E->>M: [HW] matrix service request — Depthwise Conv1D
  end
  rect rgba(225, 213, 231, 0.24)
    M->>M: Depthwise Conv1D
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Depthwise Conv1D result
  end
  rect rgba(213, 232, 212, 0.24)
    M-->>K: [EDGE E_MATRIX_GDN_CONV_HISTORY_TO_STATE] updated conv-history commit
  end
  %% source-node f04v01_n027 | owner=ElementwiseTransformCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    E->>E: SiLU
  end
  %% source-node f04v01_n028 | owner=ElementwiseTransformCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    E->>E: Split Q / K / V
  end
  %% source-node f04v01_n029 | owner=ElementwiseTransformCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    E->>E: Q reshape
  end
  %% source-node f04v01_n030 | owner=ElementwiseTransformCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    E->>E: K reshape
  end
  %% source-node f04v01_n031 | owner=ElementwiseTransformCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    E->>E: V reshape
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>B: [EDGE E_TRANSFORM_GDN_HEAD_TO_ACTBUF] Q/K/V head tiles
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [GDN HEAD-NORM SERVICE] Q/K L2Norm request
  end

  %% source-node f04v01_n032 | owner=NormCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    N->>N: Q L2Norm (shared Norm service)
  end
  %% source-node f04v01_n033 | owner=NormCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    N->>N: K L2Norm (shared Norm service)
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [GDN HEAD-NORM SERVICE] normalized Q/K response
  end
  %% source-node f04v01_n034 | owner=ElementwiseTransformCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    E->>E: Decay preactivation
  end
  %% source-node f04v01_n035 | owner=ElementwiseTransformCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    E->>E: Decay factor
  end
  %% source-node f04v01_n036 | owner=ElementwiseTransformCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    E->>E: Update gate
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>B: [EDGE E_TRANSFORM_GDN_HEAD_TO_ACTBUF] Z/A/B + decay/update streams
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>S: [EDGE E_ACTBUF_GDN_VZAB_TO_SEQUENCE] normalized Q/K + V/Z/A/B tiles
  end
  %% source-node f04v01_n037 | owner=SequenceCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    S->>S: Chunk partition
  end
  %% source-node f04v01_n038 | owner=SequenceCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    S->>S: Decay matrix Γ
  end
  %% source-node f04v01_n039 | owner=SequenceCore | class=mac | macro=OP_GDN_MIXER
  rect rgba(218, 232, 252, 0.24)
    S->>S: K Kᵀ
  end
  %% source-node f04v01_n040 | owner=SequenceCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    S->>S: Build strict-lower L
  end
  %% source-node f04v01_n041 | owner=SequenceCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    S->>S: Triangular solve
  end
  %% source-node f04v01_n042 | owner=SequenceCore | class=mac | macro=OP_GDN_MIXER
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q Kᵀ
  end
  %% source-node f04v01_n043 | owner=SequenceCore | class=mac | macro=OP_GDN_MIXER
  rect rgba(218, 232, 252, 0.24)
    S->>S: Intra-chunk output
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read recurrent state S
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] recurrent state S tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] recurrent state response
  end
  %% source-node f04v01_n044 | owner=SequenceCore | class=mac | macro=OP_GDN_MIXER
  rect rgba(218, 232, 252, 0.24)
    S->>S: State read
  end
  %% source-node f04v01_n045 | owner=SequenceCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    S->>S: Output combine
  end
  %% source-node f04v01_n046 | owner=SequenceCore | class=mac | macro=OP_GDN_MIXER
  rect rgba(218, 232, 252, 0.24)
    S->>S: Kᵀ U
  end
  %% source-node f04v01_n047 | owner=SequenceCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    S->>S: State decay
  end
  %% source-node f04v01_n048 | owner=SequenceCore | class=plus | macro=OP_GDN_MIXER
  rect rgba(255, 255, 255, 0.28)
    S->>S: +
  end
  %% source-node f04v01_n049 | owner=KVStateCore | class=state | macro=OP_GDN_MIXER
  rect rgba(213, 232, 212, 0.24)
    S-->>K: [GDN STATE COMMIT] updated recurrent state S
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write Recurrent state S
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>N: [EDGE E_SEQUENCE_GDN_NORM_REQUEST] GDN output / gated-norm request
  end
  %% source-node f04v01_n050 | owner=NormCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNormGated
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>S: [EDGE E_NORM_GDN_RESPONSE_TO_SEQUENCE] normalized/gated GDN response
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [EDGE E_SEQUENCE_TO_TAIL] gated GDN output + tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] GDN tail projection request
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for out_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — out_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — out_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v01_n051 | owner=SharedMatrixCore | class=mac | macro=OP_GDN_MIXER
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
    T-->>O: [EDGE E_TAIL_TO_COMMIT] GDN tail commit metadata
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f04v01_n052 | owner=OutputCommitCore | class=plus | macro=OP_GDN_MIXER
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f04v01_n053 | owner=OutputCommitCore | class=output | macro=OP_GDN_MIXER
  rect rgba(213, 232, 212, 0.24)
    O->>O: X + GDN
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_GDN_MIXER done
  end
  Note over C,O: OP_MOE — DDR read → RMSNorm 2 → Router / Top-k → experts → merge / residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_MOE
  end
  loop OP_MOE token batch / expert group loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-sequence MoE input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-sequence MoE input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] RMSNorm 2 / router / expert parameters
  end
  %% source-node f04v01_n054 | owner=NormCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 2 output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] router input / expert queue source
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v01_n056 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] Router projection result
  end
  %% source-node f04v01_n057 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Router scoring
  end
  %% source-node f04v01_n058 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Top-8 + renorm
  end
  %% source-node f04v01_n059 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Dispatch / gather
  end
  rect rgba(213, 232, 212, 0.24)
    F->>B: [HW] expert queue / token grouping
  end
  rect rgba(213, 232, 212, 0.24)
    B-->>F: [HW] grouped expert activation
  end
  loop selected routed experts / grouped tokens
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v01_n060 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] gate_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v01_n061 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] up_proj result
  end
  %% source-node f04v01_n062 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: SiLU
  end
  %% source-node f04v01_n063 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Elementwise gate
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v01_n064 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  %% source-node f04v01_n065 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Expert weighting
  end
  %% source-node f04v01_n066 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Scatter / weighted reduce
  end
  end
  Note over F,O: Shared expert path executes for every token
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v01_n067 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] gate_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v01_n068 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] up_proj result
  end
  %% source-node f04v01_n069 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: SiLU
  end
  %% source-node f04v01_n070 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Elementwise gate
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v01_n071 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — Shared gate projection
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for Shared gate projection
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Shared gate projection
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Shared gate projection
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v01_n072 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared gate projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] Shared gate projection result
  end
  %% source-node f04v01_n073 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Sigmoid
  end
  %% source-node f04v01_n074 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Shared gating
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] expert output stream(s)
  end
  %% source-node f04v01_n075 | owner=OutputCommitCore | class=plus | macro=OP_MOE
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f04v01_n076 | owner=OutputCommitCore | class=plus | macro=OP_MOE
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f04v01_n077 | owner=OutputCommitCore | class=output | macro=OP_MOE
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_MOE done
  end

```

## 04b_qwen3_5_qwen3_6_hybrid_moe_full_attention_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 4: Qwen3.5 / Qwen3.6 Hybrid MoE
%% Source block-atlas file: 04_qwen3_5_qwen3_6_hybrid_moe.mmd
%% Sequence file: 04b_qwen3_5_qwen3_6_hybrid_moe_full_attention_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Split variant b: Gated full-attention + routed/shared MoE block
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: OP_K_PROJ — RMSNorm 1 → K Proj → K Head RMSNorm → Partial RoPE → K cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_K_PROJ
  end
  loop OP_K_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — K pass activation / residual
  end
  %% source-node f04v02_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_K_PROJ
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% source-node f04v02_n020 | owner=NormCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — K pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v02_n022 | owner=SharedMatrixCore | class=mac | macro=OP_K_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: K Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>B: [HEAD/POST-NORM STAGING] K Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [HEAD/POST-NORM SERVICE] K Head RMSNorm request / 32-lane replay
  end
  %% source-node f04v02_n025 | owner=NormCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: K Head RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HEAD/POST-NORM SERVICE] K Head RMSNorm output response
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
  end
  %% source-node f04v02_n027 | owner=ElementwiseTransformCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: Partial RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] Partial RoPE output
  end
  %% source-node f04v02_n029 | owner=KVStateCore | class=state | macro=OP_K_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: K cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write K cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_K_PROJ done
  end
  Note over C,O: OP_V_PROJ — RMSNorm 1 → V Proj → V cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_V_PROJ
  end
  loop OP_V_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=V pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — V pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — V pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v02_n024 | owner=SharedMatrixCore | class=mac | macro=OP_V_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: V Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V Proj result → projection-result dispatch
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
  end
  %% source-node f04v02_n030 | owner=KVStateCore | class=state | macro=OP_V_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: V cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write V cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_V_PROJ done
  end
  Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: RMSNorm 1 → Q Proj + gate → Q Head RMSNorm → Partial RoPE
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_Q_ATTN_OPROJ
  end
  loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=Q pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — Q pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — Q pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q Proj + gate
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q Proj + gate
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v02_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q Proj + gate
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>T: [EDGE E_MATRIX_TO_TAIL_Q_GATE_SPLIT] Q projection + gate split stream
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>B: [EDGE E_TAIL_TO_ACTBUF_Q_QUERY] Q query stream to HeadNormTileBuffer
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>S: [EDGE E_TAIL_TO_SEQUENCE_Q_GATE] Q output-gate stream to AttentionOutputGateCore
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [HEAD-NORM SERVICE] Q Head RMSNorm request / replay
  end
  %% source-node f04v02_n026 | owner=NormCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: Q Head RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HEAD/POST-NORM SERVICE] Q Head RMSNorm output response
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
  end
  %% source-node f04v02_n028 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: Partial RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>S: [HW] Partial RoPE output
  end
  rect rgba(213, 232, 212, 0.24)
    E-->>S: [HW] commit Q tile / query stream
  end
  rect rgba(213, 232, 212, 0.24)
    S->>S: [HW] Q tile resident for subsequent sequence op
  end
  end
Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → O Proj → residual commit
loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read K/V state / history
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] K/V state tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] K/V state response
  end
  %% source-node f04v02_n031 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: K head repeat ×8
  end
  %% source-node f04v02_n032 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: V head repeat ×8
  end
  %% source-node f04v02_n033 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q × Kᵀ
  end
  %% source-node f04v02_n034 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f04v02_n035 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  %% source-node f04v02_n036 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Q-gate sigmoid (AttentionOutputGateCore)
  end
  %% source-node f04v02_n037 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Context gating (scale final O)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [EDGE E_SEQUENCE_TO_TAIL] gated attention context + tags
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] sequence output block + tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] tail projection request / grant
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v02_n038 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
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
    T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f04v02_n039 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f04v02_n040 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    O->>O: X + Attention
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_Q_ATTN_OPROJ done
  end
  Note over C,O: OP_MOE — DDR read → RMSNorm 2 → Router / Top-k → experts → merge / residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_MOE
  end
  loop OP_MOE token batch / expert group loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-sequence MoE input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-sequence MoE input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] RMSNorm 2 / router / expert parameters
  end
  %% source-node f04v02_n041 | owner=NormCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 2 output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] router input / expert queue source
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v02_n043 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] Router projection result
  end
  %% source-node f04v02_n044 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Router scoring
  end
  %% source-node f04v02_n045 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Top-8 + renorm
  end
  %% source-node f04v02_n046 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Dispatch / gather
  end
  rect rgba(213, 232, 212, 0.24)
    F->>B: [HW] expert queue / token grouping
  end
  rect rgba(213, 232, 212, 0.24)
    B-->>F: [HW] grouped expert activation
  end
  loop selected routed experts / grouped tokens
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v02_n047 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] gate_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v02_n048 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] up_proj result
  end
  %% source-node f04v02_n049 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: SiLU
  end
  %% source-node f04v02_n050 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Elementwise gate
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v02_n051 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  %% source-node f04v02_n052 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Expert weighting
  end
  %% source-node f04v02_n053 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Scatter / weighted reduce
  end
  end
  Note over F,O: Shared expert path executes for every token
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v02_n054 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] gate_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v02_n055 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] up_proj result
  end
  %% source-node f04v02_n056 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: SiLU
  end
  %% source-node f04v02_n057 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Elementwise gate
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v02_n058 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — Shared gate projection
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for Shared gate projection
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Shared gate projection
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Shared gate projection
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f04v02_n059 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared gate projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] Shared gate projection result
  end
  %% source-node f04v02_n060 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Sigmoid
  end
  %% source-node f04v02_n061 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Shared gating
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] expert output stream(s)
  end
  %% source-node f04v02_n062 | owner=OutputCommitCore | class=plus | macro=OP_MOE
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f04v02_n063 | owner=OutputCommitCore | class=plus | macro=OP_MOE
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f04v02_n064 | owner=OutputCommitCore | class=output | macro=OP_MOE
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_MOE done
  end

```

## 05_qwen3_moe_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 5: Qwen3 MoE
%% Source block-atlas file: 05_qwen3_moe.mmd
%% Sequence file: 05_qwen3_moe_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: Variant 1 — Full GQA + routed MoE block
  Note over C,O: OP_K_PROJ — RMSNorm 1 → K Proj → K Head RMSNorm → RoPE → K cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_K_PROJ
  end
  loop OP_K_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — K pass activation / residual
  end
  %% source-node f05v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_K_PROJ
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% source-node f05v01_n020 | owner=NormCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — K pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f05v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_K_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: K Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>B: [HEAD/POST-NORM STAGING] K Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [HEAD/POST-NORM SERVICE] K Head RMSNorm request / 32-lane replay
  end
  %% source-node f05v01_n025 | owner=NormCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: K Head RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HEAD/POST-NORM SERVICE] K Head RMSNorm output response
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
  end
  %% source-node f05v01_n027 | owner=ElementwiseTransformCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] RoPE output
  end
  %% source-node f05v01_n029 | owner=KVStateCore | class=state | macro=OP_K_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: K cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write K cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_K_PROJ done
  end
  Note over C,O: OP_V_PROJ — RMSNorm 1 → V Proj → V cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_V_PROJ
  end
  loop OP_V_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=V pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — V pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — V pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f05v01_n024 | owner=SharedMatrixCore | class=mac | macro=OP_V_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: V Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V Proj result → projection-result dispatch
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
  end
  %% source-node f05v01_n030 | owner=KVStateCore | class=state | macro=OP_V_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: V cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write V cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_V_PROJ done
  end
  Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: RMSNorm 1 → Q Proj → Q Head RMSNorm → RoPE
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_Q_ATTN_OPROJ
  end
  loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=Q pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — Q pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — Q pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f05v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>B: [HEAD/POST-NORM STAGING] Q Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [HEAD/POST-NORM SERVICE] Q Head RMSNorm request / 32-lane replay
  end
  %% source-node f05v01_n026 | owner=NormCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: Q Head RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HEAD/POST-NORM SERVICE] Q Head RMSNorm output response
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
  end
  %% source-node f05v01_n028 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>S: [HW] RoPE output
  end
  rect rgba(213, 232, 212, 0.24)
    E-->>S: [HW] commit Q tile / query stream
  end
  rect rgba(213, 232, 212, 0.24)
    S->>S: [HW] Q tile resident for subsequent sequence op
  end
  end
  Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → O Proj → residual commit
  loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read K/V state / history
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] K/V state tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] K/V state response
  end
  %% source-node f05v01_n031 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: K head repeat ×2
  end
  %% source-node f05v01_n032 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: V head repeat ×2
  end
  %% source-node f05v01_n033 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q × Kᵀ
  end
  %% source-node f05v01_n034 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f05v01_n035 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] sequence output block + tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] tail projection request / grant
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f05v01_n036 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
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
    T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f05v01_n037 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f05v01_n038 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    O->>O: X + Attention
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_Q_ATTN_OPROJ done
  end
  Note over C,O: OP_MOE — DDR read → RMSNorm 2 → Router / Top-k → experts → merge / residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_MOE
  end
  loop OP_MOE token batch / expert group loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-sequence MoE input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-sequence MoE input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] RMSNorm 2 / router / expert parameters
  end
  %% source-node f05v01_n039 | owner=NormCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 2 output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] router input / expert queue source
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f05v01_n041 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] Router projection result
  end
  %% source-node f05v01_n042 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Router scoring
  end
  %% source-node f05v01_n043 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Top-8 + renorm
  end
  %% source-node f05v01_n044 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Dispatch / gather
  end
  rect rgba(213, 232, 212, 0.24)
    F->>B: [HW] expert queue / token grouping
  end
  rect rgba(213, 232, 212, 0.24)
    B-->>F: [HW] grouped expert activation
  end
  loop selected routed experts / grouped tokens
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f05v01_n045 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] gate_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f05v01_n046 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] up_proj result
  end
  %% source-node f05v01_n047 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: SiLU
  end
  %% source-node f05v01_n048 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Elementwise gate
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f05v01_n049 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  %% source-node f05v01_n050 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Expert weighting
  end
  %% source-node f05v01_n051 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Scatter / weighted reduce
  end
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] expert output stream(s)
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f05v01_n052 | owner=OutputCommitCore | class=plus | macro=OP_MOE
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f05v01_n053 | owner=OutputCommitCore | class=output | macro=OP_MOE
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_MOE done
  end

```

## 06_gpt2_dense_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 6: GPT-2 Dense
%% Source block-atlas file: 06_gpt2_dense.mmd
%% Sequence file: 06_gpt2_dense_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: Variant 1 — GPT-2 pre-LN dense block
  Note over C,O: OP_INPUT_POSITION — DDR read → Learned absolute position → positioned activation commit
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_INPUT_POSITION
  end
  loop OP_INPUT_POSITION token/beat loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — block input / residual
  end
  %% source-node f06v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_INPUT_POSITION
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>E: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — Learned absolute position
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — Learned absolute position
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] Learned absolute position
  end
  %% source-node f06v01_n020 | owner=ElementwiseTransformCore | class=other | macro=OP_INPUT_POSITION
  rect rgba(225, 213, 231, 0.24)
    E->>E: Learned absolute position
  end
  rect rgba(213, 232, 212, 0.24)
    E->>DDR: [HW] write positioned activation scratch
  end
  end
  rect rgba(242, 242, 242, 0.18)
    E-->>C: OP_INPUT_POSITION done
  end
  Note over C,O: OP_QKV_PROJ — LayerNorm 1 → Combined QKV Proj → Split heads → Q/K/V state staging
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_QKV_PROJ
  end
  loop OP_QKV_PROJ token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — positioned / block activation
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] positioned / block activation
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — LayerNorm 1 parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — LayerNorm 1 parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] LayerNorm 1 parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] LayerNorm 1 parameters
  end
  %% source-node f06v01_n021 | owner=NormCore | class=other | macro=OP_QKV_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: LayerNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] LayerNorm 1 output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] QKV input tile
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Combined QKV Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Combined QKV Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f06v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_QKV_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Combined QKV Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Combined QKV Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for Split heads
  end
  %% source-node f06v01_n024 | owner=ElementwiseTransformCore | class=other | macro=OP_QKV_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: Split heads
  end
  rect rgba(213, 232, 212, 0.24)
    E-->>K: [HW] K/V state streams
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write K/V state
  end
  rect rgba(213, 232, 212, 0.24)
    E-->>S: [HW] Q tile commit
  end
  end
  rect rgba(242, 242, 242, 0.18)
    S-->>C: OP_QKV_PROJ done
  end
  Note over C,O: OP_ATTENTION_OPROJ — K/V state read → sequence mixing → Output Proj → residual commit
  rect rgba(242, 242, 242, 0.18)
    C->>S: start OP_ATTENTION_OPROJ
  end
  loop OP_ATTENTION_OPROJ Q-block / KV-tile loop
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read K/V state / history
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] K/V state tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] K/V state response
  end
  %% source-node f06v01_n025 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q × Kᵀ
  end
  %% source-node f06v01_n026 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f06v01_n027 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] sequence output block + tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] tail projection request / grant
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for Output Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Output Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Output Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f06v01_n028 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Output Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>T: [EDGE E_MATRIX_TO_TAIL] Output Proj result tile
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>O: [EDGE E_MATRIX_TO_COMMIT] OProj result stream128
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f06v01_n029 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f06v01_n030 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    O->>O: X + Attention
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_Q_ATTN_OPROJ done
  end
  Note over C,O: OP_FFN — DDR read → LayerNorm 2 → dense FFN → residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_FFN
  end
  loop OP_FFN token/chunk/weight-tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — LayerNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — LayerNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] LayerNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] LayerNorm 2 / activation parameters
  end
  %% source-node f06v01_n031 | owner=NormCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    N->>N: LayerNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] LayerNorm 2 output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] FFN resident activation tile
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — fc1
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for fc1
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — fc1
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — fc1
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f06v01_n033 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: fc1
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] fc1 result
  end
  %% source-node f06v01_n034 | owner=FeedForwardCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    F->>F: GELU
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — fc2
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for fc2
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — fc2
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — fc2
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f06v01_n035 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: fc2
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] fc2 result
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] FFN result / residual input
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f06v01_n036 | owner=OutputCommitCore | class=plus | macro=OP_FFN
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f06v01_n037 | owner=OutputCommitCore | class=output | macro=OP_FFN
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_FFN done
  end

```

## 07_opt_dense_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 7: OPT Dense
%% Source block-atlas file: 07_opt_dense.mmd
%% Sequence file: 07_opt_dense_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: Variant 1 — OPT pre-LN dense block
  Note over C,O: OP_INPUT_POSITION — DDR read → Learned absolute position → positioned activation commit
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_INPUT_POSITION
  end
  loop OP_INPUT_POSITION token/beat loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — block input / residual
  end
  %% source-node f07v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_INPUT_POSITION
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>E: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — Learned absolute position
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — Learned absolute position
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] Learned absolute position
  end
  %% source-node f07v01_n020 | owner=ElementwiseTransformCore | class=other | macro=OP_INPUT_POSITION
  rect rgba(225, 213, 231, 0.24)
    E->>E: Learned absolute position
  end
  rect rgba(213, 232, 212, 0.24)
    E->>DDR: [HW] write positioned activation scratch
  end
  end
  rect rgba(242, 242, 242, 0.18)
    E-->>C: OP_INPUT_POSITION done
  end
  Note over C,O: OP_K_PROJ — LayerNorm 1 → K Proj
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_K_PROJ
  end
  loop OP_K_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — K pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] K pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — LayerNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — LayerNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] LayerNorm 1 / position parameters
  end
  %% source-node f07v01_n021 | owner=NormCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: LayerNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] LayerNorm 1 output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — K pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f07v01_n024 | owner=SharedMatrixCore | class=mac | macro=OP_K_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: K Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] K Proj result → projection-result dispatch
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
  end
  rect rgba(213, 232, 212, 0.24)
    K->>K: [HW] K state staging
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write K state
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_K_PROJ done
  end
  Note over C,O: OP_V_PROJ — LayerNorm 1 → V Proj
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_V_PROJ
  end
  loop OP_V_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — LayerNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — LayerNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] LayerNorm 1 / position parameters
  end
  %% hardware replay of source operator: LayerNorm 1 | pass=V pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: LayerNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] LayerNorm 1 output — V pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — V pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f07v01_n025 | owner=SharedMatrixCore | class=mac | macro=OP_V_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: V Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V Proj result → projection-result dispatch
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
  end
  rect rgba(213, 232, 212, 0.24)
    K->>K: [HW] V state staging
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write V state
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_V_PROJ done
  end
  Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: LayerNorm 1 → Q Proj
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_Q_ATTN_OPROJ
  end
  loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — LayerNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — LayerNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] LayerNorm 1 / position parameters
  end
  %% hardware replay of source operator: LayerNorm 1 | pass=Q pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: LayerNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] LayerNorm 1 output — Q pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — Q pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f07v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>S: [HW] Q Proj result
  end
  rect rgba(213, 232, 212, 0.24)
    M-->>S: [HW] commit Q tile / query stream
  end
  rect rgba(213, 232, 212, 0.24)
    S->>S: [HW] Q tile resident for subsequent sequence op
  end
  end
  Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → Output Proj → residual commit
  loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read K/V state / history
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] K/V state tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] K/V state response
  end
  %% source-node f07v01_n026 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q × Kᵀ
  end
  %% source-node f07v01_n027 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f07v01_n028 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] sequence output block + tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] tail projection request / grant
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for Output Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Output Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Output Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f07v01_n029 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Output Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>T: [EDGE E_MATRIX_TO_TAIL] Output Proj result tile
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>O: [EDGE E_MATRIX_TO_COMMIT] OProj result stream128
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f07v01_n030 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f07v01_n031 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    O->>O: X + Attention
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_Q_ATTN_OPROJ done
  end
  Note over C,O: OP_FFN — DDR read → LayerNorm 2 → dense FFN → residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_FFN
  end
  loop OP_FFN token/chunk/weight-tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — LayerNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — LayerNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] LayerNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] LayerNorm 2 / activation parameters
  end
  %% source-node f07v01_n032 | owner=NormCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    N->>N: LayerNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] LayerNorm 2 output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] FFN resident activation tile
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — fc1
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for fc1
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — fc1
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — fc1
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f07v01_n034 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: fc1
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] fc1 result
  end
  %% source-node f07v01_n035 | owner=FeedForwardCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    F->>F: ReLU
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — fc2
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for fc2
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — fc2
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — fc2
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f07v01_n036 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: fc2
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] fc2 result
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] FFN result / residual input
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f07v01_n037 | owner=OutputCommitCore | class=plus | macro=OP_FFN
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f07v01_n038 | owner=OutputCommitCore | class=output | macro=OP_FFN
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_FFN done
  end

```

## 08a_qwen3_5_qwen3_6_hybrid_dense_gdn_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 8: Qwen3.5 / Qwen3.6 Hybrid Dense
%% Source block-atlas file: 08_qwen3_5_qwen3_6_hybrid_dense.mmd
%% Sequence file: 08a_qwen3_5_qwen3_6_hybrid_dense_gdn_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Split variant a: GDN + dense SwiGLU block
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: OP_GDN_MIXER — DDR read → projections / vector transforms → Chunk Gated Delta Rule → recurrent-state write → out_proj / residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_GDN_MIXER
  end
  loop OP_GDN_MIXER token/chunk/state loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — GDN block input
  end
  %% source-node f08v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_GDN_MIXER
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm / beta / decay / gate parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm / beta / decay / gate parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm / beta / decay / gate parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm / beta / decay / gate parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [EDGE E_PARAM_GDN_STATIC_TO_TRANSFORM] RoPE/GDN static parameters
  end
  %% source-node f08v01_n020 | owner=NormCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] GDN projection input tile
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] input tile for in_proj_qkv
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — in_proj_qkv
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — in_proj_qkv
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f08v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_GDN_MIXER
  rect rgba(218, 232, 252, 0.24)
    M->>M: in_proj_qkv
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] in_proj_qkv result
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] input tile for in_proj_z
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — in_proj_z
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — in_proj_z
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f08v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_GDN_MIXER
  rect rgba(218, 232, 252, 0.24)
    M->>M: in_proj_z
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] in_proj_z result
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] input tile for in_proj_a
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — in_proj_a
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — in_proj_a
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f08v01_n024 | owner=SharedMatrixCore | class=mac | macro=OP_GDN_MIXER
  rect rgba(218, 232, 252, 0.24)
    M->>M: in_proj_a
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] in_proj_a result
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] input tile for in_proj_b
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — in_proj_b
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — in_proj_b
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f08v01_n025 | owner=SharedMatrixCore | class=mac | macro=OP_GDN_MIXER
  rect rgba(218, 232, 252, 0.24)
    M->>M: in_proj_b
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] in_proj_b result
  end
  %% source-node f08v01_n026 | owner=SharedMatrixCore | class=other | macro=OP_GDN_MIXER
  rect rgba(213, 232, 212, 0.24)
    K-->>M: [EDGE E_STATE_GDN_CONV_HISTORY_TO_MATRIX] conv-history response
  end
  rect rgba(225, 213, 231, 0.24)
    E->>M: [HW] matrix service request — Depthwise Conv1D
  end
  rect rgba(225, 213, 231, 0.24)
    M->>M: Depthwise Conv1D
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Depthwise Conv1D result
  end
  rect rgba(213, 232, 212, 0.24)
    M-->>K: [EDGE E_MATRIX_GDN_CONV_HISTORY_TO_STATE] updated conv-history commit
  end
  %% source-node f08v01_n027 | owner=ElementwiseTransformCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    E->>E: SiLU
  end
  %% source-node f08v01_n028 | owner=ElementwiseTransformCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    E->>E: Split Q / K / V
  end
  %% source-node f08v01_n029 | owner=ElementwiseTransformCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    E->>E: Q reshape
  end
  %% source-node f08v01_n030 | owner=ElementwiseTransformCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    E->>E: K reshape
  end
  %% source-node f08v01_n031 | owner=ElementwiseTransformCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    E->>E: V reshape
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>B: [EDGE E_TRANSFORM_GDN_HEAD_TO_ACTBUF] Q/K/V head tiles
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [GDN HEAD-NORM SERVICE] Q/K L2Norm request
  end

  %% source-node f08v01_n032 | owner=NormCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    N->>N: Q L2Norm (shared Norm service)
  end
  %% source-node f08v01_n033 | owner=NormCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    N->>N: K L2Norm (shared Norm service)
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [GDN HEAD-NORM SERVICE] normalized Q/K response
  end
  %% source-node f08v01_n034 | owner=ElementwiseTransformCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    E->>E: Decay preactivation
  end
  %% source-node f08v01_n035 | owner=ElementwiseTransformCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    E->>E: Decay factor
  end
  %% source-node f08v01_n036 | owner=ElementwiseTransformCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    E->>E: Update gate
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>B: [EDGE E_TRANSFORM_GDN_HEAD_TO_ACTBUF] Z/A/B + decay/update streams
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>S: [EDGE E_ACTBUF_GDN_VZAB_TO_SEQUENCE] normalized Q/K + V/Z/A/B tiles
  end
  %% source-node f08v01_n037 | owner=SequenceCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    S->>S: Chunk partition
  end
  %% source-node f08v01_n038 | owner=SequenceCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    S->>S: Decay matrix Γ
  end
  %% source-node f08v01_n039 | owner=SequenceCore | class=mac | macro=OP_GDN_MIXER
  rect rgba(218, 232, 252, 0.24)
    S->>S: K Kᵀ
  end
  %% source-node f08v01_n040 | owner=SequenceCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    S->>S: Build strict-lower L
  end
  %% source-node f08v01_n041 | owner=SequenceCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    S->>S: Triangular solve
  end
  %% source-node f08v01_n042 | owner=SequenceCore | class=mac | macro=OP_GDN_MIXER
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q Kᵀ
  end
  %% source-node f08v01_n043 | owner=SequenceCore | class=mac | macro=OP_GDN_MIXER
  rect rgba(218, 232, 252, 0.24)
    S->>S: Intra-chunk output
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read recurrent state S
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] recurrent state S tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] recurrent state response
  end
  %% source-node f08v01_n044 | owner=SequenceCore | class=mac | macro=OP_GDN_MIXER
  rect rgba(218, 232, 252, 0.24)
    S->>S: State read
  end
  %% source-node f08v01_n045 | owner=SequenceCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    S->>S: Output combine
  end
  %% source-node f08v01_n046 | owner=SequenceCore | class=mac | macro=OP_GDN_MIXER
  rect rgba(218, 232, 252, 0.24)
    S->>S: Kᵀ U
  end
  %% source-node f08v01_n047 | owner=SequenceCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    S->>S: State decay
  end
  %% source-node f08v01_n048 | owner=SequenceCore | class=plus | macro=OP_GDN_MIXER
  rect rgba(255, 255, 255, 0.28)
    S->>S: +
  end
  %% source-node f08v01_n049 | owner=KVStateCore | class=state | macro=OP_GDN_MIXER
  rect rgba(213, 232, 212, 0.24)
    S-->>K: [GDN STATE COMMIT] updated recurrent state S
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write Recurrent state S
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>N: [EDGE E_SEQUENCE_GDN_NORM_REQUEST] GDN output / gated-norm request
  end
  %% source-node f08v01_n050 | owner=NormCore | class=other | macro=OP_GDN_MIXER
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNormGated
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>S: [EDGE E_NORM_GDN_RESPONSE_TO_SEQUENCE] normalized/gated GDN response
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [EDGE E_SEQUENCE_TO_TAIL] gated GDN output + tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] GDN tail projection request
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for out_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — out_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — out_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f08v01_n051 | owner=SharedMatrixCore | class=mac | macro=OP_GDN_MIXER
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
    T-->>O: [EDGE E_TAIL_TO_COMMIT] GDN tail commit metadata
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f08v01_n052 | owner=OutputCommitCore | class=plus | macro=OP_GDN_MIXER
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f08v01_n053 | owner=OutputCommitCore | class=output | macro=OP_GDN_MIXER
  rect rgba(213, 232, 212, 0.24)
    O->>O: X + GDN
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_GDN_MIXER done
  end
  Note over C,O: OP_FFN — DDR read → RMSNorm 2 → dense FFN → residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_FFN
  end
  loop OP_FFN token/chunk/weight-tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] RMSNorm 2 / activation parameters
  end
  %% source-node f08v01_n054 | owner=NormCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 2 output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] FFN resident activation tile
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f08v01_n056 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M->>M: [HW] gate tile held locally for fused SwiGLU
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f08v01_n057 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M->>M: [HW] up tile held locally for fused SwiGLU
  end
  %% source-node f08v01_n058 | owner=SharedMatrixCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    M->>M: SiLU (current fused MlpSiluLane32Core)
  end
  %% source-node f08v01_n059 | owner=SharedMatrixCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    M->>M: Elementwise gate (current fused Gate×Up)
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [EDGE E_MATRIX_TO_FFN] fused activation ready / down-phase event
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f08v01_n060 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] FFN result / residual input
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f08v01_n061 | owner=OutputCommitCore | class=plus | macro=OP_FFN
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f08v01_n062 | owner=OutputCommitCore | class=output | macro=OP_FFN
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_FFN done
  end

```

## 08b_qwen3_5_qwen3_6_hybrid_dense_full_attention_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 8: Qwen3.5 / Qwen3.6 Hybrid Dense
%% Source block-atlas file: 08_qwen3_5_qwen3_6_hybrid_dense.mmd
%% Sequence file: 08b_qwen3_5_qwen3_6_hybrid_dense_full_attention_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Split variant b: Gated full-attention + dense SwiGLU block
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: OP_K_PROJ — RMSNorm 1 → K Proj → K Head RMSNorm → Partial RoPE → K cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_K_PROJ
  end
  loop OP_K_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — K pass activation / residual
  end
  %% source-node f08v02_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_K_PROJ
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% source-node f08v02_n020 | owner=NormCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — K pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f08v02_n022 | owner=SharedMatrixCore | class=mac | macro=OP_K_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: K Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>B: [HEAD/POST-NORM STAGING] K Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [HEAD/POST-NORM SERVICE] K Head RMSNorm request / 32-lane replay
  end
  %% source-node f08v02_n025 | owner=NormCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: K Head RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HEAD/POST-NORM SERVICE] K Head RMSNorm output response
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
  end
  %% source-node f08v02_n027 | owner=ElementwiseTransformCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: Partial RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] Partial RoPE output
  end
  %% source-node f08v02_n029 | owner=KVStateCore | class=state | macro=OP_K_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: K cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write K cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_K_PROJ done
  end
  Note over C,O: OP_V_PROJ — RMSNorm 1 → V Proj → V cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_V_PROJ
  end
  loop OP_V_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=V pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — V pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — V pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f08v02_n024 | owner=SharedMatrixCore | class=mac | macro=OP_V_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: V Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V Proj result → projection-result dispatch
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
  end
  %% source-node f08v02_n030 | owner=KVStateCore | class=state | macro=OP_V_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: V cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write V cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_V_PROJ done
  end
  Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: RMSNorm 1 → Q Proj + gate → Q Head RMSNorm → Partial RoPE
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_Q_ATTN_OPROJ
  end
  loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=Q pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — Q pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — Q pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q Proj + gate
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q Proj + gate
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f08v02_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q Proj + gate
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>T: [EDGE E_MATRIX_TO_TAIL_Q_GATE_SPLIT] Q projection + gate split stream
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>B: [EDGE E_TAIL_TO_ACTBUF_Q_QUERY] Q query stream to HeadNormTileBuffer
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>S: [EDGE E_TAIL_TO_SEQUENCE_Q_GATE] Q output-gate stream to AttentionOutputGateCore
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [HEAD-NORM SERVICE] Q Head RMSNorm request / replay
  end
  %% source-node f08v02_n026 | owner=NormCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: Q Head RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HEAD/POST-NORM SERVICE] Q Head RMSNorm output response
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
  end
  %% source-node f08v02_n028 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: Partial RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>S: [HW] Partial RoPE output
  end
  rect rgba(213, 232, 212, 0.24)
    E-->>S: [HW] commit Q tile / query stream
  end
  rect rgba(213, 232, 212, 0.24)
    S->>S: [HW] Q tile resident for subsequent sequence op
  end
  end
Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → O Proj → residual commit
loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read K/V state / history
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] K/V state tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] K/V state response
  end
  %% source-node f08v02_n031 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: K head repeat ×4
  end
  %% source-node f08v02_n032 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: V head repeat ×4
  end
  %% source-node f08v02_n033 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q × Kᵀ
  end
  %% source-node f08v02_n034 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f08v02_n035 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  %% source-node f08v02_n036 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Q-gate sigmoid (AttentionOutputGateCore)
  end
  %% source-node f08v02_n037 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Context gating (scale final O)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [EDGE E_SEQUENCE_TO_TAIL] gated attention context + tags
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] sequence output block + tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] tail projection request / grant
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f08v02_n038 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
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
    T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f08v02_n039 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f08v02_n040 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    O->>O: X + Attention
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_Q_ATTN_OPROJ done
  end
  Note over C,O: OP_FFN — DDR read → RMSNorm 2 → dense FFN → residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_FFN
  end
  loop OP_FFN token/chunk/weight-tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] RMSNorm 2 / activation parameters
  end
  %% source-node f08v02_n041 | owner=NormCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 2 output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] FFN resident activation tile
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f08v02_n043 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M->>M: [HW] gate tile held locally for fused SwiGLU
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f08v02_n044 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M->>M: [HW] up tile held locally for fused SwiGLU
  end
  %% source-node f08v02_n045 | owner=SharedMatrixCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    M->>M: SiLU (current fused MlpSiluLane32Core)
  end
  %% source-node f08v02_n046 | owner=SharedMatrixCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    M->>M: Elementwise gate (current fused Gate×Up)
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [EDGE E_MATRIX_TO_FFN] fused activation ready / down-phase event
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f08v02_n047 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] FFN result / residual input
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f08v02_n048 | owner=OutputCommitCore | class=plus | macro=OP_FFN
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f08v02_n049 | owner=OutputCommitCore | class=output | macro=OP_FFN
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_FFN done
  end

```

## 09_gpt_oss_moe_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 9: GPT-OSS MoE
%% Source block-atlas file: 09_gpt_oss_moe.mmd
%% Sequence file: 09_gpt_oss_moe_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  alt Variant 1 — Sliding-window attention + Top-4 MoE block
    Note over C,O: OP_K_PROJ — RMSNorm 1 → K Proj → RoPE → K cache
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_K_PROJ
    end
    loop OP_K_PROJ autonomous token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — K pass activation / residual
    end
    %% source-node f09v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_K_PROJ
    rect rgba(255, 242, 204, 0.24)
      A->>A: X
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] RMSNorm 1 / position parameters
    end
    %% source-node f09v01_n020 | owner=NormCore | class=other | macro=OP_K_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 1
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 1 output
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] resident tile — K pass
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — K Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — K Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f09v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_K_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: K Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>E: [HW] K Proj result
    end
    rect rgba(245, 245, 245, 0.18)
      M->>E: [HW] input for RoPE
    end
    %% source-node f09v01_n025 | owner=ElementwiseTransformCore | class=other | macro=OP_K_PROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: RoPE
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>K: [HW] RoPE output
    end
    %% source-node f09v01_n027 | owner=KVStateCore | class=state | macro=OP_K_PROJ
    rect rgba(213, 232, 212, 0.24)
      K->>K: K cache
    end
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] write K cache
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] write response
    end
    end
    rect rgba(242, 242, 242, 0.18)
      K-->>C: OP_K_PROJ done
    end
    Note over C,O: OP_V_PROJ — RMSNorm 1 → V Proj → V cache
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_V_PROJ
    end
    loop OP_V_PROJ autonomous token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — V pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] V pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] RMSNorm 1 / position parameters
    end
    %% hardware replay of source operator: RMSNorm 1 | pass=V pass
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 1
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 1 output — V pass
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] resident tile — V pass
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — V Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — V Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f09v01_n024 | owner=SharedMatrixCore | class=mac | macro=OP_V_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: V Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V Proj result → projection-result dispatch
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
    end
    %% source-node f09v01_n028 | owner=KVStateCore | class=state | macro=OP_V_PROJ
    rect rgba(213, 232, 212, 0.24)
      K->>K: V cache
    end
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] write V cache
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] write response
    end
    end
    rect rgba(242, 242, 242, 0.18)
      K-->>C: OP_V_PROJ done
    end
    Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: RMSNorm 1 → Q Proj → RoPE
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_Q_ATTN_OPROJ
    end
    loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — Q pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] Q pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] RMSNorm 1 / position parameters
    end
    %% hardware replay of source operator: RMSNorm 1 | pass=Q pass
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 1
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 1 output — Q pass
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] resident tile — Q pass
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Q Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Q Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f09v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: Q Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>E: [HW] Q Proj result
    end
    rect rgba(245, 245, 245, 0.18)
      M->>E: [HW] input for RoPE
    end
    %% source-node f09v01_n026 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: RoPE
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>S: [HW] RoPE output
    end
    rect rgba(213, 232, 212, 0.24)
      E-->>S: [HW] commit Q tile / query stream
    end
    rect rgba(213, 232, 212, 0.24)
      S->>S: [HW] Q tile resident for subsequent sequence op
    end
    end
  Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → O Proj → residual commit
  loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] read K/V state / history
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] K/V state tile
    end
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] K/V state response
    end
    %% source-node f09v01_n029 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] KV-group state broadcast / lane map
    end
    rect rgba(225, 213, 231, 0.24)
      S->>S: K head repeat ×8
    end
    %% source-node f09v01_n030 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] KV-group state broadcast / lane map
    end
    rect rgba(225, 213, 231, 0.24)
      S->>S: V head repeat ×8
    end
    %% source-node f09v01_n031 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      S->>S: Q × Kᵀ
    end
    %% source-node f09v01_n032 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      S->>S: Softmax FP32 + sink
    end
    %% source-node f09v01_n033 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      S->>S: P × V / Online O recurrence (β×V + α×Oold)
    end
    rect rgba(245, 245, 245, 0.18)
      S-->>T: [HW] sequence output block + tags
    end
    rect rgba(242, 242, 242, 0.18)
      T->>M: [HW] tail projection request / grant
    end
    rect rgba(245, 245, 245, 0.18)
      T->>M: [HW] input tile for O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f09v01_n034 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
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
      T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f09v01_n035 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f09v01_n036 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      O->>O: X + Attention
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_Q_ATTN_OPROJ done
    end
    Note over C,O: OP_MOE — DDR read → RMSNorm 2 → Router / Top-k → experts → merge / residual write
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_MOE
    end
    loop OP_MOE token batch / expert group loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — post-sequence MoE input
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] post-sequence MoE input
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>F: [HW] RMSNorm 2 / router / expert parameters
    end
    %% source-node f09v01_n037 | owner=NormCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 2
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 2 output
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>F: [HW] router input / expert queue source
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — Router projection
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f09v01_n039 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: Router projection
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] Router projection result
    end
    %% source-node f09v01_n040 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Router scoring
    end
    %% source-node f09v01_n041 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Top-4 + renorm
    end
    %% source-node f09v01_n042 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Dispatch / gather
    end
    rect rgba(213, 232, 212, 0.24)
      F->>B: [HW] expert queue / token grouping
    end
    rect rgba(213, 232, 212, 0.24)
      B-->>F: [HW] grouped expert activation
    end
    loop selected routed experts / grouped tokens
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f09v01_n043 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] gate_proj result
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f09v01_n044 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] up_proj result
    end
    %% source-node f09v01_n045 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: SiLU
    end
    %% source-node f09v01_n046 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Elementwise gate
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f09v01_n047 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] down_proj result
    end
    %% source-node f09v01_n048 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Expert weighting
    end
    %% source-node f09v01_n049 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Scatter / weighted reduce
    end
    end
    rect rgba(245, 245, 245, 0.18)
      F-->>O: [HW] expert output stream(s)
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f09v01_n050 | owner=OutputCommitCore | class=plus | macro=OP_MOE
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f09v01_n051 | owner=OutputCommitCore | class=output | macro=OP_MOE
    rect rgba(213, 232, 212, 0.24)
      O->>O: Block output
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_MOE done
    end
  else Variant 2 — Full attention + Top-4 MoE block
    Note over C,O: OP_K_PROJ — RMSNorm 1 → K Proj → RoPE → K cache
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_K_PROJ
    end
    loop OP_K_PROJ autonomous token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — K pass activation / residual
    end
    %% source-node f09v02_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_K_PROJ
    rect rgba(255, 242, 204, 0.24)
      A->>A: X
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] RMSNorm 1 / position parameters
    end
    %% source-node f09v02_n020 | owner=NormCore | class=other | macro=OP_K_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 1
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 1 output
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] resident tile — K pass
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — K Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — K Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f09v02_n022 | owner=SharedMatrixCore | class=mac | macro=OP_K_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: K Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>E: [HW] K Proj result
    end
    rect rgba(245, 245, 245, 0.18)
      M->>E: [HW] input for RoPE
    end
    %% source-node f09v02_n025 | owner=ElementwiseTransformCore | class=other | macro=OP_K_PROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: RoPE
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>K: [HW] RoPE output
    end
    %% source-node f09v02_n027 | owner=KVStateCore | class=state | macro=OP_K_PROJ
    rect rgba(213, 232, 212, 0.24)
      K->>K: K cache
    end
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] write K cache
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] write response
    end
    end
    rect rgba(242, 242, 242, 0.18)
      K-->>C: OP_K_PROJ done
    end
    Note over C,O: OP_V_PROJ — RMSNorm 1 → V Proj → V cache
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_V_PROJ
    end
    loop OP_V_PROJ autonomous token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — V pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] V pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] RMSNorm 1 / position parameters
    end
    %% hardware replay of source operator: RMSNorm 1 | pass=V pass
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 1
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 1 output — V pass
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] resident tile — V pass
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — V Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — V Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f09v02_n024 | owner=SharedMatrixCore | class=mac | macro=OP_V_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: V Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V Proj result → projection-result dispatch
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
    end
    %% source-node f09v02_n028 | owner=KVStateCore | class=state | macro=OP_V_PROJ
    rect rgba(213, 232, 212, 0.24)
      K->>K: V cache
    end
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] write V cache
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] write response
    end
    end
    rect rgba(242, 242, 242, 0.18)
      K-->>C: OP_V_PROJ done
    end
    Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: RMSNorm 1 → Q Proj → RoPE
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_Q_ATTN_OPROJ
    end
    loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — Q pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] Q pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] RMSNorm 1 / position parameters
    end
    %% hardware replay of source operator: RMSNorm 1 | pass=Q pass
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 1
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 1 output — Q pass
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] resident tile — Q pass
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Q Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Q Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f09v02_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: Q Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>E: [HW] Q Proj result
    end
    rect rgba(245, 245, 245, 0.18)
      M->>E: [HW] input for RoPE
    end
    %% source-node f09v02_n026 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: RoPE
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>S: [HW] RoPE output
    end
    rect rgba(213, 232, 212, 0.24)
      E-->>S: [HW] commit Q tile / query stream
    end
    rect rgba(213, 232, 212, 0.24)
      S->>S: [HW] Q tile resident for subsequent sequence op
    end
    end
  Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → O Proj → residual commit
  loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] read K/V state / history
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] K/V state tile
    end
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] K/V state response
    end
    %% source-node f09v02_n029 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] KV-group state broadcast / lane map
    end
    rect rgba(225, 213, 231, 0.24)
      S->>S: K head repeat ×8
    end
    %% source-node f09v02_n030 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] KV-group state broadcast / lane map
    end
    rect rgba(225, 213, 231, 0.24)
      S->>S: V head repeat ×8
    end
    %% source-node f09v02_n031 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      S->>S: Q × Kᵀ
    end
    %% source-node f09v02_n032 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      S->>S: Softmax FP32 + sink
    end
    %% source-node f09v02_n033 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      S->>S: P × V / Online O recurrence (β×V + α×Oold)
    end
    rect rgba(245, 245, 245, 0.18)
      S-->>T: [HW] sequence output block + tags
    end
    rect rgba(242, 242, 242, 0.18)
      T->>M: [HW] tail projection request / grant
    end
    rect rgba(245, 245, 245, 0.18)
      T->>M: [HW] input tile for O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f09v02_n034 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
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
      T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f09v02_n035 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f09v02_n036 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      O->>O: X + Attention
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_Q_ATTN_OPROJ done
    end
    Note over C,O: OP_MOE — DDR read → RMSNorm 2 → Router / Top-k → experts → merge / residual write
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_MOE
    end
    loop OP_MOE token batch / expert group loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — post-sequence MoE input
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] post-sequence MoE input
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>F: [HW] RMSNorm 2 / router / expert parameters
    end
    %% source-node f09v02_n037 | owner=NormCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 2
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 2 output
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>F: [HW] router input / expert queue source
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — Router projection
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f09v02_n039 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: Router projection
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] Router projection result
    end
    %% source-node f09v02_n040 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Router scoring
    end
    %% source-node f09v02_n041 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Top-4 + renorm
    end
    %% source-node f09v02_n042 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Dispatch / gather
    end
    rect rgba(213, 232, 212, 0.24)
      F->>B: [HW] expert queue / token grouping
    end
    rect rgba(213, 232, 212, 0.24)
      B-->>F: [HW] grouped expert activation
    end
    loop selected routed experts / grouped tokens
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f09v02_n043 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] gate_proj result
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f09v02_n044 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] up_proj result
    end
    %% source-node f09v02_n045 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: SiLU
    end
    %% source-node f09v02_n046 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Elementwise gate
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f09v02_n047 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] down_proj result
    end
    %% source-node f09v02_n048 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Expert weighting
    end
    %% source-node f09v02_n049 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Scatter / weighted reduce
    end
    end
    rect rgba(245, 245, 245, 0.18)
      F-->>O: [HW] expert output stream(s)
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f09v02_n050 | owner=OutputCommitCore | class=plus | macro=OP_MOE
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f09v02_n051 | owner=OutputCommitCore | class=output | macro=OP_MOE
    rect rgba(213, 232, 212, 0.24)
      O->>O: Block output
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_MOE done
    end
  end

```

## 10_gemma4_dense_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 10: Gemma 4 Dense
%% Source block-atlas file: 10_gemma4_dense.mmd
%% Sequence file: 10_gemma4_dense_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  alt Variant 1 — Sliding-window GeGLU block
    Note over C,O: OP_KV_SHARED_PROJ — Pre-Attention RMSNorm → K=V shared Proj → K/V state commit
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_KV_SHARED_PROJ
    end
    loop OP_KV_SHARED_PROJ token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — K/V shared projection activation
    end
    %% source-node f10v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_KV_SHARED_PROJ
    rect rgba(255, 242, 204, 0.24)
      A->>A: X
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — Pre-Attention RMSNorm / K position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — Pre-Attention RMSNorm / K position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] Pre-Attention RMSNorm / K position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] Pre-Attention RMSNorm / K position parameters
    end
    %% source-node f10v01_n020 | owner=NormCore | class=other | macro=OP_KV_SHARED_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: Pre-Attention RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] Pre-Attention RMSNorm output
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] K/V shared input tile
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — K=V shared Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — K=V shared Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f10v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_KV_SHARED_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: K=V shared Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>B: [HEAD/POST-NORM STAGING] K=V shared Proj result
    end
    rect rgba(245, 245, 245, 0.18)
      B->>N: [HEAD/POST-NORM SERVICE] K Head RMSNorm request / 32-lane replay
    end
    %% source-node f10v01_n024 | owner=NormCore | class=other | macro=OP_KV_SHARED_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: K Head RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HEAD/POST-NORM SERVICE] K Head RMSNorm output response
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
    end
    %% source-node f10v01_n026 | owner=ElementwiseTransformCore | class=other | macro=OP_KV_SHARED_PROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: RoPE
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>K: [HW] RoPE output
    end
    %% source-node f10v01_n028 | owner=KVStateCore | class=state | macro=OP_KV_SHARED_PROJ
    rect rgba(213, 232, 212, 0.24)
      K->>K: K cache
    end
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] write K cache
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] write response
    end
    %% source-node f10v01_n029 | owner=KVStateCore | class=state | macro=OP_KV_SHARED_PROJ
    rect rgba(213, 232, 212, 0.24)
      K->>K: V cache
    end
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] write V cache
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] write response
    end
    end
    rect rgba(242, 242, 242, 0.18)
      K-->>C: OP_KV_SHARED_PROJ done
    end
    Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: Pre-Attention RMSNorm → Q Proj → Q Head RMSNorm → RoPE
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_Q_ATTN_OPROJ
    end
    loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — Q pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] Q pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] Pre-Attention RMSNorm / position parameters
    end
    %% hardware replay of source operator: Pre-Attention RMSNorm | pass=Q pass
    rect rgba(225, 213, 231, 0.24)
      N->>N: Pre-Attention RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] Pre-Attention RMSNorm output — Q pass
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] resident tile — Q pass
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Q Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Q Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f10v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: Q Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>B: [HEAD/POST-NORM STAGING] Q Proj result
    end
    rect rgba(245, 245, 245, 0.18)
      B->>N: [HEAD/POST-NORM SERVICE] Q Head RMSNorm request / 32-lane replay
    end
    %% source-node f10v01_n025 | owner=NormCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: Q Head RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HEAD/POST-NORM SERVICE] Q Head RMSNorm output response
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
    end
    %% source-node f10v01_n027 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: RoPE
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>S: [HW] RoPE output
    end
    rect rgba(213, 232, 212, 0.24)
      E-->>S: [HW] commit Q tile / query stream
    end
    rect rgba(213, 232, 212, 0.24)
      S->>S: [HW] Q tile resident for subsequent sequence op
    end
    end
  Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → O Proj → residual commit
  loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] read K/V state / history
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] K/V state tile
    end
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] K/V state response
    end
    %% source-node f10v01_n030 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] KV-group state broadcast / lane map
    end
    rect rgba(225, 213, 231, 0.24)
      S->>S: K head repeat ×2
    end
    %% source-node f10v01_n031 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] KV-group state broadcast / lane map
    end
    rect rgba(225, 213, 231, 0.24)
      S->>S: V head repeat ×2
    end
    %% source-node f10v01_n032 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      S->>S: Q × Kᵀ
    end
    %% source-node f10v01_n033 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      S->>S: Softmax FP32
    end
    %% source-node f10v01_n034 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      S->>S: P × V / Online O recurrence (β×V + α×Oold)
    end
    rect rgba(245, 245, 245, 0.18)
      S-->>T: [HW] sequence output block + tags
    end
    rect rgba(242, 242, 242, 0.18)
      T->>M: [HW] tail projection request / grant
    end
    rect rgba(245, 245, 245, 0.18)
      T->>M: [HW] input tile for O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f10v01_n035 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
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
      T->>N: [HW] input for Post-Attention RMSNorm
    end
    %% source-node f10v01_n036 | owner=NormCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: Post-Attention RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [HW] Post-Attention RMSNorm output
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f10v01_n037 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f10v01_n038 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      O->>O: X + Attention
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_Q_ATTN_OPROJ done
    end
    Note over C,O: OP_FFN — DDR read → Pre-FFN RMSNorm → dense FFN → residual write
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_FFN
    end
    loop OP_FFN token/chunk/weight-tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — post-attention / FFN input
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] post-attention / FFN input
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — Pre-FFN RMSNorm / activation parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — Pre-FFN RMSNorm / activation parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] Pre-FFN RMSNorm / activation parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>F: [HW] Pre-FFN RMSNorm / activation parameters
    end
    %% source-node f10v01_n039 | owner=NormCore | class=other | macro=OP_FFN
    rect rgba(225, 213, 231, 0.24)
      N->>N: Pre-FFN RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] Pre-FFN RMSNorm output
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>F: [HW] FFN resident activation tile
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f10v01_n041 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
    rect rgba(218, 232, 252, 0.24)
      M->>M: gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M->>M: [HW] gate tile held locally for fused SwiGLU
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f10v01_n042 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
    rect rgba(218, 232, 252, 0.24)
      M->>M: up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M->>M: [HW] up tile held locally for fused SwiGLU
    end
    %% source-node f10v01_n043 | owner=FeedForwardCore | class=other | macro=OP_FFN
    rect rgba(225, 213, 231, 0.24)
      F->>F: GELU-tanh
    end
    %% source-node f10v01_n044 | owner=SharedMatrixCore | class=other | macro=OP_FFN
    rect rgba(225, 213, 231, 0.24)
      M->>M: Elementwise gate (current fused Gate×Up)
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f10v01_n045 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
    rect rgba(218, 232, 252, 0.24)
      M->>M: down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] down_proj result
    end
    rect rgba(245, 245, 245, 0.18)
      F->>N: [HW] input for Post-FFN RMSNorm
    end
    %% source-node f10v01_n046 | owner=NormCore | class=other | macro=OP_FFN
    rect rgba(225, 213, 231, 0.24)
      N->>N: Post-FFN RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [HW] Post-FFN RMSNorm output
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f10v01_n047 | owner=OutputCommitCore | class=plus | macro=OP_FFN
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f10v01_n048 | owner=OutputCommitCore | class=output | macro=OP_FFN
    rect rgba(213, 232, 212, 0.24)
      O->>O: Block output
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_FFN done
    end
  else Variant 2 — Full-attention GeGLU block
    Note over C,O: OP_KV_SHARED_PROJ — Pre-Attention RMSNorm → K=V shared Proj → K/V state commit
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_KV_SHARED_PROJ
    end
    loop OP_KV_SHARED_PROJ token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — K/V shared projection activation
    end
    %% source-node f10v02_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_KV_SHARED_PROJ
    rect rgba(255, 242, 204, 0.24)
      A->>A: X
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — Pre-Attention RMSNorm / K position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — Pre-Attention RMSNorm / K position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] Pre-Attention RMSNorm / K position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] Pre-Attention RMSNorm / K position parameters
    end
    %% source-node f10v02_n020 | owner=NormCore | class=other | macro=OP_KV_SHARED_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: Pre-Attention RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] Pre-Attention RMSNorm output
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] K/V shared input tile
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — K=V shared Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — K=V shared Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f10v02_n022 | owner=SharedMatrixCore | class=mac | macro=OP_KV_SHARED_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: K=V shared Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>B: [HEAD/POST-NORM STAGING] K=V shared Proj result
    end
    rect rgba(245, 245, 245, 0.18)
      B->>N: [HEAD/POST-NORM SERVICE] K Head RMSNorm request / 32-lane replay
    end
    %% source-node f10v02_n024 | owner=NormCore | class=other | macro=OP_KV_SHARED_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: K Head RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HEAD/POST-NORM SERVICE] K Head RMSNorm output response
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
    end
    %% source-node f10v02_n026 | owner=ElementwiseTransformCore | class=other | macro=OP_KV_SHARED_PROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: Partial RoPE
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>K: [HW] Partial RoPE output
    end
    %% source-node f10v02_n028 | owner=KVStateCore | class=state | macro=OP_KV_SHARED_PROJ
    rect rgba(213, 232, 212, 0.24)
      K->>K: K cache
    end
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] write K cache
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] write response
    end
    %% source-node f10v02_n029 | owner=KVStateCore | class=state | macro=OP_KV_SHARED_PROJ
    rect rgba(213, 232, 212, 0.24)
      K->>K: V cache
    end
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] write V cache
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] write response
    end
    end
    rect rgba(242, 242, 242, 0.18)
      K-->>C: OP_KV_SHARED_PROJ done
    end
    Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: Pre-Attention RMSNorm → Q Proj → Q Head RMSNorm → Partial RoPE
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_Q_ATTN_OPROJ
    end
    loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — Q pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] Q pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] Pre-Attention RMSNorm / position parameters
    end
    %% hardware replay of source operator: Pre-Attention RMSNorm | pass=Q pass
    rect rgba(225, 213, 231, 0.24)
      N->>N: Pre-Attention RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] Pre-Attention RMSNorm output — Q pass
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] resident tile — Q pass
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Q Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Q Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f10v02_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: Q Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>B: [HEAD/POST-NORM STAGING] Q Proj result
    end
    rect rgba(245, 245, 245, 0.18)
      B->>N: [HEAD/POST-NORM SERVICE] Q Head RMSNorm request / 32-lane replay
    end
    %% source-node f10v02_n025 | owner=NormCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: Q Head RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HEAD/POST-NORM SERVICE] Q Head RMSNorm output response
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
    end
    %% source-node f10v02_n027 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: Partial RoPE
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>S: [HW] Partial RoPE output
    end
    rect rgba(213, 232, 212, 0.24)
      E-->>S: [HW] commit Q tile / query stream
    end
    rect rgba(213, 232, 212, 0.24)
      S->>S: [HW] Q tile resident for subsequent sequence op
    end
    end
  Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → O Proj → residual commit
  loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] read K/V state / history
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] K/V state tile
    end
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] K/V state response
    end
    %% source-node f10v02_n030 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] KV-group state broadcast / lane map
    end
    rect rgba(225, 213, 231, 0.24)
      S->>S: K head repeat ×2
    end
    %% source-node f10v02_n031 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] KV-group state broadcast / lane map
    end
    rect rgba(225, 213, 231, 0.24)
      S->>S: V head repeat ×2
    end
    %% source-node f10v02_n032 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      S->>S: Q × Kᵀ
    end
    %% source-node f10v02_n033 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      S->>S: Softmax FP32
    end
    %% source-node f10v02_n034 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      S->>S: P × V / Online O recurrence (β×V + α×Oold)
    end
    rect rgba(245, 245, 245, 0.18)
      S-->>T: [HW] sequence output block + tags
    end
    rect rgba(242, 242, 242, 0.18)
      T->>M: [HW] tail projection request / grant
    end
    rect rgba(245, 245, 245, 0.18)
      T->>M: [HW] input tile for O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f10v02_n035 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
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
      T->>N: [HW] input for Post-Attention RMSNorm
    end
    %% source-node f10v02_n036 | owner=NormCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: Post-Attention RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [HW] Post-Attention RMSNorm output
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f10v02_n037 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f10v02_n038 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      O->>O: X + Attention
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_Q_ATTN_OPROJ done
    end
    Note over C,O: OP_FFN — DDR read → Pre-FFN RMSNorm → dense FFN → residual write
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_FFN
    end
    loop OP_FFN token/chunk/weight-tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — post-attention / FFN input
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] post-attention / FFN input
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — Pre-FFN RMSNorm / activation parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — Pre-FFN RMSNorm / activation parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] Pre-FFN RMSNorm / activation parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>F: [HW] Pre-FFN RMSNorm / activation parameters
    end
    %% source-node f10v02_n039 | owner=NormCore | class=other | macro=OP_FFN
    rect rgba(225, 213, 231, 0.24)
      N->>N: Pre-FFN RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] Pre-FFN RMSNorm output
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>F: [HW] FFN resident activation tile
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f10v02_n041 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
    rect rgba(218, 232, 252, 0.24)
      M->>M: gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M->>M: [HW] gate tile held locally for fused SwiGLU
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f10v02_n042 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
    rect rgba(218, 232, 252, 0.24)
      M->>M: up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M->>M: [HW] up tile held locally for fused SwiGLU
    end
    %% source-node f10v02_n043 | owner=FeedForwardCore | class=other | macro=OP_FFN
    rect rgba(225, 213, 231, 0.24)
      F->>F: GELU-tanh
    end
    %% source-node f10v02_n044 | owner=SharedMatrixCore | class=other | macro=OP_FFN
    rect rgba(225, 213, 231, 0.24)
      M->>M: Elementwise gate (current fused Gate×Up)
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f10v02_n045 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
    rect rgba(218, 232, 252, 0.24)
      M->>M: down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] down_proj result
    end
    rect rgba(245, 245, 245, 0.18)
      F->>N: [HW] input for Post-FFN RMSNorm
    end
    %% source-node f10v02_n046 | owner=NormCore | class=other | macro=OP_FFN
    rect rgba(225, 213, 231, 0.24)
      N->>N: Post-FFN RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [HW] Post-FFN RMSNorm output
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f10v02_n047 | owner=OutputCommitCore | class=plus | macro=OP_FFN
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f10v02_n048 | owner=OutputCommitCore | class=output | macro=OP_FFN
    rect rgba(213, 232, 212, 0.24)
      O->>O: Block output
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_FFN done
    end
  end

```

## 11_glm_dsa_moe_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 11: GLM DSA MoE
%% Source block-atlas file: 11_glm_dsa_moe.mmd
%% Sequence file: 11_glm_dsa_moe_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: Variant 1 — DSA / MLA sparse attention + routed/shared MoE block
  Note over C,O: OP_Q_LATENT_PROJ — RMSNorm 1 → Q down-proj → Q low-rank RMSNorm → Q up-proj → Split Q
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_Q_LATENT_PROJ
  end
  loop OP_Q_LATENT_PROJ token/chunk/low-rank loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — Q latent projection input
  end
  %% source-node f11v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_Q_LATENT_PROJ
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / Q low-rank parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / Q low-rank parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / Q low-rank parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / Q low-rank parameters
  end
  %% source-node f11v01_n020 | owner=NormCore | class=other | macro=OP_Q_LATENT_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] Q latent input tile
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q down-proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q down-proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f11v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_Q_LATENT_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q down-proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>B: [HEAD/POST-NORM STAGING] Q down-proj result
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [HEAD/POST-NORM SERVICE] Q low-rank RMSNorm request / 32-lane replay
  end
  %% source-node f11v01_n024 | owner=NormCore | class=other | macro=OP_Q_LATENT_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: Q low-rank RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] Q low-rank RMSNorm output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [EDGE E_ACTBUF_TO_MATRIX] input tile for Q up-proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q up-proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q up-proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f11v01_n026 | owner=SharedMatrixCore | class=mac | macro=OP_Q_LATENT_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q up-proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Q up-proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for Split Q
  end
  %% source-node f11v01_n028 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_LATENT_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: Split Q
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>S: [HW] Split Q output
  end
  rect rgba(213, 232, 212, 0.24)
    S->>S: [HW] Q latent / NoPE / RoPE components resident
  end
  end
  rect rgba(242, 242, 242, 0.18)
    S-->>C: OP_Q_LATENT_PROJ done
  end
  Note over C,O: OP_KV_LATENT_PROJ — RMSNorm 1 replay → KV compression → KV latent RMSNorm → KV up-proj → Split KV → latent-state commit
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_KV_LATENT_PROJ
  end
  loop OP_KV_LATENT_PROJ token/chunk/low-rank loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — KV latent projection input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] KV latent projection input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / KV latent / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / KV latent / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / KV latent / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / KV latent / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=KV latent pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — KV latent pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] KV latent input tile
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — KV compression
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — KV compression
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f11v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_KV_LATENT_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: KV compression
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>B: [HEAD/POST-NORM STAGING] KV compression result
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [HEAD/POST-NORM SERVICE] KV latent RMSNorm request / 32-lane replay
  end
  %% source-node f11v01_n025 | owner=NormCore | class=other | macro=OP_KV_LATENT_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: KV latent RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] KV latent RMSNorm output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [EDGE E_ACTBUF_TO_MATRIX] input tile for KV up-proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — KV up-proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — KV up-proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f11v01_n027 | owner=SharedMatrixCore | class=mac | macro=OP_KV_LATENT_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: KV up-proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] KV up-proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for Split KV
  end
  %% source-node f11v01_n029 | owner=ElementwiseTransformCore | class=other | macro=OP_KV_LATENT_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: Split KV
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] Split KV output
  end
  rect rgba(245, 245, 245, 0.18)
    E->>E: [HW] input for RoPE
  end
  %% source-node f11v01_n030 | owner=ElementwiseTransformCore | class=other | macro=OP_KV_LATENT_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] RoPE output
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write latent KV / RoPE key state
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] state write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_KV_LATENT_PROJ done
  end
  Note over C,O: OP_DSA_INDEXER — latent Q/K read → indexer projections / relevance → Top-2048 → Sparse gather
  rect rgba(242, 242, 242, 0.18)
    C->>S: start OP_DSA_INDEXER
  end
  loop OP_DSA_INDEXER query / candidate loop
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read latent/index state
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] latent/index tile
  end
  rect rgba(245, 245, 245, 0.18)
    S->>M: [HW] input tile for Indexer Q projection
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Indexer Q projection
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Indexer Q projection
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f11v01_n031 | owner=SharedMatrixCore | class=mac | macro=OP_DSA_INDEXER
  rect rgba(218, 232, 252, 0.24)
    M->>M: Indexer Q projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>S: [HW] Indexer Q projection result
  end
  rect rgba(245, 245, 245, 0.18)
    K->>M: [HW] input tile for Indexer K projection
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Indexer K projection
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Indexer K projection
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f11v01_n032 | owner=SharedMatrixCore | class=mac | macro=OP_DSA_INDEXER
  rect rgba(218, 232, 252, 0.24)
    M->>M: Indexer K projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>S: [HW] Indexer K projection result
  end
  %% source-node f11v01_n033 | owner=SequenceCore | class=mac | macro=OP_DSA_INDEXER
  rect rgba(218, 232, 252, 0.24)
    S->>S: Indexer Q × Kᵀ
  end
  %% source-node f11v01_n034 | owner=SequenceCore | class=other | macro=OP_DSA_INDEXER
  rect rgba(225, 213, 231, 0.24)
    S->>S: Top-2048 select
  end
  %% source-node f11v01_n035 | owner=ActivationTileBufferCore | class=other | macro=OP_DSA_INDEXER
  rect rgba(225, 213, 231, 0.24)
    B->>B: Sparse gather
  end
  rect rgba(213, 232, 212, 0.24)
    B->>DDR: [HW] write selected indices / gathered rows
  end
  end
  rect rgba(242, 242, 242, 0.18)
    B-->>C: OP_DSA_INDEXER done
  end
  Note over C,O: OP_LATENT_ATTENTION_OPROJ — latent KV / selected state read → sequence mixing → O Proj → residual commit
  rect rgba(242, 242, 242, 0.18)
    C->>S: start OP_LATENT_ATTENTION_OPROJ
  end
  loop OP_LATENT_ATTENTION_OPROJ Q-block / KV-tile loop
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read latent KV / selected state / history
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] latent KV / selected state tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] latent KV / selected state response
  end
  %% source-node f11v01_n036 | owner=SequenceCore | class=mac | macro=OP_LATENT_ATTENTION_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: Selected Q × Kᵀ
  end
  %% source-node f11v01_n037 | owner=SequenceCore | class=other | macro=OP_LATENT_ATTENTION_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f11v01_n038 | owner=SequenceCore | class=mac | macro=OP_LATENT_ATTENTION_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] sequence output block + tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] tail projection request / grant
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f11v01_n039 | owner=SharedMatrixCore | class=mac | macro=OP_LATENT_ATTENTION_OPROJ
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
    T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f11v01_n040 | owner=OutputCommitCore | class=plus | macro=OP_LATENT_ATTENTION_OPROJ
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f11v01_n041 | owner=OutputCommitCore | class=output | macro=OP_LATENT_ATTENTION_OPROJ
  rect rgba(213, 232, 212, 0.24)
    O->>O: X + DSA/MLA
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_LATENT_ATTENTION_OPROJ done
  end
  Note over C,O: OP_MOE — DDR read → RMSNorm 2 → Router / Top-k → experts → merge / residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_MOE
  end
  loop OP_MOE token batch / expert group loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-sequence MoE input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-sequence MoE input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] RMSNorm 2 / router / expert parameters
  end
  %% source-node f11v01_n042 | owner=NormCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 2 output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] router input / expert queue source
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f11v01_n044 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] Router projection result
  end
  %% source-node f11v01_n045 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Router scoring
  end
  %% source-node f11v01_n046 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Top-8 + renorm
  end
  %% source-node f11v01_n047 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Dispatch / gather
  end
  rect rgba(213, 232, 212, 0.24)
    F->>B: [HW] expert queue / token grouping
  end
  rect rgba(213, 232, 212, 0.24)
    B-->>F: [HW] grouped expert activation
  end
  loop selected routed experts / grouped tokens
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f11v01_n048 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] gate_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f11v01_n049 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] up_proj result
  end
  %% source-node f11v01_n050 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: SiLU
  end
  %% source-node f11v01_n051 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Elementwise gate
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f11v01_n052 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  %% source-node f11v01_n053 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Expert weighting
  end
  %% source-node f11v01_n054 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Scatter / weighted reduce
  end
  end
  Note over F,O: Shared expert path executes for every token
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f11v01_n055 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] gate_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f11v01_n056 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] up_proj result
  end
  %% source-node f11v01_n057 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: SiLU
  end
  %% source-node f11v01_n058 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Elementwise gate
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f11v01_n059 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — Shared gate projection
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for Shared gate projection
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Shared gate projection
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Shared gate projection
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f11v01_n060 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared gate projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] Shared gate projection result
  end
  %% source-node f11v01_n061 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Sigmoid
  end
  %% source-node f11v01_n062 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Shared gating
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] expert output stream(s)
  end
  %% source-node f11v01_n063 | owner=OutputCommitCore | class=plus | macro=OP_MOE
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f11v01_n064 | owner=OutputCommitCore | class=plus | macro=OP_MOE
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f11v01_n065 | owner=OutputCommitCore | class=output | macro=OP_MOE
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_MOE done
  end

```

## 12_deepseek_v4_hybrid_moe_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 12: DeepSeek V4 Hybrid MoE
%% Source block-atlas file: 12_deepseek_v4_hybrid_moe.mmd
%% Sequence file: 12_deepseek_v4_hybrid_moe_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  alt Variant 1 — Sliding-only + mHC + MoE block
    Note over C,O: OP_MHC_INPUT — DDR read → mHC Sinkhorn matrix → mHC input mixing → mixed-stream staging
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_MHC_INPUT
    end
    loop OP_MHC_INPUT token / residual-stream loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — four residual streams
    end
    %% source-node f12v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_MHC_INPUT
    rect rgba(255, 242, 204, 0.24)
      A->>A: X
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>E: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — mHC Sinkhorn / mixing parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — mHC Sinkhorn / mixing parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] mHC Sinkhorn / mixing parameters
    end
    %% source-node f12v01_n020 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_INPUT
    rect rgba(225, 213, 231, 0.24)
      E->>E: mHC Sinkhorn matrix
    end
    %% source-node f12v01_n021 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_INPUT
    rect rgba(225, 213, 231, 0.24)
      E->>E: mHC input mixing
    end
    rect rgba(213, 232, 212, 0.24)
      E-->>B: [HW] mixed activation streams
    end
    rect rgba(213, 232, 212, 0.24)
      B->>DDR: [HW] write mixed-stream scratch / checkpoint
    end
    end
    rect rgba(242, 242, 242, 0.18)
      B-->>C: OP_MHC_INPUT done
    end
    Note over C,O: OP_Q_LORA_PROJ — RMSNorm 1 → Q LoRA A → Q LoRA RMSNorm → Partial RoPE split → Q LoRA B → YaRN RoPE
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_Q_LORA_PROJ
    end
    loop OP_Q_LORA_PROJ token/chunk/low-rank loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — mHC-mixed Q projection input
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] mHC-mixed Q projection input
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — Q LoRA / partial RoPE / YaRN parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — Q LoRA / partial RoPE / YaRN parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] Q LoRA / partial RoPE / YaRN parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] Q LoRA / partial RoPE / YaRN parameters
    end
    %% source-node f12v01_n022 | owner=NormCore | class=other | macro=OP_Q_LORA_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 1
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 1 output
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] Q LoRA input tile
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Q LoRA A
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Q LoRA A
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v01_n024 | owner=SharedMatrixCore | class=mac | macro=OP_Q_LORA_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: Q LoRA A
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>B: [HEAD/POST-NORM STAGING] Q LoRA A result
    end
    rect rgba(245, 245, 245, 0.18)
      B->>N: [HEAD/POST-NORM SERVICE] Q LoRA RMSNorm request / 32-lane replay
    end
    %% source-node f12v01_n026 | owner=NormCore | class=other | macro=OP_Q_LORA_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: Q LoRA RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HEAD/POST-NORM SERVICE] Q LoRA RMSNorm output response
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
    end
    %% source-node f12v01_n027 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_LORA_PROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: Partial RoPE split
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>M: [HW] Partial RoPE split output
    end
    rect rgba(245, 245, 245, 0.18)
      E->>M: [HW] input tile for Q LoRA B
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Q LoRA B
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Q LoRA B
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v01_n028 | owner=SharedMatrixCore | class=mac | macro=OP_Q_LORA_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: Q LoRA B
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>E: [HW] Q LoRA B result
    end
    rect rgba(245, 245, 245, 0.18)
      M->>E: [HW] input for YaRN RoPE
    end
    %% source-node f12v01_n029 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_LORA_PROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: YaRN RoPE
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>S: [HW] YaRN RoPE output
    end
    rect rgba(213, 232, 212, 0.24)
      S->>S: [HW] Q tile resident
    end
    end
    rect rgba(242, 242, 242, 0.18)
      S-->>C: OP_Q_LORA_PROJ done
    end
    Note over C,O: OP_SHARED_KV_PROJ — RMSNorm 1 replay → Shared K=V projection → K/V state commit
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_SHARED_KV_PROJ
    end
    loop OP_SHARED_KV_PROJ token/chunk loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — mHC-mixed shared K/V input
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] mHC-mixed shared K/V input
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    %% hardware replay of source operator: RMSNorm 1 | pass=shared K/V pass
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 1
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 1 output — shared K/V pass
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] shared K/V input tile
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Shared K=V projection
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Shared K=V projection
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v01_n025 | owner=SharedMatrixCore | class=mac | macro=OP_SHARED_KV_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: Shared K=V projection
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] Shared K=V projection result → projection-result dispatch
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
    end
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] write shared K/V state
    end
    end
    rect rgba(242, 242, 242, 0.18)
      K-->>C: OP_SHARED_KV_PROJ done
    end
    Note over C,O: OP_LOCAL_ATTENTION — Q tile + local K/V state → sliding attention
    rect rgba(242, 242, 242, 0.18)
      C->>S: start OP_LOCAL_ATTENTION
    end
    loop OP_LOCAL_ATTENTION Q-block / window loop
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] read local K/V window
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] local K/V tile
    end
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] local K/V response
    end
    %% source-node f12v01_n030 | owner=SequenceCore | class=mac | macro=OP_LOCAL_ATTENTION
    rect rgba(218, 232, 252, 0.24)
      S->>S: Sliding Q × Kᵀ
    end
    %% source-node f12v01_n031 | owner=SequenceCore | class=other | macro=OP_LOCAL_ATTENTION
    rect rgba(225, 213, 231, 0.24)
      S->>S: Local Softmax
    end
    %% source-node f12v01_n032 | owner=SequenceCore | class=mac | macro=OP_LOCAL_ATTENTION
    rect rgba(218, 232, 252, 0.24)
      S->>S: Local P × V
    end
    rect rgba(213, 232, 212, 0.24)
      S-->>B: [HW] local attention stream staging
    end
    end
    rect rgba(242, 242, 242, 0.18)
      B-->>C: OP_LOCAL_ATTENTION done
    end
    Note over C,O: OP_MHC_TAIL_COMMIT — attention sink / stream combine → low-rank O projection → mHC output mixing → DDR commit
    rect rgba(242, 242, 242, 0.18)
      C->>S: start OP_MHC_TAIL_COMMIT
    end
    loop OP_MHC_TAIL_COMMIT output-group / token loop
    %% source-node f12v01_n033 | owner=SequenceCore | class=other | macro=OP_MHC_TAIL_COMMIT
    rect rgba(225, 213, 231, 0.24)
      S->>S: Attention sink
    end
    %% source-node f12v01_n037 | owner=OutputCommitCore | class=plus | macro=OP_MHC_TAIL_COMMIT
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>T: [HW] selected attention stream(s)
    end
    rect rgba(242, 242, 242, 0.18)
      T->>M: [HW] grouped low-rank O request
    end
    rect rgba(245, 245, 245, 0.18)
      T->>M: [HW] input tile for Grouped O low-rank A
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Grouped O low-rank A
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Grouped O low-rank A
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v01_n034 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_TAIL_COMMIT
    rect rgba(218, 232, 252, 0.24)
      M->>M: Grouped O low-rank A
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>T: [HW] Grouped O low-rank A result
    end
    rect rgba(245, 245, 245, 0.18)
      T->>M: [HW] input tile for O low-rank B
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — O low-rank B
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — O low-rank B
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v01_n035 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_TAIL_COMMIT
    rect rgba(218, 232, 252, 0.24)
      M->>M: O low-rank B
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>E: [HW] O low-rank B result
    end
    rect rgba(245, 245, 245, 0.18)
      T->>E: [HW] input for mHC output mixing
    end
    %% source-node f12v01_n036 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_TAIL_COMMIT
    rect rgba(225, 213, 231, 0.24)
      E->>E: mHC output mixing
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>O: [HW] mHC output mixing output
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f12v01_n060 | owner=OutputCommitCore | class=plus | macro=OP_MHC_TAIL_COMMIT
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f12v01_n038 | owner=OutputCommitCore | class=output | macro=OP_MHC_TAIL_COMMIT
    rect rgba(213, 232, 212, 0.24)
      O->>O: 4 streams + Attention
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_MHC_TAIL_COMMIT done
    end
    Note over C,O: OP_MOE — DDR read → RMSNorm 2 → Router / Top-k → experts → merge / residual write
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_MOE
    end
    loop OP_MOE token batch / expert group loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — post-sequence MoE input
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] post-sequence MoE input
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>F: [HW] RMSNorm 2 / router / expert parameters
    end
    %% source-node f12v01_n039 | owner=NormCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 2
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 2 output
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>F: [HW] router input / expert queue source
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — Router projection
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v01_n041 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: Router projection
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] Router projection result
    end
    %% source-node f12v01_n042 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Router scoring
    end
    %% source-node f12v01_n043 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Top-6 + renorm
    end
    %% source-node f12v01_n044 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Dispatch / gather
    end
    rect rgba(213, 232, 212, 0.24)
      F->>B: [HW] expert queue / token grouping
    end
    rect rgba(213, 232, 212, 0.24)
      B-->>F: [HW] grouped expert activation
    end
    loop selected routed experts / grouped tokens
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v01_n045 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] gate_proj result
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v01_n046 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] up_proj result
    end
    %% source-node f12v01_n047 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: SiLU
    end
    %% source-node f12v01_n048 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Elementwise gate
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v01_n049 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] down_proj result
    end
    %% source-node f12v01_n050 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Expert weighting
    end
    %% source-node f12v01_n051 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Scatter / weighted reduce
    end
    end
    Note over F,O: Shared expert path executes for every token
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v01_n052 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] gate_proj result
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v01_n053 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] up_proj result
    end
    %% source-node f12v01_n054 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: SiLU
    end
    %% source-node f12v01_n055 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Elementwise gate
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v01_n056 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] down_proj result
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — Shared gate projection
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for Shared gate projection
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Shared gate projection
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Shared gate projection
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v01_n057 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: Shared gate projection
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] Shared gate projection result
    end
    %% source-node f12v01_n058 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Sigmoid
    end
    %% source-node f12v01_n059 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Shared gating
    end
    rect rgba(245, 245, 245, 0.18)
      F-->>O: [HW] expert output stream(s)
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f12v01_n061 | owner=OutputCommitCore | class=plus | macro=OP_MOE
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f12v01_n062 | owner=OutputCommitCore | class=output | macro=OP_MOE
    rect rgba(213, 232, 212, 0.24)
      O->>O: Block output
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_MOE done
    end
  else Variant 2 — Compressed Sparse Attention + mHC + MoE block
    Note over C,O: OP_MHC_INPUT — DDR read → mHC Sinkhorn matrix → mHC input mixing → mixed-stream staging
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_MHC_INPUT
    end
    loop OP_MHC_INPUT token / residual-stream loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — four residual streams
    end
    %% source-node f12v02_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_MHC_INPUT
    rect rgba(255, 242, 204, 0.24)
      A->>A: X
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>E: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — mHC Sinkhorn / mixing parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — mHC Sinkhorn / mixing parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] mHC Sinkhorn / mixing parameters
    end
    %% source-node f12v02_n020 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_INPUT
    rect rgba(225, 213, 231, 0.24)
      E->>E: mHC Sinkhorn matrix
    end
    %% source-node f12v02_n021 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_INPUT
    rect rgba(225, 213, 231, 0.24)
      E->>E: mHC input mixing
    end
    rect rgba(213, 232, 212, 0.24)
      E-->>B: [HW] mixed activation streams
    end
    rect rgba(213, 232, 212, 0.24)
      B->>DDR: [HW] write mixed-stream scratch / checkpoint
    end
    end
    rect rgba(242, 242, 242, 0.18)
      B-->>C: OP_MHC_INPUT done
    end
    Note over C,O: OP_Q_LORA_PROJ — RMSNorm 1 → Q LoRA A → Q LoRA RMSNorm → Partial RoPE split → Q LoRA B → YaRN RoPE
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_Q_LORA_PROJ
    end
    loop OP_Q_LORA_PROJ token/chunk/low-rank loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — mHC-mixed Q projection input
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] mHC-mixed Q projection input
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — Q LoRA / partial RoPE / YaRN parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — Q LoRA / partial RoPE / YaRN parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] Q LoRA / partial RoPE / YaRN parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] Q LoRA / partial RoPE / YaRN parameters
    end
    %% source-node f12v02_n022 | owner=NormCore | class=other | macro=OP_Q_LORA_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 1
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 1 output
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] Q LoRA input tile
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Q LoRA A
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Q LoRA A
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v02_n024 | owner=SharedMatrixCore | class=mac | macro=OP_Q_LORA_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: Q LoRA A
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>B: [HEAD/POST-NORM STAGING] Q LoRA A result
    end
    rect rgba(245, 245, 245, 0.18)
      B->>N: [HEAD/POST-NORM SERVICE] Q LoRA RMSNorm request / 32-lane replay
    end
    %% source-node f12v02_n026 | owner=NormCore | class=other | macro=OP_Q_LORA_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: Q LoRA RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HEAD/POST-NORM SERVICE] Q LoRA RMSNorm output response
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
    end
    %% source-node f12v02_n027 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_LORA_PROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: Partial RoPE split
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>M: [HW] Partial RoPE split output
    end
    rect rgba(245, 245, 245, 0.18)
      E->>M: [HW] input tile for Q LoRA B
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Q LoRA B
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Q LoRA B
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v02_n028 | owner=SharedMatrixCore | class=mac | macro=OP_Q_LORA_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: Q LoRA B
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>E: [HW] Q LoRA B result
    end
    rect rgba(245, 245, 245, 0.18)
      M->>E: [HW] input for YaRN RoPE
    end
    %% source-node f12v02_n029 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_LORA_PROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: YaRN RoPE
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>S: [HW] YaRN RoPE output
    end
    rect rgba(213, 232, 212, 0.24)
      S->>S: [HW] Q tile resident
    end
    end
    rect rgba(242, 242, 242, 0.18)
      S-->>C: OP_Q_LORA_PROJ done
    end
    Note over C,O: OP_SHARED_KV_PROJ — RMSNorm 1 replay → Shared K=V projection → K/V state commit
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_SHARED_KV_PROJ
    end
    loop OP_SHARED_KV_PROJ token/chunk loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — mHC-mixed shared K/V input
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] mHC-mixed shared K/V input
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    %% hardware replay of source operator: RMSNorm 1 | pass=shared K/V pass
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 1
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 1 output — shared K/V pass
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] shared K/V input tile
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Shared K=V projection
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Shared K=V projection
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v02_n025 | owner=SharedMatrixCore | class=mac | macro=OP_SHARED_KV_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: Shared K=V projection
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] Shared K=V projection result → projection-result dispatch
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
    end
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] write shared K/V state
    end
    end
    rect rgba(242, 242, 242, 0.18)
      K-->>C: OP_SHARED_KV_PROJ done
    end
    Note over C,O: OP_LOCAL_ATTENTION — Q tile + local K/V state → sliding attention
    rect rgba(242, 242, 242, 0.18)
      C->>S: start OP_LOCAL_ATTENTION
    end
    loop OP_LOCAL_ATTENTION Q-block / window loop
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] read local K/V window
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] local K/V tile
    end
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] local K/V response
    end
    %% source-node f12v02_n030 | owner=SequenceCore | class=mac | macro=OP_LOCAL_ATTENTION
    rect rgba(218, 232, 252, 0.24)
      S->>S: Sliding Q × Kᵀ
    end
    %% source-node f12v02_n031 | owner=SequenceCore | class=other | macro=OP_LOCAL_ATTENTION
    rect rgba(225, 213, 231, 0.24)
      S->>S: Local Softmax
    end
    %% source-node f12v02_n032 | owner=SequenceCore | class=mac | macro=OP_LOCAL_ATTENTION
    rect rgba(218, 232, 252, 0.24)
      S->>S: Local P × V
    end
    rect rgba(213, 232, 212, 0.24)
      S-->>B: [HW] local attention stream staging
    end
    end
    rect rgba(242, 242, 242, 0.18)
      B-->>C: OP_LOCAL_ATTENTION done
    end
    Note over C,O: OP_CSA_INDEX — Block KV compressor → Lightning indexer → Top-512 blocks → sparse attention
    rect rgba(242, 242, 242, 0.18)
      C->>M: start OP_CSA_INDEX
    end
    loop OP_CSA_INDEX compressed-block / selected-block loop
    rect rgba(245, 245, 245, 0.18)
      K->>M: [HW] input tile for Block KV compressor
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Block KV compressor
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Block KV compressor
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v02_n033 | owner=SharedMatrixCore | class=mac | macro=OP_CSA_INDEX
    rect rgba(218, 232, 252, 0.24)
      M->>M: Block KV compressor
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>M: [HW] Block KV compressor result
    end
    rect rgba(245, 245, 245, 0.18)
      M->>M: [HW] input tile for Lightning indexer
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Lightning indexer
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Lightning indexer
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v02_n034 | owner=SharedMatrixCore | class=mac | macro=OP_CSA_INDEX
    rect rgba(218, 232, 252, 0.24)
      M->>M: Lightning indexer
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>S: [HW] Lightning indexer result
    end
    %% source-node f12v02_n035 | owner=SequenceCore | class=other | macro=OP_CSA_INDEX
    rect rgba(225, 213, 231, 0.24)
      S->>S: Top-512 blocks
    end
    %% source-node f12v02_n036 | owner=SequenceCore | class=mac | macro=OP_CSA_INDEX
    rect rgba(218, 232, 252, 0.24)
      S->>S: Sparse Q × Kᵀ
    end
    %% source-node f12v02_n037 | owner=SequenceCore | class=other | macro=OP_CSA_INDEX
    rect rgba(225, 213, 231, 0.24)
      S->>S: Sparse Softmax
    end
    %% source-node f12v02_n038 | owner=SequenceCore | class=mac | macro=OP_CSA_INDEX
    rect rgba(218, 232, 252, 0.24)
      S->>S: Sparse P × V / Online O recurrence (selected V)
    end
    rect rgba(213, 232, 212, 0.24)
      S-->>B: [HW] sparse attention stream staging
    end
    end
    rect rgba(242, 242, 242, 0.18)
      B-->>C: OP_CSA_INDEX done
    end
    Note over C,O: OP_MHC_TAIL_COMMIT — attention sink / stream combine → low-rank O projection → mHC output mixing → DDR commit
    rect rgba(242, 242, 242, 0.18)
      C->>S: start OP_MHC_TAIL_COMMIT
    end
    loop OP_MHC_TAIL_COMMIT output-group / token loop
    %% source-node f12v02_n039 | owner=SequenceCore | class=other | macro=OP_MHC_TAIL_COMMIT
    rect rgba(225, 213, 231, 0.24)
      S->>S: Attention sink
    end
    %% source-node f12v02_n040 | owner=SequenceCore | class=plus | macro=OP_MHC_TAIL_COMMIT
    rect rgba(255, 255, 255, 0.28)
      S->>S: +
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>T: [HW] selected attention stream(s)
    end
    rect rgba(242, 242, 242, 0.18)
      T->>M: [HW] grouped low-rank O request
    end
    rect rgba(245, 245, 245, 0.18)
      T->>M: [HW] input tile for Grouped O low-rank A
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Grouped O low-rank A
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Grouped O low-rank A
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v02_n041 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_TAIL_COMMIT
    rect rgba(218, 232, 252, 0.24)
      M->>M: Grouped O low-rank A
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>T: [HW] Grouped O low-rank A result
    end
    rect rgba(245, 245, 245, 0.18)
      T->>M: [HW] input tile for O low-rank B
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — O low-rank B
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — O low-rank B
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v02_n042 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_TAIL_COMMIT
    rect rgba(218, 232, 252, 0.24)
      M->>M: O low-rank B
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>E: [HW] O low-rank B result
    end
    rect rgba(245, 245, 245, 0.18)
      T->>E: [HW] input for mHC output mixing
    end
    %% source-node f12v02_n043 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_TAIL_COMMIT
    rect rgba(225, 213, 231, 0.24)
      E->>E: mHC output mixing
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>O: [HW] mHC output mixing output
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f12v02_n044 | owner=OutputCommitCore | class=plus | macro=OP_MHC_TAIL_COMMIT
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f12v02_n045 | owner=OutputCommitCore | class=output | macro=OP_MHC_TAIL_COMMIT
    rect rgba(213, 232, 212, 0.24)
      O->>O: 4 streams + CSA
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_MHC_TAIL_COMMIT done
    end
    Note over C,O: OP_MOE — DDR read → RMSNorm 2 → Router / Top-k → experts → merge / residual write
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_MOE
    end
    loop OP_MOE token batch / expert group loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — post-sequence MoE input
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] post-sequence MoE input
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>F: [HW] RMSNorm 2 / router / expert parameters
    end
    %% source-node f12v02_n046 | owner=NormCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 2
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 2 output
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>F: [HW] router input / expert queue source
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — Router projection
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v02_n048 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: Router projection
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] Router projection result
    end
    %% source-node f12v02_n049 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Router scoring
    end
    %% source-node f12v02_n050 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Top-6 + renorm
    end
    %% source-node f12v02_n051 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Dispatch / gather
    end
    rect rgba(213, 232, 212, 0.24)
      F->>B: [HW] expert queue / token grouping
    end
    rect rgba(213, 232, 212, 0.24)
      B-->>F: [HW] grouped expert activation
    end
    loop selected routed experts / grouped tokens
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v02_n052 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] gate_proj result
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v02_n053 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] up_proj result
    end
    %% source-node f12v02_n054 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: SiLU
    end
    %% source-node f12v02_n055 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Elementwise gate
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v02_n056 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] down_proj result
    end
    %% source-node f12v02_n057 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Expert weighting
    end
    %% source-node f12v02_n058 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Scatter / weighted reduce
    end
    end
    Note over F,O: Shared expert path executes for every token
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v02_n059 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] gate_proj result
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v02_n060 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] up_proj result
    end
    %% source-node f12v02_n061 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: SiLU
    end
    %% source-node f12v02_n062 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Elementwise gate
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v02_n063 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] down_proj result
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — Shared gate projection
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for Shared gate projection
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Shared gate projection
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Shared gate projection
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v02_n064 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: Shared gate projection
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] Shared gate projection result
    end
    %% source-node f12v02_n065 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Sigmoid
    end
    %% source-node f12v02_n066 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Shared gating
    end
    rect rgba(245, 245, 245, 0.18)
      F-->>O: [HW] expert output stream(s)
    end
    %% source-node f12v02_n067 | owner=OutputCommitCore | class=plus | macro=OP_MOE
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f12v02_n068 | owner=OutputCommitCore | class=plus | macro=OP_MOE
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f12v02_n069 | owner=OutputCommitCore | class=output | macro=OP_MOE
    rect rgba(213, 232, 212, 0.24)
      O->>O: Block output
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_MOE done
    end
  else Variant 3 — Hierarchical Compressed Attention + mHC + MoE block
    Note over C,O: OP_MHC_INPUT — DDR read → mHC Sinkhorn matrix → mHC input mixing → mixed-stream staging
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_MHC_INPUT
    end
    loop OP_MHC_INPUT token / residual-stream loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — four residual streams
    end
    %% source-node f12v03_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_MHC_INPUT
    rect rgba(255, 242, 204, 0.24)
      A->>A: X
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>E: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — mHC Sinkhorn / mixing parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — mHC Sinkhorn / mixing parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] mHC Sinkhorn / mixing parameters
    end
    %% source-node f12v03_n020 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_INPUT
    rect rgba(225, 213, 231, 0.24)
      E->>E: mHC Sinkhorn matrix
    end
    %% source-node f12v03_n021 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_INPUT
    rect rgba(225, 213, 231, 0.24)
      E->>E: mHC input mixing
    end
    rect rgba(213, 232, 212, 0.24)
      E-->>B: [HW] mixed activation streams
    end
    rect rgba(213, 232, 212, 0.24)
      B->>DDR: [HW] write mixed-stream scratch / checkpoint
    end
    end
    rect rgba(242, 242, 242, 0.18)
      B-->>C: OP_MHC_INPUT done
    end
    Note over C,O: OP_Q_LORA_PROJ — RMSNorm 1 → Q LoRA A → Q LoRA RMSNorm → Partial RoPE split → Q LoRA B → YaRN RoPE
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_Q_LORA_PROJ
    end
    loop OP_Q_LORA_PROJ token/chunk/low-rank loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — mHC-mixed Q projection input
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] mHC-mixed Q projection input
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — Q LoRA / partial RoPE / YaRN parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — Q LoRA / partial RoPE / YaRN parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] Q LoRA / partial RoPE / YaRN parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] Q LoRA / partial RoPE / YaRN parameters
    end
    %% source-node f12v03_n022 | owner=NormCore | class=other | macro=OP_Q_LORA_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 1
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 1 output
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] Q LoRA input tile
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Q LoRA A
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Q LoRA A
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v03_n024 | owner=SharedMatrixCore | class=mac | macro=OP_Q_LORA_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: Q LoRA A
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>B: [HEAD/POST-NORM STAGING] Q LoRA A result
    end
    rect rgba(245, 245, 245, 0.18)
      B->>N: [HEAD/POST-NORM SERVICE] Q LoRA RMSNorm request / 32-lane replay
    end
    %% source-node f12v03_n026 | owner=NormCore | class=other | macro=OP_Q_LORA_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: Q LoRA RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HEAD/POST-NORM SERVICE] Q LoRA RMSNorm output response
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
    end
    %% source-node f12v03_n027 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_LORA_PROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: Partial RoPE split
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>M: [HW] Partial RoPE split output
    end
    rect rgba(245, 245, 245, 0.18)
      E->>M: [HW] input tile for Q LoRA B
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Q LoRA B
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Q LoRA B
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v03_n028 | owner=SharedMatrixCore | class=mac | macro=OP_Q_LORA_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: Q LoRA B
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>E: [HW] Q LoRA B result
    end
    rect rgba(245, 245, 245, 0.18)
      M->>E: [HW] input for YaRN RoPE
    end
    %% source-node f12v03_n029 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_LORA_PROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: YaRN RoPE
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>S: [HW] YaRN RoPE output
    end
    rect rgba(213, 232, 212, 0.24)
      S->>S: [HW] Q tile resident
    end
    end
    rect rgba(242, 242, 242, 0.18)
      S-->>C: OP_Q_LORA_PROJ done
    end
    Note over C,O: OP_SHARED_KV_PROJ — RMSNorm 1 replay → Shared K=V projection → K/V state commit
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_SHARED_KV_PROJ
    end
    loop OP_SHARED_KV_PROJ token/chunk loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — mHC-mixed shared K/V input
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] mHC-mixed shared K/V input
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    %% hardware replay of source operator: RMSNorm 1 | pass=shared K/V pass
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 1
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 1 output — shared K/V pass
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] shared K/V input tile
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Shared K=V projection
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Shared K=V projection
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v03_n025 | owner=SharedMatrixCore | class=mac | macro=OP_SHARED_KV_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: Shared K=V projection
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] Shared K=V projection result → projection-result dispatch
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
    end
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] write shared K/V state
    end
    end
    rect rgba(242, 242, 242, 0.18)
      K-->>C: OP_SHARED_KV_PROJ done
    end
    Note over C,O: OP_LOCAL_ATTENTION — Q tile + local K/V state → sliding attention
    rect rgba(242, 242, 242, 0.18)
      C->>S: start OP_LOCAL_ATTENTION
    end
    loop OP_LOCAL_ATTENTION Q-block / window loop
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] read local K/V window
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] local K/V tile
    end
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] local K/V response
    end
    %% source-node f12v03_n030 | owner=SequenceCore | class=mac | macro=OP_LOCAL_ATTENTION
    rect rgba(218, 232, 252, 0.24)
      S->>S: Sliding Q × Kᵀ
    end
    %% source-node f12v03_n031 | owner=SequenceCore | class=other | macro=OP_LOCAL_ATTENTION
    rect rgba(225, 213, 231, 0.24)
      S->>S: Local Softmax
    end
    %% source-node f12v03_n032 | owner=SequenceCore | class=mac | macro=OP_LOCAL_ATTENTION
    rect rgba(218, 232, 252, 0.24)
      S->>S: Local P × V
    end
    rect rgba(213, 232, 212, 0.24)
      S-->>B: [HW] local attention stream staging
    end
    end
    rect rgba(242, 242, 242, 0.18)
      B-->>C: OP_LOCAL_ATTENTION done
    end
    Note over C,O: OP_HCA_COMPRESS — Hierarchical compressor L1/L2 → compressed attention
    rect rgba(242, 242, 242, 0.18)
      C->>M: start OP_HCA_COMPRESS
    end
    loop OP_HCA_COMPRESS hierarchy / compressed-block loop
    rect rgba(245, 245, 245, 0.18)
      K->>M: [HW] input tile for Hierarchical compressor L1
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Hierarchical compressor L1
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Hierarchical compressor L1
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v03_n033 | owner=SharedMatrixCore | class=mac | macro=OP_HCA_COMPRESS
    rect rgba(218, 232, 252, 0.24)
      M->>M: Hierarchical compressor L1
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>M: [HW] Hierarchical compressor L1 result
    end
    rect rgba(245, 245, 245, 0.18)
      K->>M: [HW] input tile for Hierarchical compressor L2
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Hierarchical compressor L2
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Hierarchical compressor L2
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v03_n034 | owner=SharedMatrixCore | class=mac | macro=OP_HCA_COMPRESS
    rect rgba(218, 232, 252, 0.24)
      M->>M: Hierarchical compressor L2
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>M: [HW] Hierarchical compressor L2 result
    end
    %% source-node f12v03_n035 | owner=SequenceCore | class=mac | macro=OP_HCA_COMPRESS
    rect rgba(218, 232, 252, 0.24)
      S->>S: Q × compressed Kᵀ
    end
    %% source-node f12v03_n036 | owner=SequenceCore | class=other | macro=OP_HCA_COMPRESS
    rect rgba(225, 213, 231, 0.24)
      S->>S: Compressed Softmax
    end
    %% source-node f12v03_n037 | owner=SequenceCore | class=mac | macro=OP_HCA_COMPRESS
    rect rgba(218, 232, 252, 0.24)
      S->>S: P × compressed V
    end
    rect rgba(213, 232, 212, 0.24)
      S-->>B: [HW] hierarchical attention stream staging
    end
    end
    rect rgba(242, 242, 242, 0.18)
      B-->>C: OP_HCA_COMPRESS done
    end
    Note over C,O: OP_MHC_TAIL_COMMIT — attention sink / stream combine → low-rank O projection → mHC output mixing → DDR commit
    rect rgba(242, 242, 242, 0.18)
      C->>S: start OP_MHC_TAIL_COMMIT
    end
    loop OP_MHC_TAIL_COMMIT output-group / token loop
    %% source-node f12v03_n038 | owner=SequenceCore | class=other | macro=OP_MHC_TAIL_COMMIT
    rect rgba(225, 213, 231, 0.24)
      S->>S: Attention sink
    end
    %% source-node f12v03_n039 | owner=SequenceCore | class=plus | macro=OP_MHC_TAIL_COMMIT
    rect rgba(255, 255, 255, 0.28)
      S->>S: +
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>T: [HW] selected attention stream(s)
    end
    rect rgba(242, 242, 242, 0.18)
      T->>M: [HW] grouped low-rank O request
    end
    rect rgba(245, 245, 245, 0.18)
      T->>M: [HW] input tile for Grouped O low-rank A
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Grouped O low-rank A
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Grouped O low-rank A
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v03_n040 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_TAIL_COMMIT
    rect rgba(218, 232, 252, 0.24)
      M->>M: Grouped O low-rank A
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>T: [HW] Grouped O low-rank A result
    end
    rect rgba(245, 245, 245, 0.18)
      T->>M: [HW] input tile for O low-rank B
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — O low-rank B
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — O low-rank B
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v03_n041 | owner=SharedMatrixCore | class=mac | macro=OP_MHC_TAIL_COMMIT
    rect rgba(218, 232, 252, 0.24)
      M->>M: O low-rank B
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>E: [HW] O low-rank B result
    end
    rect rgba(245, 245, 245, 0.18)
      T->>E: [HW] input for mHC output mixing
    end
    %% source-node f12v03_n042 | owner=ElementwiseTransformCore | class=other | macro=OP_MHC_TAIL_COMMIT
    rect rgba(225, 213, 231, 0.24)
      E->>E: mHC output mixing
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>O: [HW] mHC output mixing output
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f12v03_n043 | owner=OutputCommitCore | class=plus | macro=OP_MHC_TAIL_COMMIT
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f12v03_n044 | owner=OutputCommitCore | class=output | macro=OP_MHC_TAIL_COMMIT
    rect rgba(213, 232, 212, 0.24)
      O->>O: 4 streams + HCA
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_MHC_TAIL_COMMIT done
    end
    Note over C,O: OP_MOE — DDR read → RMSNorm 2 → Router / Top-k → experts → merge / residual write
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_MOE
    end
    loop OP_MOE token batch / expert group loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — post-sequence MoE input
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] post-sequence MoE input
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>F: [HW] RMSNorm 2 / router / expert parameters
    end
    %% source-node f12v03_n045 | owner=NormCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 2
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 2 output
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>F: [HW] router input / expert queue source
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — Router projection
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v03_n047 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: Router projection
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] Router projection result
    end
    %% source-node f12v03_n048 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Router scoring
    end
    %% source-node f12v03_n049 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Top-6 + renorm
    end
    %% source-node f12v03_n050 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Dispatch / gather
    end
    rect rgba(213, 232, 212, 0.24)
      F->>B: [HW] expert queue / token grouping
    end
    rect rgba(213, 232, 212, 0.24)
      B-->>F: [HW] grouped expert activation
    end
    loop selected routed experts / grouped tokens
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v03_n051 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] gate_proj result
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v03_n052 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] up_proj result
    end
    %% source-node f12v03_n053 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: SiLU
    end
    %% source-node f12v03_n054 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Elementwise gate
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v03_n055 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] down_proj result
    end
    %% source-node f12v03_n056 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Expert weighting
    end
    %% source-node f12v03_n057 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Scatter / weighted reduce
    end
    end
    Note over F,O: Shared expert path executes for every token
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v03_n058 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] gate_proj result
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v03_n059 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] up_proj result
    end
    %% source-node f12v03_n060 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: SiLU
    end
    %% source-node f12v03_n061 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Elementwise gate
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v03_n062 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] down_proj result
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — Shared gate projection
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for Shared gate projection
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Shared gate projection
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Shared gate projection
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f12v03_n063 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: Shared gate projection
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] Shared gate projection result
    end
    %% source-node f12v03_n064 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Sigmoid
    end
    %% source-node f12v03_n065 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Shared gating
    end
    rect rgba(245, 245, 245, 0.18)
      F-->>O: [HW] expert output stream(s)
    end
    %% source-node f12v03_n066 | owner=OutputCommitCore | class=plus | macro=OP_MOE
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f12v03_n067 | owner=OutputCommitCore | class=plus | macro=OP_MOE
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f12v03_n068 | owner=OutputCommitCore | class=output | macro=OP_MOE
    rect rgba(213, 232, 212, 0.24)
      O->>O: Block output
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_MOE done
    end
  end

```

## 13_gemma3_dense_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 13: Gemma 3 Dense
%% Source block-atlas file: 13_gemma3_dense.mmd
%% Sequence file: 13_gemma3_dense_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  alt Variant 1 — Local sliding-attention GeGLU block
    Note over C,O: OP_K_PROJ — Pre-Attention RMSNorm → K Proj → K Head RMSNorm → Local RoPE → K cache
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_K_PROJ
    end
    loop OP_K_PROJ autonomous token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — K pass activation / residual
    end
    %% source-node f13v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_K_PROJ
    rect rgba(255, 242, 204, 0.24)
      A->>A: X
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] Pre-Attention RMSNorm / position parameters
    end
    %% source-node f13v01_n020 | owner=NormCore | class=other | macro=OP_K_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: Pre-Attention RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] Pre-Attention RMSNorm output
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] resident tile — K pass
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — K Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — K Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f13v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_K_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: K Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>B: [HEAD/POST-NORM STAGING] K Proj result
    end
    rect rgba(245, 245, 245, 0.18)
      B->>N: [HEAD/POST-NORM SERVICE] K Head RMSNorm request / 32-lane replay
    end
    %% source-node f13v01_n025 | owner=NormCore | class=other | macro=OP_K_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: K Head RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HEAD/POST-NORM SERVICE] K Head RMSNorm output response
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
    end
    %% source-node f13v01_n027 | owner=ElementwiseTransformCore | class=other | macro=OP_K_PROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: Local RoPE
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>K: [HW] Local RoPE output
    end
    %% source-node f13v01_n029 | owner=KVStateCore | class=state | macro=OP_K_PROJ
    rect rgba(213, 232, 212, 0.24)
      K->>K: K cache
    end
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] write K cache
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] write response
    end
    end
    rect rgba(242, 242, 242, 0.18)
      K-->>C: OP_K_PROJ done
    end
    Note over C,O: OP_V_PROJ — Pre-Attention RMSNorm → V Proj → V cache
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_V_PROJ
    end
    loop OP_V_PROJ autonomous token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — V pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] V pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] Pre-Attention RMSNorm / position parameters
    end
    %% hardware replay of source operator: Pre-Attention RMSNorm | pass=V pass
    rect rgba(225, 213, 231, 0.24)
      N->>N: Pre-Attention RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] Pre-Attention RMSNorm output — V pass
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] resident tile — V pass
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — V Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — V Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f13v01_n024 | owner=SharedMatrixCore | class=mac | macro=OP_V_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: V Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V Proj result → projection-result dispatch
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
    end
    %% source-node f13v01_n030 | owner=KVStateCore | class=state | macro=OP_V_PROJ
    rect rgba(213, 232, 212, 0.24)
      K->>K: V cache
    end
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] write V cache
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] write response
    end
    end
    rect rgba(242, 242, 242, 0.18)
      K-->>C: OP_V_PROJ done
    end
    Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: Pre-Attention RMSNorm → Q Proj → Q Head RMSNorm → Local RoPE
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_Q_ATTN_OPROJ
    end
    loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — Q pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] Q pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] Pre-Attention RMSNorm / position parameters
    end
    %% hardware replay of source operator: Pre-Attention RMSNorm | pass=Q pass
    rect rgba(225, 213, 231, 0.24)
      N->>N: Pre-Attention RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] Pre-Attention RMSNorm output — Q pass
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] resident tile — Q pass
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Q Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Q Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f13v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: Q Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>B: [HEAD/POST-NORM STAGING] Q Proj result
    end
    rect rgba(245, 245, 245, 0.18)
      B->>N: [HEAD/POST-NORM SERVICE] Q Head RMSNorm request / 32-lane replay
    end
    %% source-node f13v01_n026 | owner=NormCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: Q Head RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HEAD/POST-NORM SERVICE] Q Head RMSNorm output response
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
    end
    %% source-node f13v01_n028 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: Local RoPE
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>S: [HW] Local RoPE output
    end
    rect rgba(213, 232, 212, 0.24)
      E-->>S: [HW] commit Q tile / query stream
    end
    rect rgba(213, 232, 212, 0.24)
      S->>S: [HW] Q tile resident for subsequent sequence op
    end
    end
  Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → O Proj → residual commit
  loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] read K/V state / history
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] K/V state tile
    end
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] K/V state response
    end
    %% source-node f13v01_n031 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] KV-group state broadcast / lane map
    end
    rect rgba(225, 213, 231, 0.24)
      S->>S: K head repeat ×2
    end
    %% source-node f13v01_n032 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] KV-group state broadcast / lane map
    end
    rect rgba(225, 213, 231, 0.24)
      S->>S: V head repeat ×2
    end
    %% source-node f13v01_n033 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      S->>S: Q × Kᵀ
    end
    %% source-node f13v01_n034 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      S->>S: Softmax FP32
    end
    %% source-node f13v01_n035 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      S->>S: P × V / Online O recurrence (β×V + α×Oold)
    end
    rect rgba(245, 245, 245, 0.18)
      S-->>T: [HW] sequence output block + tags
    end
    rect rgba(242, 242, 242, 0.18)
      T->>M: [HW] tail projection request / grant
    end
    rect rgba(245, 245, 245, 0.18)
      T->>M: [HW] input tile for O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f13v01_n036 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
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
      T->>N: [HW] input for Post-Attention RMSNorm
    end
    %% source-node f13v01_n037 | owner=NormCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: Post-Attention RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [HW] Post-Attention RMSNorm output
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f13v01_n038 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f13v01_n039 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      O->>O: X + Attention
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_Q_ATTN_OPROJ done
    end
    Note over C,O: OP_FFN — DDR read → Pre-FFN RMSNorm → dense FFN → residual write
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_FFN
    end
    loop OP_FFN token/chunk/weight-tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — post-attention / FFN input
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] post-attention / FFN input
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — Pre-FFN RMSNorm / activation parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — Pre-FFN RMSNorm / activation parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] Pre-FFN RMSNorm / activation parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>F: [HW] Pre-FFN RMSNorm / activation parameters
    end
    %% source-node f13v01_n040 | owner=NormCore | class=other | macro=OP_FFN
    rect rgba(225, 213, 231, 0.24)
      N->>N: Pre-FFN RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] Pre-FFN RMSNorm output
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>F: [HW] FFN resident activation tile
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f13v01_n042 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
    rect rgba(218, 232, 252, 0.24)
      M->>M: gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M->>M: [HW] gate tile held locally for fused SwiGLU
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f13v01_n043 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
    rect rgba(218, 232, 252, 0.24)
      M->>M: up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M->>M: [HW] up tile held locally for fused SwiGLU
    end
    %% source-node f13v01_n044 | owner=FeedForwardCore | class=other | macro=OP_FFN
    rect rgba(225, 213, 231, 0.24)
      F->>F: GELU-tanh
    end
    %% source-node f13v01_n045 | owner=SharedMatrixCore | class=other | macro=OP_FFN
    rect rgba(225, 213, 231, 0.24)
      M->>M: Elementwise gate (current fused Gate×Up)
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f13v01_n046 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
    rect rgba(218, 232, 252, 0.24)
      M->>M: down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] down_proj result
    end
    rect rgba(245, 245, 245, 0.18)
      F->>N: [HW] input for Post-FFN RMSNorm
    end
    %% source-node f13v01_n047 | owner=NormCore | class=other | macro=OP_FFN
    rect rgba(225, 213, 231, 0.24)
      N->>N: Post-FFN RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [HW] Post-FFN RMSNorm output
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f13v01_n048 | owner=OutputCommitCore | class=plus | macro=OP_FFN
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f13v01_n049 | owner=OutputCommitCore | class=output | macro=OP_FFN
    rect rgba(213, 232, 212, 0.24)
      O->>O: Block output
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_FFN done
    end
  else Variant 2 — Global full-attention GeGLU block
    Note over C,O: OP_K_PROJ — Pre-Attention RMSNorm → K Proj → K Head RMSNorm → Global RoPE → K cache
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_K_PROJ
    end
    loop OP_K_PROJ autonomous token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — K pass activation / residual
    end
    %% source-node f13v02_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_K_PROJ
    rect rgba(255, 242, 204, 0.24)
      A->>A: X
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] Pre-Attention RMSNorm / position parameters
    end
    %% source-node f13v02_n020 | owner=NormCore | class=other | macro=OP_K_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: Pre-Attention RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] Pre-Attention RMSNorm output
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] resident tile — K pass
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — K Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — K Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f13v02_n022 | owner=SharedMatrixCore | class=mac | macro=OP_K_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: K Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>B: [HEAD/POST-NORM STAGING] K Proj result
    end
    rect rgba(245, 245, 245, 0.18)
      B->>N: [HEAD/POST-NORM SERVICE] K Head RMSNorm request / 32-lane replay
    end
    %% source-node f13v02_n025 | owner=NormCore | class=other | macro=OP_K_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: K Head RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HEAD/POST-NORM SERVICE] K Head RMSNorm output response
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
    end
    %% source-node f13v02_n027 | owner=ElementwiseTransformCore | class=other | macro=OP_K_PROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: Global RoPE
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>K: [HW] Global RoPE output
    end
    %% source-node f13v02_n029 | owner=KVStateCore | class=state | macro=OP_K_PROJ
    rect rgba(213, 232, 212, 0.24)
      K->>K: K cache
    end
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] write K cache
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] write response
    end
    end
    rect rgba(242, 242, 242, 0.18)
      K-->>C: OP_K_PROJ done
    end
    Note over C,O: OP_V_PROJ — Pre-Attention RMSNorm → V Proj → V cache
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_V_PROJ
    end
    loop OP_V_PROJ autonomous token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — V pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] V pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] Pre-Attention RMSNorm / position parameters
    end
    %% hardware replay of source operator: Pre-Attention RMSNorm | pass=V pass
    rect rgba(225, 213, 231, 0.24)
      N->>N: Pre-Attention RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] Pre-Attention RMSNorm output — V pass
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] resident tile — V pass
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — V Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — V Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f13v02_n024 | owner=SharedMatrixCore | class=mac | macro=OP_V_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: V Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V Proj result → projection-result dispatch
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
    end
    %% source-node f13v02_n030 | owner=KVStateCore | class=state | macro=OP_V_PROJ
    rect rgba(213, 232, 212, 0.24)
      K->>K: V cache
    end
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] write V cache
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] write response
    end
    end
    rect rgba(242, 242, 242, 0.18)
      K-->>C: OP_V_PROJ done
    end
    Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: Pre-Attention RMSNorm → Q Proj → Q Head RMSNorm → Global RoPE
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_Q_ATTN_OPROJ
    end
    loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — Q pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] Q pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] Pre-Attention RMSNorm / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] Pre-Attention RMSNorm / position parameters
    end
    %% hardware replay of source operator: Pre-Attention RMSNorm | pass=Q pass
    rect rgba(225, 213, 231, 0.24)
      N->>N: Pre-Attention RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] Pre-Attention RMSNorm output — Q pass
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] resident tile — Q pass
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Q Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Q Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f13v02_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: Q Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>B: [HEAD/POST-NORM STAGING] Q Proj result
    end
    rect rgba(245, 245, 245, 0.18)
      B->>N: [HEAD/POST-NORM SERVICE] Q Head RMSNorm request / 32-lane replay
    end
    %% source-node f13v02_n026 | owner=NormCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: Q Head RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HEAD/POST-NORM SERVICE] Q Head RMSNorm output response
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
    end
    %% source-node f13v02_n028 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: Global RoPE
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>S: [HW] Global RoPE output
    end
    rect rgba(213, 232, 212, 0.24)
      E-->>S: [HW] commit Q tile / query stream
    end
    rect rgba(213, 232, 212, 0.24)
      S->>S: [HW] Q tile resident for subsequent sequence op
    end
    end
  Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → O Proj → residual commit
  loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] read K/V state / history
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] K/V state tile
    end
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] K/V state response
    end
    %% source-node f13v02_n031 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] KV-group state broadcast / lane map
    end
    rect rgba(225, 213, 231, 0.24)
      S->>S: K head repeat ×2
    end
    %% source-node f13v02_n032 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] KV-group state broadcast / lane map
    end
    rect rgba(225, 213, 231, 0.24)
      S->>S: V head repeat ×2
    end
    %% source-node f13v02_n033 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      S->>S: Q × Kᵀ
    end
    %% source-node f13v02_n034 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      S->>S: Softmax FP32
    end
    %% source-node f13v02_n035 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      S->>S: P × V / Online O recurrence (β×V + α×Oold)
    end
    rect rgba(245, 245, 245, 0.18)
      S-->>T: [HW] sequence output block + tags
    end
    rect rgba(242, 242, 242, 0.18)
      T->>M: [HW] tail projection request / grant
    end
    rect rgba(245, 245, 245, 0.18)
      T->>M: [HW] input tile for O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f13v02_n036 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
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
      T->>N: [HW] input for Post-Attention RMSNorm
    end
    %% source-node f13v02_n037 | owner=NormCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: Post-Attention RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [HW] Post-Attention RMSNorm output
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f13v02_n038 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f13v02_n039 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      O->>O: X + Attention
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_Q_ATTN_OPROJ done
    end
    Note over C,O: OP_FFN — DDR read → Pre-FFN RMSNorm → dense FFN → residual write
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_FFN
    end
    loop OP_FFN token/chunk/weight-tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — post-attention / FFN input
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] post-attention / FFN input
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — Pre-FFN RMSNorm / activation parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — Pre-FFN RMSNorm / activation parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] Pre-FFN RMSNorm / activation parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>F: [HW] Pre-FFN RMSNorm / activation parameters
    end
    %% source-node f13v02_n040 | owner=NormCore | class=other | macro=OP_FFN
    rect rgba(225, 213, 231, 0.24)
      N->>N: Pre-FFN RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] Pre-FFN RMSNorm output
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>F: [HW] FFN resident activation tile
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f13v02_n042 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
    rect rgba(218, 232, 252, 0.24)
      M->>M: gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M->>M: [HW] gate tile held locally for fused SwiGLU
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f13v02_n043 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
    rect rgba(218, 232, 252, 0.24)
      M->>M: up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M->>M: [HW] up tile held locally for fused SwiGLU
    end
    %% source-node f13v02_n044 | owner=FeedForwardCore | class=other | macro=OP_FFN
    rect rgba(225, 213, 231, 0.24)
      F->>F: GELU-tanh
    end
    %% source-node f13v02_n045 | owner=SharedMatrixCore | class=other | macro=OP_FFN
    rect rgba(225, 213, 231, 0.24)
      M->>M: Elementwise gate (current fused Gate×Up)
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f13v02_n046 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
    rect rgba(218, 232, 252, 0.24)
      M->>M: down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] down_proj result
    end
    rect rgba(245, 245, 245, 0.18)
      F->>N: [HW] input for Post-FFN RMSNorm
    end
    %% source-node f13v02_n047 | owner=NormCore | class=other | macro=OP_FFN
    rect rgba(225, 213, 231, 0.24)
      N->>N: Post-FFN RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [HW] Post-FFN RMSNorm output
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f13v02_n048 | owner=OutputCommitCore | class=plus | macro=OP_FFN
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f13v02_n049 | owner=OutputCommitCore | class=output | macro=OP_FFN
    rect rgba(213, 232, 212, 0.24)
      O->>O: Block output
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_FFN done
    end
  end

```

## 14_deepseek_v3_r1_mla_moe_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 14: DeepSeek V3 / R1 MLA MoE
%% Source block-atlas file: 14_deepseek_v3_r1_mla_moe.mmd
%% Sequence file: 14_deepseek_v3_r1_mla_moe_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: Variant 1 — MLA + routed/shared MoE block
  Note over C,O: OP_Q_LATENT_PROJ — RMSNorm 1 → Q low-rank A → Q LoRA RMSNorm → Q low-rank B → Split Q
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_Q_LATENT_PROJ
  end
  loop OP_Q_LATENT_PROJ token/chunk/low-rank loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — Q latent projection input
  end
  %% source-node f14v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_Q_LATENT_PROJ
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / Q low-rank parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / Q low-rank parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / Q low-rank parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / Q low-rank parameters
  end
  %% source-node f14v01_n020 | owner=NormCore | class=other | macro=OP_Q_LATENT_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] Q latent input tile
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q low-rank A
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q low-rank A
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f14v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_Q_LATENT_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q low-rank A
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>B: [HEAD/POST-NORM STAGING] Q low-rank A result
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [HEAD/POST-NORM SERVICE] Q LoRA RMSNorm request / 32-lane replay
  end
  %% source-node f14v01_n024 | owner=NormCore | class=other | macro=OP_Q_LATENT_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: Q LoRA RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] Q LoRA RMSNorm output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [EDGE E_ACTBUF_TO_MATRIX] input tile for Q low-rank B
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q low-rank B
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q low-rank B
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f14v01_n026 | owner=SharedMatrixCore | class=mac | macro=OP_Q_LATENT_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q low-rank B
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Q low-rank B result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for Split Q
  end
  %% source-node f14v01_n028 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_LATENT_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: Split Q
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>S: [HW] Split Q output
  end
  rect rgba(213, 232, 212, 0.24)
    S->>S: [HW] Q latent / NoPE / RoPE components resident
  end
  end
  rect rgba(242, 242, 242, 0.18)
    S-->>C: OP_Q_LATENT_PROJ done
  end
  Note over C,O: OP_KV_LATENT_PROJ — RMSNorm 1 replay → KV compression → KV latent RMSNorm → KV expansion → Split KV → latent-state commit
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_KV_LATENT_PROJ
  end
  loop OP_KV_LATENT_PROJ token/chunk/low-rank loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — KV latent projection input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] KV latent projection input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / KV latent / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / KV latent / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / KV latent / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / KV latent / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=KV latent pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — KV latent pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] KV latent input tile
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — KV compression
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — KV compression
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f14v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_KV_LATENT_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: KV compression
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>B: [HEAD/POST-NORM STAGING] KV compression result
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [HEAD/POST-NORM SERVICE] KV latent RMSNorm request / 32-lane replay
  end
  %% source-node f14v01_n025 | owner=NormCore | class=other | macro=OP_KV_LATENT_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: KV latent RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] KV latent RMSNorm output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [EDGE E_ACTBUF_TO_MATRIX] input tile for KV expansion
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — KV expansion
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — KV expansion
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f14v01_n027 | owner=SharedMatrixCore | class=mac | macro=OP_KV_LATENT_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: KV expansion
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] KV expansion result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for Split KV
  end
  %% source-node f14v01_n029 | owner=ElementwiseTransformCore | class=other | macro=OP_KV_LATENT_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: Split KV
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] Split KV output
  end
  rect rgba(245, 245, 245, 0.18)
    E->>E: [HW] input for YaRN RoPE
  end
  %% source-node f14v01_n030 | owner=ElementwiseTransformCore | class=other | macro=OP_KV_LATENT_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: YaRN RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] YaRN RoPE output
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write latent KV / RoPE key state
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] state write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_KV_LATENT_PROJ done
  end
  Note over C,O: OP_LATENT_ATTENTION_OPROJ — latent KV / selected state read → sequence mixing → O Proj → residual commit
  rect rgba(242, 242, 242, 0.18)
    C->>S: start OP_LATENT_ATTENTION_OPROJ
  end
  loop OP_LATENT_ATTENTION_OPROJ Q-block / KV-tile loop
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read latent KV / selected state / history
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] latent KV / selected state tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] latent KV / selected state response
  end
  %% source-node f14v01_n031 | owner=SequenceCore | class=mac | macro=OP_LATENT_ATTENTION_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: MLA Q × Kᵀ
  end
  %% source-node f14v01_n032 | owner=SequenceCore | class=other | macro=OP_LATENT_ATTENTION_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f14v01_n033 | owner=SequenceCore | class=mac | macro=OP_LATENT_ATTENTION_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] sequence output block + tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] tail projection request / grant
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f14v01_n034 | owner=SharedMatrixCore | class=mac | macro=OP_LATENT_ATTENTION_OPROJ
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
    T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f14v01_n035 | owner=OutputCommitCore | class=plus | macro=OP_LATENT_ATTENTION_OPROJ
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f14v01_n036 | owner=OutputCommitCore | class=output | macro=OP_LATENT_ATTENTION_OPROJ
  rect rgba(213, 232, 212, 0.24)
    O->>O: X + MLA
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_LATENT_ATTENTION_OPROJ done
  end
  Note over C,O: OP_MOE — DDR read → RMSNorm 2 → Router / Top-k → experts → merge / residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_MOE
  end
  loop OP_MOE token batch / expert group loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-sequence MoE input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-sequence MoE input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] RMSNorm 2 / router / expert parameters
  end
  %% source-node f14v01_n037 | owner=NormCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 2 output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] router input / expert queue source
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f14v01_n039 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] Router projection result
  end
  %% source-node f14v01_n040 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Router scoring
  end
  %% source-node f14v01_n041 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Top-8 + renorm
  end
  %% source-node f14v01_n042 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Dispatch / gather
  end
  rect rgba(213, 232, 212, 0.24)
    F->>B: [HW] expert queue / token grouping
  end
  rect rgba(213, 232, 212, 0.24)
    B-->>F: [HW] grouped expert activation
  end
  loop selected routed experts / grouped tokens
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f14v01_n043 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] gate_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f14v01_n044 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] up_proj result
  end
  %% source-node f14v01_n045 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: SiLU
  end
  %% source-node f14v01_n046 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Elementwise gate
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f14v01_n047 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  %% source-node f14v01_n048 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Expert weighting
  end
  %% source-node f14v01_n049 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Scatter / weighted reduce
  end
  end
  Note over F,O: Shared expert path executes for every token
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f14v01_n050 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] gate_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f14v01_n051 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] up_proj result
  end
  %% source-node f14v01_n052 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: SiLU
  end
  %% source-node f14v01_n053 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Elementwise gate
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f14v01_n054 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — Shared gate projection
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for Shared gate projection
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Shared gate projection
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Shared gate projection
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f14v01_n055 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared gate projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] Shared gate projection result
  end
  %% source-node f14v01_n056 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Sigmoid
  end
  %% source-node f14v01_n057 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Shared gating
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] expert output stream(s)
  end
  %% source-node f14v01_n058 | owner=OutputCommitCore | class=plus | macro=OP_MOE
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f14v01_n059 | owner=OutputCommitCore | class=plus | macro=OP_MOE
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f14v01_n060 | owner=OutputCommitCore | class=output | macro=OP_MOE
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_MOE done
  end

```

## 15_gpt_neox_pythia_dense_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 15: GPT-NeoX / Pythia Dense
%% Source block-atlas file: 15_gpt_neox_pythia_dense.mmd
%% Sequence file: 15_gpt_neox_pythia_dense_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: Variant 1 — Parallel residual RoPE MHA + GELU block
  Note over C,O: OP_K_PROJ — LayerNorm (attn) → K Proj → RoPE
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_K_PROJ
  end
  loop OP_K_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — attention K pass activation / residual
  end
  %% source-node f15v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_K_PROJ
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — LayerNorm (attn) / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — LayerNorm (attn) / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] LayerNorm (attn) / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] LayerNorm (attn) / position parameters
  end
  %% source-node f15v01_n020 | owner=NormCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: LayerNorm (attn)
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] LayerNorm (attn) output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — attention K pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f15v01_n024 | owner=SharedMatrixCore | class=mac | macro=OP_K_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: K Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] K Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for RoPE
  end
  %% source-node f15v01_n027 | owner=ElementwiseTransformCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] RoPE output
  end
  rect rgba(213, 232, 212, 0.24)
    K->>K: [HW] K state staging
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write K state
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_K_PROJ done
  end
  Note over C,O: OP_V_PROJ — LayerNorm (attn) → V Proj
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_V_PROJ
  end
  loop OP_V_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — attention V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] attention V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — LayerNorm (attn) / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — LayerNorm (attn) / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] LayerNorm (attn) / position parameters
  end
  %% hardware replay of source operator: LayerNorm (attn) | pass=attention V pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: LayerNorm (attn)
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] LayerNorm (attn) output — attention V pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — attention V pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f15v01_n026 | owner=SharedMatrixCore | class=mac | macro=OP_V_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: V Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V Proj result → projection-result dispatch
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
  end
  rect rgba(213, 232, 212, 0.24)
    K->>K: [HW] V state staging
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write V state
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_V_PROJ done
  end
  Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: LayerNorm (attn) → Q Proj → RoPE
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_Q_ATTN_OPROJ
  end
  loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — attention Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] attention Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — LayerNorm (attn) / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — LayerNorm (attn) / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] LayerNorm (attn) / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] LayerNorm (attn) / position parameters
  end
  %% hardware replay of source operator: LayerNorm (attn) | pass=attention Q pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: LayerNorm (attn)
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] LayerNorm (attn) output — attention Q pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — attention Q pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f15v01_n025 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Q Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for RoPE
  end
  %% source-node f15v01_n028 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>S: [HW] RoPE output
  end
  rect rgba(213, 232, 212, 0.24)
    E-->>S: [HW] commit Q tile / query stream
  end
  rect rgba(213, 232, 212, 0.24)
    S->>S: [HW] Q tile resident for subsequent sequence op
  end
  end
  rect rgba(242, 242, 242, 0.18)
    S-->>C: OP_Q_PROJ done
  end
  Note over C,O: OP_PARALLEL_ATTN_FFN — Attention and MLP branches execute from the same residual input, then join
  rect rgba(242, 242, 242, 0.18)
    C->>S: start OP_PARALLEL_ATTN_FFN
  end
  loop OP_PARALLEL_ATTN_FFN token / tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — parallel residual input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] parallel residual input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — LayerNorm (MLP) / branch parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — LayerNorm (MLP) / branch parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] LayerNorm (MLP) / branch parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>S: [HW] LayerNorm (MLP) / branch parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] LayerNorm (MLP) / branch parameters
  end
  par Attention branch
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read K/V state
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] K/V state tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] K/V response
  end
  %% source-node f15v01_n029 | owner=SequenceCore | class=mac | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q × Kᵀ
  end
  %% source-node f15v01_n030 | owner=SequenceCore | class=other | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f15v01_n031 | owner=SequenceCore | class=mac | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] attention output block
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] OProj request
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f15v01_n032 | owner=SharedMatrixCore | class=mac | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: O Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>T: [EDGE E_MATRIX_TO_TAIL] O Proj result tile
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>O: [EDGE E_MATRIX_TO_COMMIT] OProj result stream128
  end
  and MLP branch
  %% source-node f15v01_n021 | owner=NormCore | class=other | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(225, 213, 231, 0.24)
    N->>N: LayerNorm (MLP)
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] LayerNorm (MLP) output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] MLP branch input
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — fc1
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for fc1
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — fc1
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — fc1
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f15v01_n033 | owner=SharedMatrixCore | class=mac | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: fc1
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] fc1 result
  end
  %% source-node f15v01_n034 | owner=FeedForwardCore | class=other | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(225, 213, 231, 0.24)
    F->>F: GELU
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — fc2
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for fc2
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — fc2
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — fc2
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f15v01_n035 | owner=SharedMatrixCore | class=mac | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: fc2
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] fc2 result
  end
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>O: [HW] attention branch result
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] MLP branch result
  end
  %% source-node f15v01_n036 | owner=OutputCommitCore | class=plus | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f15v01_n037 | owner=OutputCommitCore | class=plus | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f15v01_n038 | owner=OutputCommitCore | class=output | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_PARALLEL_ATTN_FFN done
  end

```

## 16_gemma4_moe_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 16: Gemma 4 MoE
%% Source block-atlas file: 16_gemma4_moe.mmd
%% Sequence file: 16_gemma4_moe_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  alt Variant 1 — Sliding-window attention + routed/shared MoE block
    Note over C,O: OP_KV_SHARED_PROJ — RMSNorm 1 → K=V shared Proj → K/V state commit
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_KV_SHARED_PROJ
    end
    loop OP_KV_SHARED_PROJ token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — K/V shared projection activation
    end
    %% source-node f16v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_KV_SHARED_PROJ
    rect rgba(255, 242, 204, 0.24)
      A->>A: X
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — RMSNorm 1 / K position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — RMSNorm 1 / K position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] RMSNorm 1 / K position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] RMSNorm 1 / K position parameters
    end
    %% source-node f16v01_n020 | owner=NormCore | class=other | macro=OP_KV_SHARED_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 1
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 1 output
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] K/V shared input tile
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — K=V shared Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — K=V shared Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_KV_SHARED_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: K=V shared Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>B: [HEAD/POST-NORM STAGING] K=V shared Proj result
    end
    rect rgba(245, 245, 245, 0.18)
      B->>N: [HEAD/POST-NORM SERVICE] K Head RMSNorm request / 32-lane replay
    end
    %% source-node f16v01_n024 | owner=NormCore | class=other | macro=OP_KV_SHARED_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: K Head RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HEAD/POST-NORM SERVICE] K Head RMSNorm output response
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
    end
    %% source-node f16v01_n026 | owner=ElementwiseTransformCore | class=other | macro=OP_KV_SHARED_PROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: RoPE
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>K: [HW] RoPE output
    end
    %% source-node f16v01_n028 | owner=KVStateCore | class=state | macro=OP_KV_SHARED_PROJ
    rect rgba(213, 232, 212, 0.24)
      K->>K: K cache
    end
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] write K cache
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] write response
    end
    %% source-node f16v01_n029 | owner=KVStateCore | class=state | macro=OP_KV_SHARED_PROJ
    rect rgba(213, 232, 212, 0.24)
      K->>K: V cache
    end
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] write V cache
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] write response
    end
    end
    rect rgba(242, 242, 242, 0.18)
      K-->>C: OP_KV_SHARED_PROJ done
    end
    Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: RMSNorm 1 → Q Proj → Q Head RMSNorm → RoPE
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_Q_ATTN_OPROJ
    end
    loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — Q pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] Q pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] RMSNorm 1 / position parameters
    end
    %% hardware replay of source operator: RMSNorm 1 | pass=Q pass
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 1
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 1 output — Q pass
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] resident tile — Q pass
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Q Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Q Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: Q Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>B: [HEAD/POST-NORM STAGING] Q Proj result
    end
    rect rgba(245, 245, 245, 0.18)
      B->>N: [HEAD/POST-NORM SERVICE] Q Head RMSNorm request / 32-lane replay
    end
    %% source-node f16v01_n025 | owner=NormCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: Q Head RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HEAD/POST-NORM SERVICE] Q Head RMSNorm output response
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
    end
    %% source-node f16v01_n027 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: RoPE
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>S: [HW] RoPE output
    end
    rect rgba(213, 232, 212, 0.24)
      E-->>S: [HW] commit Q tile / query stream
    end
    rect rgba(213, 232, 212, 0.24)
      S->>S: [HW] Q tile resident for subsequent sequence op
    end
    end
  Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → O Proj → residual commit
  loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] read K/V state / history
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] K/V state tile
    end
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] K/V state response
    end
    %% source-node f16v01_n030 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] KV-group state broadcast / lane map
    end
    rect rgba(225, 213, 231, 0.24)
      S->>S: K head repeat ×2
    end
    %% source-node f16v01_n031 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] KV-group state broadcast / lane map
    end
    rect rgba(225, 213, 231, 0.24)
      S->>S: V head repeat ×2
    end
    %% source-node f16v01_n032 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      S->>S: Q × Kᵀ
    end
    %% source-node f16v01_n033 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      S->>S: Softmax FP32
    end
    %% source-node f16v01_n034 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      S->>S: P × V / Online O recurrence (β×V + α×Oold)
    end
    rect rgba(245, 245, 245, 0.18)
      S-->>T: [HW] sequence output block + tags
    end
    rect rgba(242, 242, 242, 0.18)
      T->>M: [HW] tail projection request / grant
    end
    rect rgba(245, 245, 245, 0.18)
      T->>M: [HW] input tile for O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v01_n035 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
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
      T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f16v01_n036 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f16v01_n037 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      O->>O: X + Attention
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_Q_ATTN_OPROJ done
    end
    Note over C,O: OP_MOE — DDR read → RMSNorm 2 → Router / Top-k → experts → merge / residual write
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_MOE
    end
    loop OP_MOE token batch / expert group loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — post-sequence MoE input
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] post-sequence MoE input
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>F: [HW] RMSNorm 2 / router / expert parameters
    end
    %% source-node f16v01_n038 | owner=NormCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 2
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 2 output
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>F: [HW] router input / expert queue source
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — Router projection
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v01_n040 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: Router projection
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] Router projection result
    end
    %% source-node f16v01_n041 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Router scoring
    end
    %% source-node f16v01_n042 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Top-8 + renorm
    end
    %% source-node f16v01_n043 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Dispatch / gather
    end
    rect rgba(213, 232, 212, 0.24)
      F->>B: [HW] expert queue / token grouping
    end
    rect rgba(213, 232, 212, 0.24)
      B-->>F: [HW] grouped expert activation
    end
    loop selected routed experts / grouped tokens
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v01_n044 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] gate_proj result
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v01_n045 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] up_proj result
    end
    %% source-node f16v01_n046 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: GELU-tanh
    end
    %% source-node f16v01_n047 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Elementwise gate
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v01_n048 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] down_proj result
    end
    %% source-node f16v01_n049 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Expert weighting
    end
    %% source-node f16v01_n050 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Scatter / weighted reduce
    end
    end
    Note over F,O: Shared expert path executes for every token
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v01_n051 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] gate_proj result
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v01_n052 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] up_proj result
    end
    %% source-node f16v01_n053 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: GELU-tanh
    end
    %% source-node f16v01_n054 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Elementwise gate
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v01_n055 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] down_proj result
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — Shared gate projection
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for Shared gate projection
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Shared gate projection
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Shared gate projection
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v01_n056 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: Shared gate projection
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] Shared gate projection result
    end
    %% source-node f16v01_n057 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Sigmoid
    end
    %% source-node f16v01_n058 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Shared gating
    end
    rect rgba(245, 245, 245, 0.18)
      F-->>O: [HW] expert output stream(s)
    end
    %% source-node f16v01_n059 | owner=OutputCommitCore | class=plus | macro=OP_MOE
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f16v01_n060 | owner=OutputCommitCore | class=plus | macro=OP_MOE
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f16v01_n061 | owner=OutputCommitCore | class=output | macro=OP_MOE
    rect rgba(213, 232, 212, 0.24)
      O->>O: Block output
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_MOE done
    end
  else Variant 2 — Full attention + routed/shared MoE block
    Note over C,O: OP_KV_SHARED_PROJ — RMSNorm 1 → K=V shared Proj → K/V state commit
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_KV_SHARED_PROJ
    end
    loop OP_KV_SHARED_PROJ token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — K/V shared projection activation
    end
    %% source-node f16v02_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_KV_SHARED_PROJ
    rect rgba(255, 242, 204, 0.24)
      A->>A: X
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — RMSNorm 1 / K position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — RMSNorm 1 / K position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] RMSNorm 1 / K position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] RMSNorm 1 / K position parameters
    end
    %% source-node f16v02_n020 | owner=NormCore | class=other | macro=OP_KV_SHARED_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 1
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 1 output
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] K/V shared input tile
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — K=V shared Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — K=V shared Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v02_n022 | owner=SharedMatrixCore | class=mac | macro=OP_KV_SHARED_PROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: K=V shared Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>B: [HEAD/POST-NORM STAGING] K=V shared Proj result
    end
    rect rgba(245, 245, 245, 0.18)
      B->>N: [HEAD/POST-NORM SERVICE] K Head RMSNorm request / 32-lane replay
    end
    %% source-node f16v02_n024 | owner=NormCore | class=other | macro=OP_KV_SHARED_PROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: K Head RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HEAD/POST-NORM SERVICE] K Head RMSNorm output response
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
    end
    %% source-node f16v02_n026 | owner=ElementwiseTransformCore | class=other | macro=OP_KV_SHARED_PROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: RoPE
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>K: [HW] RoPE output
    end
    %% source-node f16v02_n028 | owner=KVStateCore | class=state | macro=OP_KV_SHARED_PROJ
    rect rgba(213, 232, 212, 0.24)
      K->>K: K cache
    end
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] write K cache
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] write response
    end
    %% source-node f16v02_n029 | owner=KVStateCore | class=state | macro=OP_KV_SHARED_PROJ
    rect rgba(213, 232, 212, 0.24)
      K->>K: V cache
    end
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] write V cache
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] write response
    end
    end
    rect rgba(242, 242, 242, 0.18)
      K-->>C: OP_KV_SHARED_PROJ done
    end
    Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: RMSNorm 1 → Q Proj → Q Head RMSNorm → RoPE
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_Q_ATTN_OPROJ
    end
    loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — Q pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] Q pass activation / residual
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] RMSNorm 1 / position parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>E: [HW] RMSNorm 1 / position parameters
    end
    %% hardware replay of source operator: RMSNorm 1 | pass=Q pass
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 1
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 1 output — Q pass
    end
    rect rgba(245, 245, 245, 0.18)
      B->>M: [HW] resident tile — Q pass
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Q Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Q Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v02_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      M->>M: Q Proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>B: [HEAD/POST-NORM STAGING] Q Proj result
    end
    rect rgba(245, 245, 245, 0.18)
      B->>N: [HEAD/POST-NORM SERVICE] Q Head RMSNorm request / 32-lane replay
    end
    %% source-node f16v02_n025 | owner=NormCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      N->>N: Q Head RMSNorm
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HEAD/POST-NORM SERVICE] Q Head RMSNorm output response
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>E: [HEAD-NORM REPLAY] normalized head stream to position/split transform
    end
    %% source-node f16v02_n027 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      E->>E: RoPE
    end
    rect rgba(245, 245, 245, 0.18)
      E-->>S: [HW] RoPE output
    end
    rect rgba(213, 232, 212, 0.24)
      E-->>S: [HW] commit Q tile / query stream
    end
    rect rgba(213, 232, 212, 0.24)
      S->>S: [HW] Q tile resident for subsequent sequence op
    end
    end
  Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → O Proj → residual commit
  loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
    rect rgba(213, 232, 212, 0.24)
      K->>DDR: [HW] read K/V state / history
    end
    rect rgba(213, 232, 212, 0.24)
      DDR-->>K: [HW] K/V state tile
    end
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] K/V state response
    end
    %% source-node f16v02_n030 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] KV-group state broadcast / lane map
    end
    rect rgba(225, 213, 231, 0.24)
      S->>S: K head repeat ×2
    end
    %% source-node f16v02_n031 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      K-->>S: [HW] KV-group state broadcast / lane map
    end
    rect rgba(225, 213, 231, 0.24)
      S->>S: V head repeat ×2
    end
    %% source-node f16v02_n032 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      S->>S: Q × Kᵀ
    end
    %% source-node f16v02_n033 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
    rect rgba(225, 213, 231, 0.24)
      S->>S: Softmax FP32
    end
    %% source-node f16v02_n034 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
    rect rgba(218, 232, 252, 0.24)
      S->>S: P × V / Online O recurrence (β×V + α×Oold)
    end
    rect rgba(245, 245, 245, 0.18)
      S-->>T: [HW] sequence output block + tags
    end
    rect rgba(242, 242, 242, 0.18)
      T->>M: [HW] tail projection request / grant
    end
    rect rgba(245, 245, 245, 0.18)
      T->>M: [HW] input tile for O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — O Proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v02_n035 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
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
      T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f16v02_n036 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f16v02_n037 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
    rect rgba(213, 232, 212, 0.24)
      O->>O: X + Attention
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_Q_ATTN_OPROJ done
    end
    Note over C,O: OP_MOE — DDR read → RMSNorm 2 → Router / Top-k → experts → merge / residual write
    rect rgba(242, 242, 242, 0.18)
      C->>A: start OP_MOE
    end
    loop OP_MOE token batch / expert group loop
    rect rgba(255, 242, 204, 0.24)
      A->>DDR: [HW] AXI read request — post-sequence MoE input
    end
    rect rgba(255, 242, 204, 0.24)
      DDR-->>A: [HW] post-sequence MoE input
    end
    rect rgba(255, 242, 204, 0.24)
      A-->>N: [HW] activation / residual stream
    end
    rect rgba(248, 206, 204, 0.24)
      P->>DDR: [HW] parameter read request — RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>P: [HW] parameter stream — RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>N: [HW] RMSNorm 2 / router / expert parameters
    end
    rect rgba(248, 206, 204, 0.24)
      P-->>F: [HW] RMSNorm 2 / router / expert parameters
    end
    %% source-node f16v02_n038 | owner=NormCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      N->>N: RMSNorm 2
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>B: [HW] RMSNorm 2 output
    end
    rect rgba(245, 245, 245, 0.18)
      B-->>F: [HW] router input / expert queue source
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — Router projection
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Router projection
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v02_n040 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: Router projection
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] Router projection result
    end
    %% source-node f16v02_n041 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Router scoring
    end
    %% source-node f16v02_n042 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Top-8 + renorm
    end
    %% source-node f16v02_n043 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Dispatch / gather
    end
    rect rgba(213, 232, 212, 0.24)
      F->>B: [HW] expert queue / token grouping
    end
    rect rgba(213, 232, 212, 0.24)
      B-->>F: [HW] grouped expert activation
    end
    loop selected routed experts / grouped tokens
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v02_n044 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] gate_proj result
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v02_n045 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] up_proj result
    end
    %% source-node f16v02_n046 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: GELU-tanh
    end
    %% source-node f16v02_n047 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Elementwise gate
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v02_n048 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] down_proj result
    end
    %% source-node f16v02_n049 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Expert weighting
    end
    %% source-node f16v02_n050 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Scatter / weighted reduce
    end
    end
    Note over F,O: Shared expert path executes for every token
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — gate_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v02_n051 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: gate_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] gate_proj result
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — up_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v02_n052 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: up_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] up_proj result
    end
    %% source-node f16v02_n053 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: GELU-tanh
    end
    %% source-node f16v02_n054 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Elementwise gate
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — down_proj
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v02_n055 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: down_proj
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] down_proj result
    end
    rect rgba(242, 242, 242, 0.18)
      F->>M: [HW] matrix request — Shared gate projection
    end
    rect rgba(245, 245, 245, 0.18)
      F->>M: [HW] input tile for Shared gate projection
    end
    rect rgba(248, 206, 204, 0.24)
      W->>DDR: [HW] weight read request — Shared gate projection
    end
    rect rgba(248, 206, 204, 0.24)
      DDR-->>W: [HW] weight stream — Shared gate projection
    end
    rect rgba(248, 206, 204, 0.24)
      W-->>M: [HW] weight tile stream
    end
    %% source-node f16v02_n056 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
    rect rgba(218, 232, 252, 0.24)
      M->>M: Shared gate projection
    end
    rect rgba(245, 245, 245, 0.18)
      M-->>F: [HW] Shared gate projection result
    end
    %% source-node f16v02_n057 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Sigmoid
    end
    %% source-node f16v02_n058 | owner=FeedForwardCore | class=other | macro=OP_MOE
    rect rgba(225, 213, 231, 0.24)
      F->>F: Shared gating
    end
    rect rgba(245, 245, 245, 0.18)
      F-->>O: [HW] expert output stream(s)
    end
    %% source-node f16v02_n059 | owner=OutputCommitCore | class=plus | macro=OP_MOE
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    rect rgba(245, 245, 245, 0.18)
      N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
    end
    %% source-node f16v02_n060 | owner=OutputCommitCore | class=plus | macro=OP_MOE
    rect rgba(255, 255, 255, 0.28)
      O->>O: +
    end
    %% source-node f16v02_n061 | owner=OutputCommitCore | class=output | macro=OP_MOE
    rect rgba(213, 232, 212, 0.24)
      O->>O: Block output
    end
    end
    rect rgba(242, 242, 242, 0.18)
      O-->>C: OP_MOE done
    end
  end

```

## 17_kimi_k3_hybrid_moe_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 17: Kimi K3 Hybrid MoE
%% Source block-atlas file: 17_kimi_k3_hybrid_moe.mmd
%% Sequence file: 17_kimi_k3_hybrid_moe_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: Variant 1 — Representative MLA + sparse MoE block
  Note over C,O: OP_Q_LATENT_PROJ — RMSNorm 1 → Q low-rank A → Q LoRA RMSNorm → Q low-rank B → Split Q
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_Q_LATENT_PROJ
  end
  loop OP_Q_LATENT_PROJ token/chunk/low-rank loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — Q latent projection input
  end
  %% source-node f17v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_Q_LATENT_PROJ
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / Q low-rank parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / Q low-rank parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / Q low-rank parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / Q low-rank parameters
  end
  %% source-node f17v01_n020 | owner=NormCore | class=other | macro=OP_Q_LATENT_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] Q latent input tile
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q low-rank A
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q low-rank A
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f17v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_Q_LATENT_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q low-rank A
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>B: [HEAD/POST-NORM STAGING] Q low-rank A result
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [HEAD/POST-NORM SERVICE] Q LoRA RMSNorm request / 32-lane replay
  end
  %% source-node f17v01_n024 | owner=NormCore | class=other | macro=OP_Q_LATENT_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: Q LoRA RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] Q LoRA RMSNorm output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [EDGE E_ACTBUF_TO_MATRIX] input tile for Q low-rank B
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q low-rank B
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q low-rank B
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f17v01_n026 | owner=SharedMatrixCore | class=mac | macro=OP_Q_LATENT_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q low-rank B
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Q low-rank B result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for Split Q
  end
  %% source-node f17v01_n028 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_LATENT_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: Split Q
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>S: [HW] Split Q output
  end
  rect rgba(213, 232, 212, 0.24)
    S->>S: [HW] Q latent / NoPE / RoPE components resident
  end
  end
  rect rgba(242, 242, 242, 0.18)
    S-->>C: OP_Q_LATENT_PROJ done
  end
  Note over C,O: OP_KV_LATENT_PROJ — RMSNorm 1 replay → KV compression → KV latent RMSNorm → KV expansion → Split KV → latent-state commit
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_KV_LATENT_PROJ
  end
  loop OP_KV_LATENT_PROJ token/chunk/low-rank loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — KV latent projection input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] KV latent projection input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / KV latent / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / KV latent / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / KV latent / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / KV latent / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=KV latent pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — KV latent pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] KV latent input tile
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — KV compression
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — KV compression
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f17v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_KV_LATENT_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: KV compression
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>B: [HEAD/POST-NORM STAGING] KV compression result
  end
  rect rgba(245, 245, 245, 0.18)
    B->>N: [HEAD/POST-NORM SERVICE] KV latent RMSNorm request / 32-lane replay
  end
  %% source-node f17v01_n025 | owner=NormCore | class=other | macro=OP_KV_LATENT_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: KV latent RMSNorm
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [EDGE E_NORM_TO_ACTBUF] KV latent RMSNorm output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [EDGE E_ACTBUF_TO_MATRIX] input tile for KV expansion
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — KV expansion
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — KV expansion
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f17v01_n027 | owner=SharedMatrixCore | class=mac | macro=OP_KV_LATENT_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: KV expansion
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] KV expansion result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for Split KV
  end
  %% source-node f17v01_n029 | owner=ElementwiseTransformCore | class=other | macro=OP_KV_LATENT_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: Split KV
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] Split KV output
  end
  rect rgba(245, 245, 245, 0.18)
    E->>E: [HW] input for YaRN RoPE
  end
  %% source-node f17v01_n030 | owner=ElementwiseTransformCore | class=other | macro=OP_KV_LATENT_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: YaRN RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] YaRN RoPE output
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write latent KV / RoPE key state
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] state write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_KV_LATENT_PROJ done
  end
  Note over C,O: OP_LATENT_ATTENTION_OPROJ — latent KV / selected state read → sequence mixing → O Proj → residual commit
  rect rgba(242, 242, 242, 0.18)
    C->>S: start OP_LATENT_ATTENTION_OPROJ
  end
  loop OP_LATENT_ATTENTION_OPROJ Q-block / KV-tile loop
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read latent KV / selected state / history
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] latent KV / selected state tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] latent KV / selected state response
  end
  %% source-node f17v01_n031 | owner=SequenceCore | class=mac | macro=OP_LATENT_ATTENTION_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: MLA Q × Kᵀ
  end
  %% source-node f17v01_n032 | owner=SequenceCore | class=other | macro=OP_LATENT_ATTENTION_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f17v01_n033 | owner=SequenceCore | class=mac | macro=OP_LATENT_ATTENTION_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] sequence output block + tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] tail projection request / grant
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f17v01_n034 | owner=SharedMatrixCore | class=mac | macro=OP_LATENT_ATTENTION_OPROJ
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
    T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f17v01_n035 | owner=OutputCommitCore | class=plus | macro=OP_LATENT_ATTENTION_OPROJ
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f17v01_n036 | owner=OutputCommitCore | class=output | macro=OP_LATENT_ATTENTION_OPROJ
  rect rgba(213, 232, 212, 0.24)
    O->>O: X + MLA
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_LATENT_ATTENTION_OPROJ done
  end
  Note over C,O: OP_MOE — DDR read → RMSNorm 2 → Router / Top-k → experts → merge / residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_MOE
  end
  loop OP_MOE token batch / expert group loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-sequence MoE input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-sequence MoE input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] RMSNorm 2 / router / expert parameters
  end
  %% source-node f17v01_n037 | owner=NormCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 2 output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] router input / expert queue source
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f17v01_n039 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] Router projection result
  end
  %% source-node f17v01_n040 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Router scoring
  end
  %% source-node f17v01_n041 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Top-8 + renorm
  end
  %% source-node f17v01_n042 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Dispatch / gather
  end
  rect rgba(213, 232, 212, 0.24)
    F->>B: [HW] expert queue / token grouping
  end
  rect rgba(213, 232, 212, 0.24)
    B-->>F: [HW] grouped expert activation
  end
  loop selected routed experts / grouped tokens
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f17v01_n043 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] gate_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f17v01_n044 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] up_proj result
  end
  %% source-node f17v01_n045 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: SiLU
  end
  %% source-node f17v01_n046 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Elementwise gate
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f17v01_n047 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  %% source-node f17v01_n048 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Expert weighting
  end
  %% source-node f17v01_n049 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Scatter / weighted reduce
  end
  end
  Note over F,O: Shared expert path executes for every token
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f17v01_n050 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] gate_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f17v01_n051 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] up_proj result
  end
  %% source-node f17v01_n052 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: SiLU
  end
  %% source-node f17v01_n053 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Elementwise gate
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f17v01_n054 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — Shared gate projection
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for Shared gate projection
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Shared gate projection
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Shared gate projection
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f17v01_n055 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared gate projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] Shared gate projection result
  end
  %% source-node f17v01_n056 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Sigmoid
  end
  %% source-node f17v01_n057 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Shared gating
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] expert output stream(s)
  end
  %% source-node f17v01_n058 | owner=OutputCommitCore | class=plus | macro=OP_MOE
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f17v01_n059 | owner=OutputCommitCore | class=plus | macro=OP_MOE
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f17v01_n060 | owner=OutputCommitCore | class=output | macro=OP_MOE
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_MOE done
  end

```

## 18_granite4_hybrid_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 18: Granite 4 Hybrid
%% Source block-atlas file: 18_granite4_hybrid.mmd
%% Sequence file: 18_granite4_hybrid_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: Variant 1 — Representative grouped-query hybrid dense block
  Note over C,O: OP_K_PROJ — RMSNorm 1 → K Proj → RoPE → K cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_K_PROJ
  end
  loop OP_K_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — K pass activation / residual
  end
  %% source-node f18v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_K_PROJ
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% source-node f18v01_n020 | owner=NormCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — K pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f18v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_K_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: K Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] K Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for RoPE
  end
  %% source-node f18v01_n025 | owner=ElementwiseTransformCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] RoPE output
  end
  %% source-node f18v01_n027 | owner=KVStateCore | class=state | macro=OP_K_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: K cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write K cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_K_PROJ done
  end
  Note over C,O: OP_V_PROJ — RMSNorm 1 → V Proj → V cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_V_PROJ
  end
  loop OP_V_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=V pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — V pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — V pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f18v01_n024 | owner=SharedMatrixCore | class=mac | macro=OP_V_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: V Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V Proj result → projection-result dispatch
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
  end
  %% source-node f18v01_n028 | owner=KVStateCore | class=state | macro=OP_V_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: V cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write V cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_V_PROJ done
  end
  Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: RMSNorm 1 → Q Proj → RoPE
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_Q_ATTN_OPROJ
  end
  loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=Q pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — Q pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — Q pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f18v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Q Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for RoPE
  end
  %% source-node f18v01_n026 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>S: [HW] RoPE output
  end
  rect rgba(213, 232, 212, 0.24)
    E-->>S: [HW] commit Q tile / query stream
  end
  rect rgba(213, 232, 212, 0.24)
    S->>S: [HW] Q tile resident for subsequent sequence op
  end
  end
  Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → O Proj → residual commit
  loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read K/V state / history
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] K/V state tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] K/V state response
  end
  %% source-node f18v01_n029 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: K head repeat ×4
  end
  %% source-node f18v01_n030 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: V head repeat ×4
  end
  %% source-node f18v01_n031 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q × Kᵀ
  end
  %% source-node f18v01_n032 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f18v01_n033 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] sequence output block + tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] tail projection request / grant
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f18v01_n034 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
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
    T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f18v01_n035 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f18v01_n036 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    O->>O: X + Attention
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_Q_ATTN_OPROJ done
  end
  Note over C,O: OP_FFN — DDR read → RMSNorm 2 → dense FFN → residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_FFN
  end
  loop OP_FFN token/chunk/weight-tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] RMSNorm 2 / activation parameters
  end
  %% source-node f18v01_n037 | owner=NormCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 2 output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] FFN resident activation tile
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f18v01_n039 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M->>M: [HW] gate tile held locally for fused SwiGLU
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f18v01_n040 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M->>M: [HW] up tile held locally for fused SwiGLU
  end
  %% source-node f18v01_n041 | owner=SharedMatrixCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    M->>M: SiLU (current fused MlpSiluLane32Core)
  end
  %% source-node f18v01_n042 | owner=SharedMatrixCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    M->>M: Elementwise gate (current fused Gate×Up)
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [EDGE E_MATRIX_TO_FFN] fused activation ready / down-phase event
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f18v01_n043 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] FFN result / residual input
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f18v01_n044 | owner=OutputCommitCore | class=plus | macro=OP_FFN
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f18v01_n045 | owner=OutputCommitCore | class=output | macro=OP_FFN
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_FFN done
  end

```

## 19_qwen1_dense_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 19: Qwen1 Dense
%% Source block-atlas file: 19_qwen1_dense.mmd
%% Sequence file: 19_qwen1_dense_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: Variant 1 — Earlier Qwen dense decoder block
  Note over C,O: OP_K_PROJ — RMSNorm 1 → K Proj → RoPE → K cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_K_PROJ
  end
  loop OP_K_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — K pass activation / residual
  end
  %% source-node f19v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_K_PROJ
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% source-node f19v01_n020 | owner=NormCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — K pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f19v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_K_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: K Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] K Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for RoPE
  end
  %% source-node f19v01_n025 | owner=ElementwiseTransformCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] RoPE output
  end
  %% source-node f19v01_n027 | owner=KVStateCore | class=state | macro=OP_K_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: K cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write K cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_K_PROJ done
  end
  Note over C,O: OP_V_PROJ — RMSNorm 1 → V Proj → V cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_V_PROJ
  end
  loop OP_V_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=V pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — V pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — V pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f19v01_n024 | owner=SharedMatrixCore | class=mac | macro=OP_V_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: V Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V Proj result → projection-result dispatch
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
  end
  %% source-node f19v01_n028 | owner=KVStateCore | class=state | macro=OP_V_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: V cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write V cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_V_PROJ done
  end
  Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: RMSNorm 1 → Q Proj → RoPE
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_Q_ATTN_OPROJ
  end
  loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=Q pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — Q pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — Q pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f19v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Q Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for RoPE
  end
  %% source-node f19v01_n026 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>S: [HW] RoPE output
  end
  rect rgba(213, 232, 212, 0.24)
    E-->>S: [HW] commit Q tile / query stream
  end
  rect rgba(213, 232, 212, 0.24)
    S->>S: [HW] Q tile resident for subsequent sequence op
  end
  end
  Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → O Proj → residual commit
  loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read K/V state / history
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] K/V state tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] K/V state response
  end
  %% source-node f19v01_n029 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: K head repeat ×8
  end
  %% source-node f19v01_n030 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: V head repeat ×8
  end
  %% source-node f19v01_n031 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q × Kᵀ
  end
  %% source-node f19v01_n032 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f19v01_n033 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] sequence output block + tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] tail projection request / grant
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f19v01_n034 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
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
    T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f19v01_n035 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f19v01_n036 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    O->>O: X + Attention
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_Q_ATTN_OPROJ done
  end
  Note over C,O: OP_FFN — DDR read → RMSNorm 2 → dense FFN → residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_FFN
  end
  loop OP_FFN token/chunk/weight-tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] RMSNorm 2 / activation parameters
  end
  %% source-node f19v01_n037 | owner=NormCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 2 output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] FFN resident activation tile
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f19v01_n039 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M->>M: [HW] gate tile held locally for fused SwiGLU
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f19v01_n040 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M->>M: [HW] up tile held locally for fused SwiGLU
  end
  %% source-node f19v01_n041 | owner=SharedMatrixCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    M->>M: SiLU (current fused MlpSiluLane32Core)
  end
  %% source-node f19v01_n042 | owner=SharedMatrixCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    M->>M: Elementwise gate (current fused Gate×Up)
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [EDGE E_MATRIX_TO_FFN] fused activation ready / down-phase event
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f19v01_n043 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] FFN result / residual input
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f19v01_n044 | owner=OutputCommitCore | class=plus | macro=OP_FFN
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f19v01_n045 | owner=OutputCommitCore | class=output | macro=OP_FFN
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_FFN done
  end

```

## 20_phi2_dense_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 20: Phi-2 Dense
%% Source block-atlas file: 20_phi2_dense.mmd
%% Sequence file: 20_phi2_dense_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: Variant 1 — Parallel residual MHA + GELU block
  Note over C,O: OP_K_PROJ — LayerNorm (attn) → K Proj → RoPE
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_K_PROJ
  end
  loop OP_K_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — attention K pass activation / residual
  end
  %% source-node f20v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_K_PROJ
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — LayerNorm (attn) / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — LayerNorm (attn) / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] LayerNorm (attn) / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] LayerNorm (attn) / position parameters
  end
  %% source-node f20v01_n020 | owner=NormCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: LayerNorm (attn)
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] LayerNorm (attn) output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — attention K pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f20v01_n024 | owner=SharedMatrixCore | class=mac | macro=OP_K_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: K Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] K Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for RoPE
  end
  %% source-node f20v01_n027 | owner=ElementwiseTransformCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] RoPE output
  end
  rect rgba(213, 232, 212, 0.24)
    K->>K: [HW] K state staging
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write K state
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_K_PROJ done
  end
  Note over C,O: OP_V_PROJ — LayerNorm (attn) → V Proj
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_V_PROJ
  end
  loop OP_V_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — attention V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] attention V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — LayerNorm (attn) / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — LayerNorm (attn) / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] LayerNorm (attn) / position parameters
  end
  %% hardware replay of source operator: LayerNorm (attn) | pass=attention V pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: LayerNorm (attn)
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] LayerNorm (attn) output — attention V pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — attention V pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f20v01_n026 | owner=SharedMatrixCore | class=mac | macro=OP_V_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: V Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V Proj result → projection-result dispatch
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
  end
  rect rgba(213, 232, 212, 0.24)
    K->>K: [HW] V state staging
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write V state
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_V_PROJ done
  end
  Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: LayerNorm (attn) → Q Proj → RoPE
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_Q_ATTN_OPROJ
  end
  loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — attention Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] attention Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — LayerNorm (attn) / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — LayerNorm (attn) / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] LayerNorm (attn) / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] LayerNorm (attn) / position parameters
  end
  %% hardware replay of source operator: LayerNorm (attn) | pass=attention Q pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: LayerNorm (attn)
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] LayerNorm (attn) output — attention Q pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — attention Q pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f20v01_n025 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Q Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for RoPE
  end
  %% source-node f20v01_n028 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>S: [HW] RoPE output
  end
  rect rgba(213, 232, 212, 0.24)
    E-->>S: [HW] commit Q tile / query stream
  end
  rect rgba(213, 232, 212, 0.24)
    S->>S: [HW] Q tile resident for subsequent sequence op
  end
  end
  rect rgba(242, 242, 242, 0.18)
    S-->>C: OP_Q_PROJ done
  end
  Note over C,O: OP_PARALLEL_ATTN_FFN — Attention and MLP branches execute from the same residual input, then join
  rect rgba(242, 242, 242, 0.18)
    C->>S: start OP_PARALLEL_ATTN_FFN
  end
  loop OP_PARALLEL_ATTN_FFN token / tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — parallel residual input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] parallel residual input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — LayerNorm (MLP) / branch parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — LayerNorm (MLP) / branch parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] LayerNorm (MLP) / branch parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>S: [HW] LayerNorm (MLP) / branch parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] LayerNorm (MLP) / branch parameters
  end
  par Attention branch
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read K/V state
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] K/V state tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] K/V response
  end
  %% source-node f20v01_n029 | owner=SequenceCore | class=mac | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q × Kᵀ
  end
  %% source-node f20v01_n030 | owner=SequenceCore | class=other | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f20v01_n031 | owner=SequenceCore | class=mac | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] attention output block
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] OProj request
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f20v01_n032 | owner=SharedMatrixCore | class=mac | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: O Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>T: [EDGE E_MATRIX_TO_TAIL] O Proj result tile
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>O: [EDGE E_MATRIX_TO_COMMIT] OProj result stream128
  end
  and MLP branch
  %% source-node f20v01_n021 | owner=NormCore | class=other | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(225, 213, 231, 0.24)
    N->>N: LayerNorm (MLP)
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] LayerNorm (MLP) output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] MLP branch input
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — fc1
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for fc1
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — fc1
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — fc1
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f20v01_n033 | owner=SharedMatrixCore | class=mac | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: fc1
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] fc1 result
  end
  %% source-node f20v01_n034 | owner=FeedForwardCore | class=other | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(225, 213, 231, 0.24)
    F->>F: GELU
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — fc2
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for fc2
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — fc2
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — fc2
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f20v01_n035 | owner=SharedMatrixCore | class=mac | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: fc2
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] fc2 result
  end
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>O: [HW] attention branch result
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] MLP branch result
  end
  %% source-node f20v01_n036 | owner=OutputCommitCore | class=plus | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f20v01_n037 | owner=OutputCommitCore | class=plus | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f20v01_n038 | owner=OutputCommitCore | class=output | macro=OP_PARALLEL_ATTN_FFN
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_PARALLEL_ATTN_FFN done
  end

```

## 21_bloom_dense_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 21: BLOOM Dense
%% Source block-atlas file: 21_bloom_dense.mmd
%% Sequence file: 21_bloom_dense_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: Variant 1 — BLOOM pre-LN dense block
  Note over C,O: OP_INPUT_POSITION — DDR read → Learned absolute position → positioned activation commit
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_INPUT_POSITION
  end
  loop OP_INPUT_POSITION token/beat loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — block input / residual
  end
  %% source-node f21v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_INPUT_POSITION
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>E: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — Learned absolute position
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — Learned absolute position
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] Learned absolute position
  end
  %% source-node f21v01_n020 | owner=ElementwiseTransformCore | class=other | macro=OP_INPUT_POSITION
  rect rgba(225, 213, 231, 0.24)
    E->>E: Learned absolute position
  end
  rect rgba(213, 232, 212, 0.24)
    E->>DDR: [HW] write positioned activation scratch
  end
  end
  rect rgba(242, 242, 242, 0.18)
    E-->>C: OP_INPUT_POSITION done
  end
  Note over C,O: OP_QKV_PROJ — LayerNorm 1 → Combined QKV Proj → Split heads → Q/K/V state staging
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_QKV_PROJ
  end
  loop OP_QKV_PROJ token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — positioned / block activation
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] positioned / block activation
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — LayerNorm 1 parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — LayerNorm 1 parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] LayerNorm 1 parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] LayerNorm 1 parameters
  end
  %% source-node f21v01_n021 | owner=NormCore | class=other | macro=OP_QKV_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: LayerNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] LayerNorm 1 output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] QKV input tile
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Combined QKV Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Combined QKV Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f21v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_QKV_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Combined QKV Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Combined QKV Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for Split heads
  end
  %% source-node f21v01_n024 | owner=ElementwiseTransformCore | class=other | macro=OP_QKV_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: Split heads
  end
  rect rgba(213, 232, 212, 0.24)
    E-->>K: [HW] K/V state streams
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write K/V state
  end
  rect rgba(213, 232, 212, 0.24)
    E-->>S: [HW] Q tile commit
  end
  end
  rect rgba(242, 242, 242, 0.18)
    S-->>C: OP_QKV_PROJ done
  end
  Note over C,O: OP_ATTENTION_OPROJ — K/V state read → sequence mixing → Output Proj → residual commit
  rect rgba(242, 242, 242, 0.18)
    C->>S: start OP_ATTENTION_OPROJ
  end
  loop OP_ATTENTION_OPROJ Q-block / KV-tile loop
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read K/V state / history
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] K/V state tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] K/V state response
  end
  %% source-node f21v01_n025 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q × Kᵀ
  end
  %% source-node f21v01_n026 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f21v01_n027 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] sequence output block + tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] tail projection request / grant
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for Output Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Output Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Output Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f21v01_n028 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Output Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>T: [EDGE E_MATRIX_TO_TAIL] Output Proj result tile
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>O: [EDGE E_MATRIX_TO_COMMIT] OProj result stream128
  end
  rect rgba(245, 245, 245, 0.18)
    T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f21v01_n029 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f21v01_n030 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    O->>O: X + Attention
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_Q_ATTN_OPROJ done
  end
  Note over C,O: OP_FFN — DDR read → LayerNorm 2 → dense FFN → residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_FFN
  end
  loop OP_FFN token/chunk/weight-tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — LayerNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — LayerNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] LayerNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] LayerNorm 2 / activation parameters
  end
  %% source-node f21v01_n031 | owner=NormCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    N->>N: LayerNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] LayerNorm 2 output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] FFN resident activation tile
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — fc1
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for fc1
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — fc1
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — fc1
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f21v01_n033 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: fc1
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] fc1 result
  end
  %% source-node f21v01_n034 | owner=FeedForwardCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    F->>F: GELU
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — fc2
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for fc2
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — fc2
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — fc2
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f21v01_n035 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: fc2
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] fc2 result
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] FFN result / residual input
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f21v01_n036 | owner=OutputCommitCore | class=plus | macro=OP_FFN
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f21v01_n037 | owner=OutputCommitCore | class=output | macro=OP_FFN
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_FFN done
  end

```

## 22_openelm_dense_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 22: OpenELM Dense
%% Source block-atlas file: 22_openelm_dense.mmd
%% Sequence file: 22_openelm_dense_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: Variant 1 — Compact GQA + SwiGLU block
  Note over C,O: OP_K_PROJ — RMSNorm 1 → K Proj → RoPE → K cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_K_PROJ
  end
  loop OP_K_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — K pass activation / residual
  end
  %% source-node f22v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_K_PROJ
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% source-node f22v01_n020 | owner=NormCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — K pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f22v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_K_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: K Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] K Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for RoPE
  end
  %% source-node f22v01_n025 | owner=ElementwiseTransformCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] RoPE output
  end
  %% source-node f22v01_n027 | owner=KVStateCore | class=state | macro=OP_K_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: K cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write K cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_K_PROJ done
  end
  Note over C,O: OP_V_PROJ — RMSNorm 1 → V Proj → V cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_V_PROJ
  end
  loop OP_V_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=V pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — V pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — V pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f22v01_n024 | owner=SharedMatrixCore | class=mac | macro=OP_V_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: V Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V Proj result → projection-result dispatch
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
  end
  %% source-node f22v01_n028 | owner=KVStateCore | class=state | macro=OP_V_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: V cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write V cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_V_PROJ done
  end
  Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: RMSNorm 1 → Q Proj → RoPE
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_Q_ATTN_OPROJ
  end
  loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=Q pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — Q pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — Q pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f22v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Q Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for RoPE
  end
  %% source-node f22v01_n026 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>S: [HW] RoPE output
  end
  rect rgba(213, 232, 212, 0.24)
    E-->>S: [HW] commit Q tile / query stream
  end
  rect rgba(213, 232, 212, 0.24)
    S->>S: [HW] Q tile resident for subsequent sequence op
  end
  end
  Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → O Proj → residual commit
  loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read K/V state / history
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] K/V state tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] K/V state response
  end
  %% source-node f22v01_n029 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: K head repeat ×4
  end
  %% source-node f22v01_n030 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: V head repeat ×4
  end
  %% source-node f22v01_n031 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q × Kᵀ
  end
  %% source-node f22v01_n032 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f22v01_n033 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] sequence output block + tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] tail projection request / grant
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f22v01_n034 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
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
    T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f22v01_n035 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f22v01_n036 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    O->>O: X + Attention
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_Q_ATTN_OPROJ done
  end
  Note over C,O: OP_FFN — DDR read → RMSNorm 2 → dense FFN → residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_FFN
  end
  loop OP_FFN token/chunk/weight-tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] RMSNorm 2 / activation parameters
  end
  %% source-node f22v01_n037 | owner=NormCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 2 output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] FFN resident activation tile
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f22v01_n039 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M->>M: [HW] gate tile held locally for fused SwiGLU
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f22v01_n040 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M->>M: [HW] up tile held locally for fused SwiGLU
  end
  %% source-node f22v01_n041 | owner=SharedMatrixCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    M->>M: SiLU (current fused MlpSiluLane32Core)
  end
  %% source-node f22v01_n042 | owner=SharedMatrixCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    M->>M: Elementwise gate (current fused Gate×Up)
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [EDGE E_MATRIX_TO_FFN] fused activation ready / down-phase event
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f22v01_n043 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] FFN result / residual input
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f22v01_n044 | owner=OutputCommitCore | class=plus | macro=OP_FFN
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f22v01_n045 | owner=OutputCommitCore | class=output | macro=OP_FFN
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_FFN done
  end

```

## 23_powermoe_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 23: PowerMoE
%% Source block-atlas file: 23_powermoe.mmd
%% Sequence file: 23_powermoe_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: Variant 1 — Attention + sparse MoE block
  Note over C,O: OP_K_PROJ — RMSNorm 1 → K Proj → RoPE → K cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_K_PROJ
  end
  loop OP_K_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — K pass activation / residual
  end
  %% source-node f23v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_K_PROJ
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% source-node f23v01_n020 | owner=NormCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — K pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f23v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_K_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: K Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] K Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for RoPE
  end
  %% source-node f23v01_n025 | owner=ElementwiseTransformCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] RoPE output
  end
  %% source-node f23v01_n027 | owner=KVStateCore | class=state | macro=OP_K_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: K cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write K cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_K_PROJ done
  end
  Note over C,O: OP_V_PROJ — RMSNorm 1 → V Proj → V cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_V_PROJ
  end
  loop OP_V_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=V pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — V pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — V pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f23v01_n024 | owner=SharedMatrixCore | class=mac | macro=OP_V_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: V Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V Proj result → projection-result dispatch
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
  end
  %% source-node f23v01_n028 | owner=KVStateCore | class=state | macro=OP_V_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: V cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write V cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_V_PROJ done
  end
  Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: RMSNorm 1 → Q Proj → RoPE
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_Q_ATTN_OPROJ
  end
  loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=Q pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — Q pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — Q pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f23v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Q Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for RoPE
  end
  %% source-node f23v01_n026 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>S: [HW] RoPE output
  end
  rect rgba(213, 232, 212, 0.24)
    E-->>S: [HW] commit Q tile / query stream
  end
  rect rgba(213, 232, 212, 0.24)
    S->>S: [HW] Q tile resident for subsequent sequence op
  end
  end
  Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → O Proj → residual commit
  loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read K/V state / history
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] K/V state tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] K/V state response
  end
  %% source-node f23v01_n029 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: K head repeat ×4
  end
  %% source-node f23v01_n030 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: V head repeat ×4
  end
  %% source-node f23v01_n031 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q × Kᵀ
  end
  %% source-node f23v01_n032 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f23v01_n033 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] sequence output block + tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] tail projection request / grant
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f23v01_n034 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
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
    T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f23v01_n035 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f23v01_n036 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    O->>O: X + Attention
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_Q_ATTN_OPROJ done
  end
  Note over C,O: OP_MOE — DDR read → RMSNorm 2 → Router / Top-k → experts → merge / residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_MOE
  end
  loop OP_MOE token batch / expert group loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-sequence MoE input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-sequence MoE input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] RMSNorm 2 / router / expert parameters
  end
  %% source-node f23v01_n037 | owner=NormCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 2 output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] router input / expert queue source
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f23v01_n039 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] Router projection result
  end
  %% source-node f23v01_n040 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Router scoring
  end
  %% source-node f23v01_n041 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Top-4 + renorm
  end
  %% source-node f23v01_n042 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Dispatch / gather
  end
  rect rgba(213, 232, 212, 0.24)
    F->>B: [HW] expert queue / token grouping
  end
  rect rgba(213, 232, 212, 0.24)
    B-->>F: [HW] grouped expert activation
  end
  loop selected routed experts / grouped tokens
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f23v01_n043 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] gate_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f23v01_n044 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] up_proj result
  end
  %% source-node f23v01_n045 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: SiLU
  end
  %% source-node f23v01_n046 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Elementwise gate
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f23v01_n047 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  %% source-node f23v01_n048 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Expert weighting
  end
  %% source-node f23v01_n049 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Scatter / weighted reduce
  end
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] expert output stream(s)
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f23v01_n050 | owner=OutputCommitCore | class=plus | macro=OP_MOE
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f23v01_n051 | owner=OutputCommitCore | class=output | macro=OP_MOE
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_MOE done
  end

```

## 24_nemotron3_hybrid_moe_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 24: Nemotron 3 Hybrid MoE
%% Source block-atlas file: 24_nemotron3_hybrid_moe.mmd
%% Sequence file: 24_nemotron3_hybrid_moe_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: Variant 1 — Representative long-context attention + routed/shared MoE block
  Note over C,O: OP_K_PROJ — RMSNorm 1 → K Proj → RoPE → K cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_K_PROJ
  end
  loop OP_K_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — K pass activation / residual
  end
  %% source-node f24v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_K_PROJ
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% source-node f24v01_n020 | owner=NormCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — K pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f24v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_K_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: K Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] K Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for RoPE
  end
  %% source-node f24v01_n025 | owner=ElementwiseTransformCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] RoPE output
  end
  %% source-node f24v01_n027 | owner=KVStateCore | class=state | macro=OP_K_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: K cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write K cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_K_PROJ done
  end
  Note over C,O: OP_V_PROJ — RMSNorm 1 → V Proj → V cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_V_PROJ
  end
  loop OP_V_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=V pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — V pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — V pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f24v01_n024 | owner=SharedMatrixCore | class=mac | macro=OP_V_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: V Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V Proj result → projection-result dispatch
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
  end
  %% source-node f24v01_n028 | owner=KVStateCore | class=state | macro=OP_V_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: V cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write V cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_V_PROJ done
  end
  Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: RMSNorm 1 → Q Proj → RoPE
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_Q_ATTN_OPROJ
  end
  loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=Q pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — Q pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — Q pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f24v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Q Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for RoPE
  end
  %% source-node f24v01_n026 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>S: [HW] RoPE output
  end
  rect rgba(213, 232, 212, 0.24)
    E-->>S: [HW] commit Q tile / query stream
  end
  rect rgba(213, 232, 212, 0.24)
    S->>S: [HW] Q tile resident for subsequent sequence op
  end
  end
  Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → O Proj → residual commit
  loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read K/V state / history
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] K/V state tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] K/V state response
  end
  %% source-node f24v01_n029 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: K head repeat ×4
  end
  %% source-node f24v01_n030 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: V head repeat ×4
  end
  %% source-node f24v01_n031 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q × Kᵀ
  end
  %% source-node f24v01_n032 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Long-Context Softmax FP32
  end
  %% source-node f24v01_n033 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] sequence output block + tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] tail projection request / grant
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f24v01_n034 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
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
    T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f24v01_n035 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f24v01_n036 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    O->>O: X + Attention
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_Q_ATTN_OPROJ done
  end
  Note over C,O: OP_MOE — DDR read → RMSNorm 2 → Router / Top-k → experts → merge / residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_MOE
  end
  loop OP_MOE token batch / expert group loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-sequence MoE input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-sequence MoE input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 2 / router / expert parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] RMSNorm 2 / router / expert parameters
  end
  %% source-node f24v01_n037 | owner=NormCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 2 output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] router input / expert queue source
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Router projection
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f24v01_n039 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Router projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] Router projection result
  end
  %% source-node f24v01_n040 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Router scoring
  end
  %% source-node f24v01_n041 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Top-8 + renorm
  end
  %% source-node f24v01_n042 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Dispatch / gather
  end
  rect rgba(213, 232, 212, 0.24)
    F->>B: [HW] expert queue / token grouping
  end
  rect rgba(213, 232, 212, 0.24)
    B-->>F: [HW] grouped expert activation
  end
  loop selected routed experts / grouped tokens
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f24v01_n043 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] gate_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f24v01_n044 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] up_proj result
  end
  %% source-node f24v01_n045 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: SiLU
  end
  %% source-node f24v01_n046 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Elementwise gate
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f24v01_n047 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  %% source-node f24v01_n048 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Expert weighting
  end
  %% source-node f24v01_n049 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Scatter / weighted reduce
  end
  end
  Note over F,O: Shared expert path executes for every token
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f24v01_n050 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] gate_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f24v01_n051 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] up_proj result
  end
  %% source-node f24v01_n052 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: SiLU
  end
  %% source-node f24v01_n053 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Elementwise gate
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f24v01_n054 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — Shared gate projection
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for Shared gate projection
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Shared gate projection
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Shared gate projection
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f24v01_n055 | owner=SharedMatrixCore | class=mac | macro=OP_MOE
  rect rgba(218, 232, 252, 0.24)
    M->>M: Shared gate projection
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] Shared gate projection result
  end
  %% source-node f24v01_n056 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Sigmoid
  end
  %% source-node f24v01_n057 | owner=FeedForwardCore | class=other | macro=OP_MOE
  rect rgba(225, 213, 231, 0.24)
    F->>F: Shared gating
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] expert output stream(s)
  end
  %% source-node f24v01_n058 | owner=OutputCommitCore | class=plus | macro=OP_MOE
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f24v01_n059 | owner=OutputCommitCore | class=plus | macro=OP_MOE
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f24v01_n060 | owner=OutputCommitCore | class=output | macro=OP_MOE
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_MOE done
  end

```

## 25_mistral_dense_owner_timing_sequence_v6

```mermaid
%%{init: {"theme": "base", "sequence": {"useMaxWidth": false, "diagramMarginX": 18, "diagramMarginY": 12, "actorMargin": 24, "width": 150, "height": 42, "boxMargin": 8, "boxTextMargin": 5, "noteMargin": 8, "messageMargin": 24, "mirrorActors": false, "rightAngles": true, "wrap": true}, "themeVariables": {"actorBkg": "#ffffff", "actorBorder": "#555555", "actorTextColor": "#1f1f1f", "actorLineColor": "#666666", "signalColor": "#333333", "signalTextColor": "#1f1f1f", "labelBoxBkgColor": "#ffffff", "labelBoxBorderColor": "#888888", "labelTextColor": "#1f1f1f", "loopTextColor": "#1f1f1f", "noteBkgColor": "#ffffff", "noteBorderColor": "#999999", "noteTextColor": "#333333", "activationBkgColor": "#f5f5f5", "activationBorderColor": "#777777", "sequenceNumberColor": "#555555"}, "themeCSS": ".actor-line { stroke: #666 !important; stroke-width: 1.25px !important; stroke-dasharray: 3 3; }"}}%%
%% Family rank 25: Mistral Dense
%% Source block-atlas file: 25_mistral_dense.mmd
%% Sequence file: 25_mistral_dense_owner_timing_sequence_v6.mmd
%% 13-owner review basis: 381d85219d6feec9b10345e2800ac74d4185e5a0; frozen universal SLX 94384dda268433b7ec47bc88fe97b85a3d1a9fe2360116974e0f0358e2880945.
%% Current-main confirmation: 0db7eed1e80610083ecc40b1c5982f60db5bda40; SLX 33d79655d4de9bf0e6147fb74f50cc7e26450d9e6e0cecc2d30f386ac7b83379; owner manifest v6.6.
%% Q×Kᵀ is ScoreCore/QKProduct+QKBeatSum in SequenceCore.
%% P×V is the OnlineORecurrence beta×V + alpha×Oold update in SequenceCore; full P is not materialized.
%% SharedMatrix token-dot mode is FFN-down product reduction, not Attention QK/PV.
%% Unsupported-family files are owner/edge mappings, not implementation-support claims.
%% Q projection is shown as a separate sub-operation; in the current full-block profile it is followed immediately by sequence/OProj under the QSEQ control window.
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


  Note over C,O: Variant 1 — Sliding-window GQA + SwiGLU block
  Note over C,O: OP_K_PROJ — RMSNorm 1 → K Proj → RoPE → K cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_K_PROJ
  end
  loop OP_K_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — K pass activation / residual
  end
  %% source-node f25v01_n019 | owner=ActivationReadDmaCore | class=input | macro=OP_K_PROJ
  rect rgba(255, 242, 204, 0.24)
    A->>A: X
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% source-node f25v01_n020 | owner=NormCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — K pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — K Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f25v01_n022 | owner=SharedMatrixCore | class=mac | macro=OP_K_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: K Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] K Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for RoPE
  end
  %% source-node f25v01_n025 | owner=ElementwiseTransformCore | class=other | macro=OP_K_PROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [HW] RoPE output
  end
  %% source-node f25v01_n027 | owner=KVStateCore | class=state | macro=OP_K_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: K cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write K cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_K_PROJ done
  end
  Note over C,O: OP_V_PROJ — RMSNorm 1 → V Proj → V cache
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_V_PROJ
  end
  loop OP_V_PROJ autonomous token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] V pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=V pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — V pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — V pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — V Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f25v01_n024 | owner=SharedMatrixCore | class=mac | macro=OP_V_PROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: V Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [EDGE E_MATRIX_TO_TRANSFORM] V Proj result → projection-result dispatch
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>K: [EDGE E_TRANSFORM_TO_KV] K/V cache-write stream (RoPE or bypass)
  end
  %% source-node f25v01_n028 | owner=KVStateCore | class=state | macro=OP_V_PROJ
  rect rgba(213, 232, 212, 0.24)
    K->>K: V cache
  end
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] write V cache
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] write response
  end
  end
  rect rgba(242, 242, 242, 0.18)
    K-->>C: OP_V_PROJ done
  end
  Note over C,O: OP_Q_ATTN_OPROJ — Q projection phase: RMSNorm 1 → Q Proj → RoPE
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_Q_ATTN_OPROJ
  end
  loop OP_Q_ATTN_OPROJ Q-projection token/chunk/tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] Q pass activation / residual
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 1 / position parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>E: [HW] RMSNorm 1 / position parameters
  end
  %% hardware replay of source operator: RMSNorm 1 | pass=Q pass
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 1
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 1 output — Q pass
  end
  rect rgba(245, 245, 245, 0.18)
    B->>M: [HW] resident tile — Q pass
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — Q Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f25v01_n023 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    M->>M: Q Proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>E: [HW] Q Proj result
  end
  rect rgba(245, 245, 245, 0.18)
    M->>E: [HW] input for RoPE
  end
  %% source-node f25v01_n026 | owner=ElementwiseTransformCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    E->>E: RoPE
  end
  rect rgba(245, 245, 245, 0.18)
    E-->>S: [HW] RoPE output
  end
  rect rgba(213, 232, 212, 0.24)
    E-->>S: [HW] commit Q tile / query stream
  end
  rect rgba(213, 232, 212, 0.24)
    S->>S: [HW] Q tile resident for subsequent sequence op
  end
  end
  Note over C,O: OP_Q_ATTN_OPROJ — attention/OProj phase: K/V state read → sequence mixing → O Proj → residual commit
  loop OP_Q_ATTN_OPROJ attention Q-block / KV-tile loop
  rect rgba(213, 232, 212, 0.24)
    K->>DDR: [HW] read K/V state / history
  end
  rect rgba(213, 232, 212, 0.24)
    DDR-->>K: [HW] K/V state tile
  end
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] K/V state response
  end
  %% source-node f25v01_n029 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: K head repeat ×4
  end
  %% source-node f25v01_n030 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    K-->>S: [HW] KV-group state broadcast / lane map
  end
  rect rgba(225, 213, 231, 0.24)
    S->>S: V head repeat ×4
  end
  %% source-node f25v01_n031 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: Q × Kᵀ
  end
  %% source-node f25v01_n032 | owner=SequenceCore | class=other | macro=OP_Q_ATTN_OPROJ
  rect rgba(225, 213, 231, 0.24)
    S->>S: Softmax FP32
  end
  %% source-node f25v01_n033 | owner=SequenceCore | class=mac | macro=OP_Q_ATTN_OPROJ
  rect rgba(218, 232, 252, 0.24)
    S->>S: P × V / Online O recurrence (β×V + α×Oold)
  end
  rect rgba(245, 245, 245, 0.18)
    S-->>T: [HW] sequence output block + tags
  end
  rect rgba(242, 242, 242, 0.18)
    T->>M: [HW] tail projection request / grant
  end
  rect rgba(245, 245, 245, 0.18)
    T->>M: [HW] input tile for O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — O Proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f25v01_n034 | owner=SharedMatrixCore | class=mac | macro=OP_Q_ATTN_OPROJ
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
    T-->>O: [EDGE E_TAIL_TO_COMMIT] tail commit metadata / token-layout control
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f25v01_n035 | owner=OutputCommitCore | class=plus | macro=OP_Q_ATTN_OPROJ
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f25v01_n036 | owner=OutputCommitCore | class=output | macro=OP_Q_ATTN_OPROJ
  rect rgba(213, 232, 212, 0.24)
    O->>O: X + Attention
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_Q_ATTN_OPROJ done
  end
  Note over C,O: OP_FFN — DDR read → RMSNorm 2 → dense FFN → residual write
  rect rgba(242, 242, 242, 0.18)
    C->>A: start OP_FFN
  end
  loop OP_FFN token/chunk/weight-tile loop
  rect rgba(255, 242, 204, 0.24)
    A->>DDR: [HW] AXI read request — post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    DDR-->>A: [HW] post-attention / FFN input
  end
  rect rgba(255, 242, 204, 0.24)
    A-->>N: [HW] activation / residual stream
  end
  rect rgba(248, 206, 204, 0.24)
    P->>DDR: [HW] parameter read request — RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>P: [HW] parameter stream — RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>N: [HW] RMSNorm 2 / activation parameters
  end
  rect rgba(248, 206, 204, 0.24)
    P-->>F: [HW] RMSNorm 2 / activation parameters
  end
  %% source-node f25v01_n037 | owner=NormCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    N->>N: RMSNorm 2
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>B: [HW] RMSNorm 2 output
  end
  rect rgba(245, 245, 245, 0.18)
    B-->>F: [HW] FFN resident activation tile
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — gate_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f25v01_n039 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: gate_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M->>M: [HW] gate tile held locally for fused SwiGLU
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — up_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f25v01_n040 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: up_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M->>M: [HW] up tile held locally for fused SwiGLU
  end
  %% source-node f25v01_n041 | owner=SharedMatrixCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    M->>M: SiLU (current fused MlpSiluLane32Core)
  end
  %% source-node f25v01_n042 | owner=SharedMatrixCore | class=other | macro=OP_FFN
  rect rgba(225, 213, 231, 0.24)
    M->>M: Elementwise gate (current fused Gate×Up)
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [EDGE E_MATRIX_TO_FFN] fused activation ready / down-phase event
  end
  rect rgba(242, 242, 242, 0.18)
    F->>M: [HW] matrix request — down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    F->>M: [HW] input tile for down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W->>DDR: [HW] weight read request — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    DDR-->>W: [HW] weight stream — down_proj
  end
  rect rgba(248, 206, 204, 0.24)
    W-->>M: [HW] weight tile stream
  end
  %% source-node f25v01_n043 | owner=SharedMatrixCore | class=mac | macro=OP_FFN
  rect rgba(218, 232, 252, 0.24)
    M->>M: down_proj
  end
  rect rgba(245, 245, 245, 0.18)
    M-->>F: [HW] down_proj result
  end
  rect rgba(245, 245, 245, 0.18)
    F-->>O: [HW] FFN result / residual input
  end
  rect rgba(245, 245, 245, 0.18)
    N-->>O: [EDGE E_NORM_RESIDUAL_TO_COMMIT] captured residual stream
  end
  %% source-node f25v01_n044 | owner=OutputCommitCore | class=plus | macro=OP_FFN
  rect rgba(255, 255, 255, 0.28)
    O->>O: +
  end
  %% source-node f25v01_n045 | owner=OutputCommitCore | class=output | macro=OP_FFN
  rect rgba(213, 232, 212, 0.24)
    O->>O: Block output
  end
  end
  rect rgba(242, 242, 242, 0.18)
    O-->>C: OP_FFN done
  end

```

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

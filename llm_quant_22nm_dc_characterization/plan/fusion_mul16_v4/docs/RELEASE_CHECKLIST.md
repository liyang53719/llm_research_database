# FusionMul16 v4 release checklist

## Completed in sandbox

- [x] v2 product pipe imported and namespaced with source provenance.
- [x] v3 BF16 tree + four FP32 recurrent accumulators integrated.
- [x] Complete multiplier and accumulator RTL.
- [x] 128-bit packed interfaces; no direct INT16 mode.
- [x] Standalone clear, last alignment, busy and protocol checking.
- [x] All seven scalar input domains covered by literal exhaustive scans or complete BF16 equivalence proof.
- [x] Long-K precision sweep through K=4096.
- [x] VCS vectors/testbench and one-GHz DC automation generated.

## Local Agent required

- [ ] Full-IP VCS 28/28.
- [ ] Optional special-profile directed VCS.
- [ ] DC 12/12 at 1.000 ns.
- [ ] Structural multiplier/add-count proof.
- [ ] Setup, hold and DRC report.
- [ ] Area comparison against v3 14,043.211 µm².

## Product signoff still separate

- [ ] Target-model layer-output relative-L2/cosine.
- [ ] Full-logit comparison.
- [ ] Perplexity and task-suite regression.
- [ ] Power with representative activity.
- [ ] P&R/CTS/OCV physical 1 GHz closure.
- [ ] Formal equivalence or gate-level simulation.

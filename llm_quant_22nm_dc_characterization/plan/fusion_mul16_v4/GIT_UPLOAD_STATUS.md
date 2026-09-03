# Git upload status

```text
repository  liyang53719/llm_research_database
base        fusion-mul16-v3-accum @ fd43c01dc9ab9fd364c5c1e4c6d99f64970ac130
branch      fusion-mul16-v4-final
path        llm_quant_22nm_dc_characterization/plan/fusion_mul16_v4/
```

The target branch is based on the v3 commit. Local SSH git transport is used for the final commit and push. Before publishing, the bundle is rebuilt from the validated local sources and evidence with local absolute paths, hostname, proprietary `.db/.lib/.sldb`, DDC, generated netlists and raw DC logs excluded or sanitized.

The public bundle keeps the complete v4 RTL, scripts, verification vectors, summaries and sanitized DC reports. `V4_FINAL_DYNAMIC_FTZ` is the release inference profile; `V4_FINAL_DYNAMIC_IEEE` remains optional characterization data.

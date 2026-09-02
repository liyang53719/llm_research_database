# Git 上传

目标：

```text
repository : liyang53719/llm_research_database
base       : fusion-mul16-v2-1ghz / 041e6fc472422d57166f3489d3f62794c67fdea8
branch     : fusion-mul16-v3-accum
path       : llm_quant_22nm_dc_characterization/plan/fusion_mul16_v3_accum/
```

本地执行通过 SSH remote 完成分支、commit 与 push；上传前会移除本地绝对路径、hostname、专有 `.db/.lib/.sldb`、DDC、网表和 DC 原始日志，仅保留脱敏后的源代码、配置、汇总与 reports evidence。

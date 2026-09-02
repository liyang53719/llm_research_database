# FusionMul16 v2 本地结果

本目录包含 CLN22UL 0.80V TT、DC X-2025.06-SP3、1.000ns 条件下的 21 组综合、VCS 交叉检查、P5 消融和 Shared/Separate 架构结论。

- `results/local_dc/`：脱敏汇总、P5 消融、critical path、DW/brick proof 和严格校验。
- `evidence/runs/`：21 个 run 的脱敏 DC 报告、summary 和元数据。
- `PUBLIC_LOCAL_RESULTS_MANIFEST.csv`：公开结果文件哈希清单。
- `source_bundle_v2/`：修复后、可从 Git 解包复现的 v2 源码分片包。

结果中未包含标准单元/DesignWare 实现库、DDC、映射网表或本机绝对路径。

# FusionMul16 v3 sandbox validation

```text
status                     PASS
Python files compiled      16
unit tests                 20 / 20
RTL source files           7
numeric comparison rows    54
VCS cases generated        15
1 GHz DC groups planned    12
VCS available in sandbox   no
DC/DW available in sandbox no
```

Synthetic K=4096 gate:

- `bf16_block64_fp32_checkpoint`: PASS
- `bf16_tree_fp32_recurrent`: PASS
- `full_bf16`: FAIL — fp8_proxy/gaussian nrmse=4.325 p99=38.534; fp8_proxy/positive nrmse=34.142; fp8_proxy/outlier nrmse=3.873; bf16/gaussian nrmse=7.521 p99=38.752; bf16/positive nrmse=58.622; bf16/outlier nrmse=6.038

The synthetic gate is not a target-model accuracy signoff. Local VCS must run the 15 generated accumulation sequences; local DC must run the 12 one-GHz groups.

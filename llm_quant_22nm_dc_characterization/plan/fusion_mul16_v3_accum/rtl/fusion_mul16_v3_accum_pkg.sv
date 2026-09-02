package fusion_mul16_v3_accum_pkg;
  typedef enum logic [1:0] {
    ACCUM_FULL_BF16                 = 2'd0,
    ACCUM_BF16_TREE_FP32_RECURRENT  = 2'd1,
    ACCUM_BF16_BLOCK64_FP32_CKPT    = 2'd2
  } fusion_mul16_v3_accum_style_e;
endpackage

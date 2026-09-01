package mixed_format_pkg;
  typedef enum logic [1:0] {
    FMT_INT4 = 2'd0,
    FMT_INT8 = 2'd1,
    FMT_FP8_E4M3 = 2'd2,
    FMT_BF16 = 2'd3
  } operand_format_e;
endpackage

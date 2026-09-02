module fusion_mul16_v2_cluster #(
  parameter int INT_ACC_W = 48,
  parameter int FIXED_MODE = -1,
  parameter bit SUPPORT_FP8 = 1'b1,
  parameter bit SUPPORT_BF16 = 1'b1,
  parameter bit SUPPORT_I4_FP8 = 1'b1,
  parameter bit SUPPORT_I4_BF16 = 1'b1,
  parameter bit SUPPORT_I8_BF16 = 1'b1,
  parameter bit SUPPORT_SPECIALS = 1'b0
) (
  input  logic clk,
  input  logic rst_n,
  input  logic cfg_valid_i,
  input  logic [2:0] cfg_mode_i,
  input  logic [2:0] cfg_rnd_i,
  output logic cfg_ready_o,
  output logic cfg_error_o,
  input  logic valid_i,
  input  logic clear_i,
  input  logic [127:0] lhs_packed_i,
  input  logic [127:0] rhs_packed_i,
  output logic int_valid_o,
  output logic fp_valid_o,
  output logic signed [INT_ACC_W-1:0] int_acc_o [0:3],
  output logic [15:0] bf16_acc_o [0:3],
  output logic [7:0] bf16_status_o [0:3],
  output logic [2:0] active_mode_o
);
  import fusion_mul16_v2_pkg::*;

  logic accept_data;
  logic [2:0] active_mode;
  logic [6:0] active_onehot;
  logic [2:0] active_rnd;

  logic product_int_valid;
  logic product_int_clear;
  logic signed [17:0] int_lane_sum [0:3];
  logic product_fp_valid;
  logic product_fp_clear;
  logic [15:0] bf16_lane_item [0:3][0:3];

  fusion_mul16_v2_config #(
    .FIXED_MODE(FIXED_MODE),
    .SUPPORT_FP8(SUPPORT_FP8),
    .SUPPORT_BF16(SUPPORT_BF16),
    .SUPPORT_I4_FP8(SUPPORT_I4_FP8),
    .SUPPORT_I4_BF16(SUPPORT_I4_BF16),
    .SUPPORT_I8_BF16(SUPPORT_I8_BF16),
    .INFLIGHT_DEPTH(10)
  ) u_config (
    .clk, .rst_n, .cfg_valid_i, .cfg_mode_i, .cfg_rnd_i,
    .cfg_ready_o, .cfg_error_o, .valid_i, .accept_data_o(accept_data),
    .active_mode_o(active_mode), .active_onehot_o(active_onehot),
    .active_rnd_o(active_rnd)
  );

  assign active_mode_o = active_mode;

  fusion_mul16_v2_product_pipe #(
    .SUPPORT_FP8(SUPPORT_FP8),
    .SUPPORT_BF16(SUPPORT_BF16),
    .SUPPORT_I4_FP8(SUPPORT_I4_FP8),
    .SUPPORT_I4_BF16(SUPPORT_I4_BF16),
    .SUPPORT_I8_BF16(SUPPORT_I8_BF16),
    .SUPPORT_SPECIALS(SUPPORT_SPECIALS)
  ) u_product_pipe (
    .clk,
    .rst_n,
    .valid_i(accept_data),
    .clear_i,
    .mode_onehot_i(active_onehot),
    .lhs_packed_i,
    .rhs_packed_i,
    .int_valid_o(product_int_valid),
    .int_clear_o(product_int_clear),
    .int_lane_sum_o(int_lane_sum),
    .fp_valid_o(product_fp_valid),
    .fp_clear_o(product_fp_clear),
    .bf16_lane_item_o(bf16_lane_item)
  );

  fusion_mul16_v2_int_accum #(.ACC_W(INT_ACC_W)) u_int_accum (
    .clk,
    .rst_n,
    .valid_i(product_int_valid),
    .clear_i(product_int_clear),
    .lane_sum_i(int_lane_sum),
    .valid_o(int_valid_o),
    .acc_o(int_acc_o)
  );

  fusion_mul16_v2_bf16_accum_dw u_bf16_accum (
    .clk,
    .rst_n,
    .valid_i(product_fp_valid),
    .clear_i(product_fp_clear),
    .lane_item_i(bf16_lane_item),
    .rnd_i(active_rnd),
    .valid_o(fp_valid_o),
    .acc_o(bf16_acc_o),
    .status_o(bf16_status_o)
  );
endmodule

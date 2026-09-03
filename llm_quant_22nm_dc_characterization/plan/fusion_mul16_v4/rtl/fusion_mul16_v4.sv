module fusion_mul16_v4 #(
  parameter int INT_ACC_W = 48,
  parameter int FIXED_MODE = -1,
  parameter bit SUPPORT_FP8 = 1'b1,
  parameter bit SUPPORT_BF16 = 1'b1,
  parameter bit SUPPORT_I4_FP8 = 1'b1,
  parameter bit SUPPORT_I4_BF16 = 1'b1,
  parameter bit SUPPORT_I8_BF16 = 1'b1,
  parameter bit SUPPORT_SPECIALS = 1'b0,
  parameter int IEEE_COMPLIANCE = 0
) (
  input  logic clk,
  input  logic rst_n,
  input  logic cfg_valid_i,
  input  logic [2:0] cfg_mode_i,
  output logic cfg_ready_o,
  output logic cfg_error_o,
  input  logic valid_i,
  output logic in_ready_o,
  input  logic clear_i,
  input  logic last_i,
  input  logic [127:0] lhs_packed_i,
  input  logic [127:0] rhs_packed_i,
  output logic busy_o,
  output logic protocol_error_o,
  output logic int_valid_o,
  output logic int_last_o,
  output logic fp_valid_o,
  output logic fp_last_o,
  output logic clear_done_o,
  output logic signed [INT_ACC_W-1:0] int_acc_o [0:3],
  output logic [31:0] fp_acc_o [0:3],
  output logic [7:0] fp_status_o [0:3],
  output logic [2:0] active_mode_o
);
  localparam int INT_VISIBLE_LATENCY = 4;
  localparam int FP_VISIBLE_LATENCY  = 7;
  logic accept_data, accept_clear, config_protocol_error;
  logic [6:0] active_onehot;
  logic product_int_valid, product_int_clear;
  logic signed [17:0] int_lane_sum [0:3];
  logic product_fp_valid, product_fp_clear;
  logic [15:0] bf16_lane_item [0:3][0:3];
  logic int_clear_done, fp_clear_done;
  logic [FP_VISIBLE_LATENCY-1:0] last_pipe_q;

  fusion_mul16_v4_config #(
    .FIXED_MODE(FIXED_MODE), .SUPPORT_FP8(SUPPORT_FP8),
    .SUPPORT_BF16(SUPPORT_BF16), .SUPPORT_I4_FP8(SUPPORT_I4_FP8),
    .SUPPORT_I4_BF16(SUPPORT_I4_BF16), .SUPPORT_I8_BF16(SUPPORT_I8_BF16),
    .INFLIGHT_DEPTH(8)
  ) u_config (
    .clk, .rst_n, .cfg_valid_i, .cfg_mode_i, .cfg_ready_o, .cfg_error_o,
    .valid_i, .clear_i, .last_i, .in_ready_o,
    .accept_data_o(accept_data), .accept_clear_o(accept_clear),
    .protocol_error_o(config_protocol_error), .busy_o,
    .active_mode_o, .active_onehot_o(active_onehot)
  );

  fusion_mul16_v4_product_pipe #(
    .SUPPORT_FP8(SUPPORT_FP8), .SUPPORT_BF16(SUPPORT_BF16),
    .SUPPORT_I4_FP8(SUPPORT_I4_FP8), .SUPPORT_I4_BF16(SUPPORT_I4_BF16),
    .SUPPORT_I8_BF16(SUPPORT_I8_BF16), .SUPPORT_SPECIALS(SUPPORT_SPECIALS)
  ) u_product_pipe (
    .clk, .rst_n, .valid_i(accept_data), .clear_i(accept_clear),
    .mode_onehot_i(active_onehot), .lhs_packed_i, .rhs_packed_i,
    .int_valid_o(product_int_valid), .int_clear_o(product_int_clear),
    .int_lane_sum_o(int_lane_sum), .fp_valid_o(product_fp_valid),
    .fp_clear_o(product_fp_clear), .bf16_lane_item_o(bf16_lane_item)
  );

  fusion_mul16_v4_int_accum #(.ACC_W(INT_ACC_W)) u_int_accum (
    .clk, .rst_n, .valid_i(product_int_valid), .clear_i(product_int_clear),
    .lane_sum_i(int_lane_sum), .valid_o(int_valid_o),
    .clear_done_o(int_clear_done), .acc_o(int_acc_o)
  );

  fusion_mul16_v4_fp32_recurrent_accum_dw #(.IEEE_COMPLIANCE(IEEE_COMPLIANCE)) u_fp_accum (
    .clk, .rst_n, .valid_i(product_fp_valid), .clear_i(product_fp_clear),
    .lane_item_i(bf16_lane_item), .rnd_i(3'b000), .valid_o(fp_valid_o),
    .clear_done_o(fp_clear_done), .acc_fp32_o(fp_acc_o), .status_o(fp_status_o)
  );

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      last_pipe_q <= '0;
    else
      last_pipe_q <= {last_pipe_q[FP_VISIBLE_LATENCY-2:0], accept_data && last_i};
  end

  assign int_last_o = int_valid_o && last_pipe_q[INT_VISIBLE_LATENCY-1];
  assign fp_last_o  = fp_valid_o  && last_pipe_q[FP_VISIBLE_LATENCY-1];
  assign clear_done_o = fp_clear_done;
  assign protocol_error_o = config_protocol_error;
endmodule

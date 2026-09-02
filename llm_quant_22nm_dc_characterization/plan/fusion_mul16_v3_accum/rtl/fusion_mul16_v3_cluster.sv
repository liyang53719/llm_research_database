module fusion_mul16_v3_cluster #(
  parameter int INT_ACC_W = 48,
  parameter int FIXED_MODE = -1,
  parameter int ACCUM_STYLE = 0,
  parameter bit SUPPORT_FP8 = 1'b1,
  parameter bit SUPPORT_BF16 = 1'b1,
  parameter bit SUPPORT_I4_FP8 = 1'b1,
  parameter bit SUPPORT_I4_BF16 = 1'b1,
  parameter bit SUPPORT_I8_BF16 = 1'b1,
  parameter bit SUPPORT_SPECIALS = 1'b0,
  parameter int BLOCK_PRODUCTS = 64
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
  input  logic flush_i,
  input  logic [127:0] lhs_packed_i,
  input  logic [127:0] rhs_packed_i,
  output logic int_valid_o,
  output logic fp_valid_o,
  output logic flush_done_o,
  output logic protocol_error_o,
  output logic signed [INT_ACC_W-1:0] int_acc_o [0:3],
  output logic [31:0] fp_acc_o [0:3],
  output logic [7:0] fp_status_o [0:3],
  output logic [2:0] active_mode_o
);
  import fusion_mul16_v2_pkg::*;

  localparam int STYLE_FULL_BF16 = 0;
  localparam int STYLE_FP32_RECURRENT = 1;
  localparam int STYLE_BLOCK64_CHECKPOINT = 2;

  logic accept_data;
  logic [2:0] active_mode;
  logic [6:0] active_onehot;
  logic [2:0] active_rnd;
  logic [2:0] items_per_lane;

  logic product_int_valid;
  logic product_int_clear;
  logic signed [17:0] int_lane_sum [0:3];
  logic product_fp_valid;
  logic product_fp_clear;
  logic [15:0] bf16_lane_item [0:3][0:3];

  always_comb begin
    case (active_mode)
      MODE_FP8_FP8, MODE_I4_FP8: items_per_lane = 3'd4;
      MODE_I4_BF16:              items_per_lane = 3'd2;
      default:                    items_per_lane = 3'd1;
    endcase
  end

  fusion_mul16_v2_config #(
    .FIXED_MODE(FIXED_MODE),
    .SUPPORT_FP8(SUPPORT_FP8),
    .SUPPORT_BF16(SUPPORT_BF16),
    .SUPPORT_I4_FP8(SUPPORT_I4_FP8),
    .SUPPORT_I4_BF16(SUPPORT_I4_BF16),
    .SUPPORT_I8_BF16(SUPPORT_I8_BF16),
    .INFLIGHT_DEPTH(14)
  ) u_config (
    .clk, .rst_n, .cfg_valid_i, .cfg_mode_i, .cfg_rnd_i,
    .cfg_ready_o, .cfg_error_o, .valid_i,
    .accept_data_o(accept_data),
    .active_mode_o(active_mode),
    .active_onehot_o(active_onehot),
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
    .clk, .rst_n,
    .valid_i(accept_data),
    .clear_i,
    .mode_onehot_i(active_onehot),
    .lhs_packed_i, .rhs_packed_i,
    .int_valid_o(product_int_valid),
    .int_clear_o(product_int_clear),
    .int_lane_sum_o(int_lane_sum),
    .fp_valid_o(product_fp_valid),
    .fp_clear_o(product_fp_clear),
    .bf16_lane_item_o(bf16_lane_item)
  );

  fusion_mul16_v2_int_accum #(.ACC_W(INT_ACC_W)) u_int_accum (
    .clk, .rst_n,
    .valid_i(product_int_valid),
    .clear_i(product_int_clear),
    .lane_sum_i(int_lane_sum),
    .valid_o(int_valid_o),
    .acc_o(int_acc_o)
  );

  genvar gv;
  generate
    if (ACCUM_STYLE == STYLE_FULL_BF16) begin : G_FULL_BF16
      logic [15:0] bf16_acc [0:3];
      logic [31:0] fp32_view [0:3];
      fusion_mul16_v3_accum_full_bf16_dw u_accum (
        .clk, .rst_n,
        .valid_i(product_fp_valid),
        .clear_i(product_fp_clear),
        .lane_item_i(bf16_lane_item),
        .rnd_i(active_rnd),
        .valid_o(fp_valid_o),
        .acc_bf16_o(bf16_acc),
        .acc_fp32_view_o(fp32_view),
        .status_o(fp_status_o)
      );
      for (gv = 0; gv < 4; gv = gv + 1) begin : G_VIEW
        assign fp_acc_o[gv] = fp32_view[gv];
      end
      assign flush_done_o = 1'b0;
      assign protocol_error_o = flush_i;
    end else if (ACCUM_STYLE == STYLE_FP32_RECURRENT) begin : G_FP32_REC
      fusion_mul16_v3_accum_fp32_recurrent_dw u_accum (
        .clk, .rst_n,
        .valid_i(product_fp_valid),
        .clear_i(product_fp_clear),
        .lane_item_i(bf16_lane_item),
        .rnd_i(active_rnd),
        .valid_o(fp_valid_o),
        .acc_fp32_o(fp_acc_o),
        .status_o(fp_status_o)
      );
      assign flush_done_o = 1'b0;
      assign protocol_error_o = flush_i;
    end else begin : G_BLOCK64
      logic [15:0] partial_unused [0:3];
      logic [6:0] count_unused;
      fusion_mul16_v3_accum_block64_fp32_checkpoint_dw #(
        .BLOCK_PRODUCTS(BLOCK_PRODUCTS),
        .CHECKPOINT_WAIT_CYCLES(2)
      ) u_accum (
        .clk, .rst_n,
        .valid_i(product_fp_valid),
        .clear_i(product_fp_clear),
        .flush_i,
        .items_per_lane_i(items_per_lane),
        .lane_item_i(bf16_lane_item),
        .rnd_i(active_rnd),
        .checkpoint_valid_o(fp_valid_o),
        .flush_done_o,
        .protocol_error_o,
        .checkpoint_fp32_o(fp_acc_o),
        .partial_bf16_o(partial_unused),
        .products_in_partial_o(count_unused),
        .status_o(fp_status_o)
      );
    end
  endgenerate
endmodule

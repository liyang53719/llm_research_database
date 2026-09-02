module fusion_mul16_v3_accum_compare (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic clear_i,
  input  logic flush_i,
  input  logic [2:0] items_per_lane_i,
  input  logic [15:0] lane_item_i [0:3][0:3],
  input  logic [2:0] rnd_i,
  output logic full_bf16_valid_o,
  output logic fp32_recurrent_valid_o,
  output logic checkpoint_valid_o,
  output logic checkpoint_flush_done_o,
  output logic [15:0] full_bf16_acc_o [0:3],
  output logic [31:0] fp32_recurrent_acc_o [0:3],
  output logic [31:0] checkpoint_acc_o [0:3],
  output logic checkpoint_protocol_error_o
);
  logic [31:0] unused_full_view [0:3];
  logic [7:0] unused_status0 [0:3];
  logic [7:0] unused_status1 [0:3];
  logic [7:0] unused_status2 [0:3];
  logic [15:0] unused_partial [0:3];
  logic [6:0] unused_count;

  fusion_mul16_v3_accum_full_bf16_dw u_full_bf16 (
    .clk, .rst_n, .valid_i, .clear_i, .lane_item_i, .rnd_i,
    .valid_o(full_bf16_valid_o), .acc_bf16_o(full_bf16_acc_o),
    .acc_fp32_view_o(unused_full_view), .status_o(unused_status0)
  );

  fusion_mul16_v3_accum_fp32_recurrent_dw u_fp32_recurrent (
    .clk, .rst_n, .valid_i, .clear_i, .lane_item_i, .rnd_i,
    .valid_o(fp32_recurrent_valid_o), .acc_fp32_o(fp32_recurrent_acc_o),
    .status_o(unused_status1)
  );

  fusion_mul16_v3_accum_block64_fp32_checkpoint_dw u_block64 (
    .clk, .rst_n, .valid_i, .clear_i, .flush_i, .items_per_lane_i,
    .lane_item_i, .rnd_i, .checkpoint_valid_o,
    .flush_done_o(checkpoint_flush_done_o),
    .protocol_error_o(checkpoint_protocol_error_o),
    .checkpoint_fp32_o(checkpoint_acc_o),
    .partial_bf16_o(unused_partial),
    .products_in_partial_o(unused_count),
    .status_o(unused_status2)
  );
endmodule

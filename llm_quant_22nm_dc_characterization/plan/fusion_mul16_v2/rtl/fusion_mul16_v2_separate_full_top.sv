module fusion_mul16_v2_separate_full_top (
  input  logic clk,
  input  logic rst_n,
  input  logic int_cfg_valid_i,
  input  logic [2:0] int_cfg_mode_i,
  output logic int_cfg_ready_o,
  output logic int_cfg_error_o,
  input  logic int_valid_i,
  input  logic int_clear_i,
  input  logic [127:0] int_lhs_i,
  input  logic [127:0] int_rhs_i,
  input  logic fp8_valid_i,
  input  logic fp8_clear_i,
  input  logic [127:0] fp8_lhs_i,
  input  logic [127:0] fp8_rhs_i,
  input  logic bf16_valid_i,
  input  logic bf16_clear_i,
  input  logic [127:0] bf16_lhs_i,
  input  logic [127:0] bf16_rhs_i,
  output logic int_valid_o,
  output logic fp8_valid_o,
  output logic bf16_valid_o,
  output logic signed [47:0] int_acc_o [0:3],
  output logic [15:0] fp8_acc_o [0:3],
  output logic [15:0] bf16_acc_o [0:3]
);
  import fusion_mul16_v2_pkg::*;
  logic cfg_ready_unused [0:2];
  logic cfg_error_unused [0:2];
  logic int_unused [0:1];
  logic fp_unused;
  logic signed [47:0] int_acc_unused [0:1][0:3];
  logic [15:0] bf16_acc_unused [0:3];
  logic [7:0] status_unused [0:2][0:3];
  logic [2:0] mode_unused [0:2];
  fusion_mul16_v2_cluster #(
    .FIXED_MODE(-1),
    .SUPPORT_FP8(1'b0), .SUPPORT_BF16(1'b0),
    .SUPPORT_I4_FP8(1'b0), .SUPPORT_I4_BF16(1'b0), .SUPPORT_I8_BF16(1'b0)
  ) u_int (
    .clk, .rst_n,
    .cfg_valid_i(int_cfg_valid_i), .cfg_mode_i(int_cfg_mode_i), .cfg_rnd_i(3'b000),
    .cfg_ready_o(int_cfg_ready_o), .cfg_error_o(int_cfg_error_o),
    .valid_i(int_valid_i), .clear_i(int_clear_i),
    .lhs_packed_i(int_lhs_i), .rhs_packed_i(int_rhs_i),
    .int_valid_o(int_valid_o), .fp_valid_o(fp_unused),
    .int_acc_o(int_acc_o), .bf16_acc_o(bf16_acc_unused),
    .bf16_status_o(status_unused[0]), .active_mode_o(mode_unused[0])
  );

  fusion_mul16_v2_cluster #(
    .FIXED_MODE(MODE_FP8_FP8),
    .SUPPORT_FP8(1'b1), .SUPPORT_BF16(1'b0),
    .SUPPORT_I4_FP8(1'b0), .SUPPORT_I4_BF16(1'b0), .SUPPORT_I8_BF16(1'b0)
  ) u_fp8 (
    .clk, .rst_n,
    .cfg_valid_i(1'b0), .cfg_mode_i('0), .cfg_rnd_i(3'b000),
    .cfg_ready_o(cfg_ready_unused[1]), .cfg_error_o(cfg_error_unused[1]),
    .valid_i(fp8_valid_i), .clear_i(fp8_clear_i),
    .lhs_packed_i(fp8_lhs_i), .rhs_packed_i(fp8_rhs_i),
    .int_valid_o(int_unused[0]), .fp_valid_o(fp8_valid_o),
    .int_acc_o(int_acc_unused[0]), .bf16_acc_o(fp8_acc_o),
    .bf16_status_o(status_unused[1]), .active_mode_o(mode_unused[1])
  );

  fusion_mul16_v2_cluster #(
    .FIXED_MODE(MODE_BF16_BF16),
    .SUPPORT_FP8(1'b0), .SUPPORT_BF16(1'b1),
    .SUPPORT_I4_FP8(1'b0), .SUPPORT_I4_BF16(1'b0), .SUPPORT_I8_BF16(1'b0)
  ) u_bf16 (
    .clk, .rst_n,
    .cfg_valid_i(1'b0), .cfg_mode_i('0), .cfg_rnd_i(3'b000),
    .cfg_ready_o(cfg_ready_unused[2]), .cfg_error_o(cfg_error_unused[2]),
    .valid_i(bf16_valid_i), .clear_i(bf16_clear_i),
    .lhs_packed_i(bf16_lhs_i), .rhs_packed_i(bf16_rhs_i),
    .int_valid_o(int_unused[1]), .fp_valid_o(bf16_valid_o),
    .int_acc_o(int_acc_unused[1]), .bf16_acc_o(bf16_acc_o),
    .bf16_status_o(status_unused[2]), .active_mode_o(mode_unused[2])
  );
endmodule

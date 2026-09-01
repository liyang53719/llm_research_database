module fusion_mul16_separate_reference_pipe_dw #(
  parameter int INT_ACC_W = 48
) (
  input  logic clk,
  input  logic rst_n,
  input  logic [1:0] int_mode_i,
  input  logic int_valid_i,
  input  logic int_clear_i,
  input  logic [15:0] int_lhs_i [0:15],
  input  logic [15:0] int_rhs_i [0:15],
  input  logic fp8_valid_i,
  input  logic fp8_clear_i,
  input  logic [15:0] fp8_lhs_i [0:15],
  input  logic [15:0] fp8_rhs_i [0:15],
  input  logic bf16_valid_i,
  input  logic bf16_clear_i,
  input  logic [15:0] bf16_lhs_i [0:15],
  input  logic [15:0] bf16_rhs_i [0:15],
  input  logic [2:0] rnd_i,
  output logic int_valid_o,
  output logic fp8_valid_o,
  output logic bf16_valid_o,
  output logic signed [INT_ACC_W-1:0] int_acc_o [0:3],
  output logic [31:0] fp8_acc_o [0:3],
  output logic [31:0] bf16_acc_o [0:3],
  output logic [7:0] fp8_status_o [0:3],
  output logic [7:0] bf16_status_o [0:3]
);
  import fusion_mul16_pkg::*;

  logic [3:0] safe_int_mode;
  logic int_fp_unused;
  logic fp8_int_unused;
  logic bf16_int_unused;
  logic [31:0] int_fp_acc_unused [0:3];
  logic signed [INT_ACC_W-1:0] fp8_int_acc_unused [0:3];
  logic signed [INT_ACC_W-1:0] bf16_int_acc_unused [0:3];
  logic [7:0] int_fp_status_unused [0:3];

  assign safe_int_mode = {2'b00, int_mode_i};

  fusion_mul16_cluster_dw_pipe #(.INT_ACC_W(INT_ACC_W)) u_int_cluster (
    .clk, .rst_n, .valid_i(int_valid_i), .clear_i(int_clear_i),
    .mode_i(safe_int_mode), .lhs_i(int_lhs_i), .rhs_i(int_rhs_i), .rnd_i,
    .int_valid_o(int_valid_o), .fp_valid_o(int_fp_unused),
    .int_acc_o(int_acc_o), .fp_acc_o(int_fp_acc_unused),
    .fp_status_o(int_fp_status_unused)
  );

  fusion_mul16_cluster_dw_pipe #(.INT_ACC_W(INT_ACC_W)) u_fp8_cluster (
    .clk, .rst_n, .valid_i(fp8_valid_i), .clear_i(fp8_clear_i),
    .mode_i(MODE_FP8_FP8), .lhs_i(fp8_lhs_i), .rhs_i(fp8_rhs_i), .rnd_i,
    .int_valid_o(fp8_int_unused), .fp_valid_o(fp8_valid_o),
    .int_acc_o(fp8_int_acc_unused), .fp_acc_o(fp8_acc_o),
    .fp_status_o(fp8_status_o)
  );

  fusion_mul16_cluster_dw_pipe #(.INT_ACC_W(INT_ACC_W)) u_bf16_cluster (
    .clk, .rst_n, .valid_i(bf16_valid_i), .clear_i(bf16_clear_i),
    .mode_i(MODE_BF16_BF16), .lhs_i(bf16_lhs_i), .rhs_i(bf16_rhs_i), .rnd_i,
    .int_valid_o(bf16_int_unused), .fp_valid_o(bf16_valid_o),
    .int_acc_o(bf16_int_acc_unused), .fp_acc_o(bf16_acc_o),
    .fp_status_o(bf16_status_o)
  );
endmodule

module fusion_mul16_fp8_only_pipe_top (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic clear_i,
  input  logic [15:0] lhs_i [0:15],
  input  logic [15:0] rhs_i [0:15],
  input  logic [2:0] rnd_i,
  output logic valid_o,
  output logic [31:0] acc_o [0:3],
  output logic [7:0] status_o [0:3]
);
  import fusion_mul16_pkg::*;
  logic int_valid_unused;
  logic signed [47:0] int_acc_unused [0:3];
  fusion_mul16_cluster_dw_pipe u_cluster (
    .clk, .rst_n, .valid_i, .clear_i, .mode_i(MODE_FP8_FP8), .lhs_i, .rhs_i,
    .rnd_i, .int_valid_o(int_valid_unused), .fp_valid_o(valid_o),
    .int_acc_o(int_acc_unused), .fp_acc_o(acc_o), .fp_status_o(status_o)
  );
endmodule

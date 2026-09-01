module fusion_mul16_int_only_pipe_top #(
  parameter int INT_ACC_W = 48
) (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic clear_i,
  input  logic [1:0] int_mode_i,
  input  logic [15:0] lhs_i [0:15],
  input  logic [15:0] rhs_i [0:15],
  output logic valid_o,
  output logic signed [INT_ACC_W-1:0] acc_o [0:3]
);
  logic [3:0] safe_mode;
  logic fp_valid_unused;
  logic [31:0] fp_acc_unused [0:3];
  logic [7:0] fp_status_unused [0:3];
  assign safe_mode = {2'b00, int_mode_i};
  fusion_mul16_cluster_dw_pipe #(.INT_ACC_W(INT_ACC_W)) u_cluster (
    .clk, .rst_n, .valid_i, .clear_i, .mode_i(safe_mode), .lhs_i, .rhs_i,
    .rnd_i(3'b000), .int_valid_o(valid_o), .fp_valid_o(fp_valid_unused),
    .int_acc_o(acc_o), .fp_acc_o(fp_acc_unused), .fp_status_o(fp_status_unused)
  );
endmodule

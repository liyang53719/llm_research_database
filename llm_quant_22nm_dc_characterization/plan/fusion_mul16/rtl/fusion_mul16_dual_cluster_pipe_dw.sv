module fusion_mul16_dual_cluster_pipe_dw #(
  parameter int INT_ACC_W = 48
) (
  input  logic clk,
  input  logic rst_n,
  input  logic valid0_i,
  input  logic valid1_i,
  input  logic clear0_i,
  input  logic clear1_i,
  input  logic [3:0] mode0_i,
  input  logic [3:0] mode1_i,
  input  logic [15:0] lhs0_i [0:15],
  input  logic [15:0] rhs0_i [0:15],
  input  logic [15:0] lhs1_i [0:15],
  input  logic [15:0] rhs1_i [0:15],
  input  logic [2:0] rnd_i,
  output logic int_valid0_o,
  output logic fp_valid0_o,
  output logic int_valid1_o,
  output logic fp_valid1_o,
  output logic signed [INT_ACC_W-1:0] int_acc0_o [0:3],
  output logic signed [INT_ACC_W-1:0] int_acc1_o [0:3],
  output logic [31:0] fp_acc0_o [0:3],
  output logic [31:0] fp_acc1_o [0:3],
  output logic [7:0] fp_status0_o [0:3],
  output logic [7:0] fp_status1_o [0:3]
);
  fusion_mul16_cluster_dw_pipe #(.INT_ACC_W(INT_ACC_W)) u_cluster0 (
    .clk, .rst_n, .valid_i(valid0_i), .clear_i(clear0_i), .mode_i(mode0_i),
    .lhs_i(lhs0_i), .rhs_i(rhs0_i), .rnd_i,
    .int_valid_o(int_valid0_o), .fp_valid_o(fp_valid0_o),
    .int_acc_o(int_acc0_o), .fp_acc_o(fp_acc0_o), .fp_status_o(fp_status0_o)
  );
  fusion_mul16_cluster_dw_pipe #(.INT_ACC_W(INT_ACC_W)) u_cluster1 (
    .clk, .rst_n, .valid_i(valid1_i), .clear_i(clear1_i), .mode_i(mode1_i),
    .lhs_i(lhs1_i), .rhs_i(rhs1_i), .rnd_i,
    .int_valid_o(int_valid1_o), .fp_valid_o(fp_valid1_o),
    .int_acc_o(int_acc1_o), .fp_acc_o(fp_acc1_o), .fp_status_o(fp_status1_o)
  );
endmodule

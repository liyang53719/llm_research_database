module fusion_mul16_v4_flat #(
  parameter int INT_ACC_W = 48,
  parameter int FIXED_MODE = -1,
  parameter bit SUPPORT_SPECIALS = 1'b0,
  parameter int IEEE_COMPLIANCE = 0
) (
  input logic clk, rst_n,
  input logic cfg_valid_i,
  input logic [2:0] cfg_mode_i,
  output logic cfg_ready_o, cfg_error_o,
  input logic valid_i,
  output logic in_ready_o,
  input logic clear_i, last_i,
  input logic [127:0] lhs_packed_i, rhs_packed_i,
  output logic busy_o, protocol_error_o,
  output logic int_valid_o, int_last_o, fp_valid_o, fp_last_o, clear_done_o,
  output logic [4*INT_ACC_W-1:0] int_acc_packed_o,
  output logic [127:0] fp_acc_packed_o,
  output logic [31:0] fp_status_packed_o,
  output logic [2:0] active_mode_o
);
  logic signed [INT_ACC_W-1:0] int_acc [0:3];
  logic [31:0] fp_acc [0:3];
  logic [7:0] fp_status [0:3];
  fusion_mul16_v4 #(.INT_ACC_W(INT_ACC_W),.FIXED_MODE(FIXED_MODE),.SUPPORT_SPECIALS(SUPPORT_SPECIALS),.IEEE_COMPLIANCE(IEEE_COMPLIANCE)) u_core (
    .clk,.rst_n,.cfg_valid_i,.cfg_mode_i,.cfg_ready_o,.cfg_error_o,
    .valid_i,.in_ready_o,.clear_i,.last_i,.lhs_packed_i,.rhs_packed_i,
    .busy_o,.protocol_error_o,.int_valid_o,.int_last_o,.fp_valid_o,.fp_last_o,
    .clear_done_o,.int_acc_o(int_acc),.fp_acc_o(fp_acc),.fp_status_o(fp_status),.active_mode_o
  );
  genvar g;
  generate for (g=0;g<4;g=g+1) begin:G_PACK
    assign int_acc_packed_o[g*INT_ACC_W +: INT_ACC_W]=int_acc[g];
    assign fp_acc_packed_o[g*32 +: 32]=fp_acc[g];
    assign fp_status_packed_o[g*8 +: 8]=fp_status[g];
  end endgenerate
endmodule

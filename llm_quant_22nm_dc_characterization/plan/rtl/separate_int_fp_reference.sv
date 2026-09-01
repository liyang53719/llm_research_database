// Independent INT and FP arithmetic reference. Both outputs remain visible.
module separate_int_fp_reference #(
  parameter int INT_W_W=4, INT_A_W=8, INT_LANES=4, INT_ACC_W=40,
  parameter int FP_SIG_WIDTH=3, FP_EXP_WIDTH=4
) (
  input logic clk,rst_n,int_valid_i,int_clear_i,fp_valid_i,
  input logic signed [INT_LANES*INT_W_W-1:0] int_w_i,
  input logic signed [INT_LANES*INT_A_W-1:0] int_a_i,
  input logic [FP_SIG_WIDTH+FP_EXP_WIDTH:0] fp_a_i,fp_b_i,fp_c_i,
  input logic [2:0] rnd_i,
  output logic int_valid_o,fp_valid_o,
  output logic signed [INT_ACC_W-1:0] int_acc_o,
  output logic [FP_SIG_WIDTH+FP_EXP_WIDTH:0] fp_z_o,
  output logic [7:0] fp_status_o
);
  packed_dot_pe #(.W_W(INT_W_W),.A_W(INT_A_W),.LANES(INT_LANES),.ACC_W(INT_ACC_W))
  u_int(.clk,.rst_n,.valid_i(int_valid_i),.clear_i(int_clear_i),
        .w_vec_i(int_w_i),.a_vec_i(int_a_i),.valid_o(int_valid_o),.acc_o(int_acc_o));
  fp_mac_dw #(.SIG_WIDTH(FP_SIG_WIDTH),.EXP_WIDTH(FP_EXP_WIDTH),.IEEE_COMPLIANCE(0))
  u_fp(.clk,.rst_n,.valid_i(fp_valid_i),.a_i(fp_a_i),.b_i(fp_b_i),.c_i(fp_c_i),
       .rnd_i,.valid_o(fp_valid_o),.z_o(fp_z_o),.status_o(fp_status_o));
endmodule

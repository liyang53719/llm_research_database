// Dynamic mode wrapper; arithmetic is still physically separate.
module dual_domain_int_fp_reference #(
  parameter int INT_W_W=4, INT_A_W=8, INT_LANES=4, INT_ACC_W=40,
  parameter int FP_SIG_WIDTH=3, FP_EXP_WIDTH=4
) (
  input logic clk,rst_n,mode_fp_i,valid_i,clear_i,
  input logic signed [INT_LANES*INT_W_W-1:0] int_w_i,
  input logic signed [INT_LANES*INT_A_W-1:0] int_a_i,
  input logic [FP_SIG_WIDTH+FP_EXP_WIDTH:0] fp_a_i,fp_b_i,fp_c_i,
  input logic [2:0] rnd_i,
  output logic valid_o,
  output logic signed [INT_ACC_W-1:0] int_result_o,
  output logic [FP_SIG_WIDTH+FP_EXP_WIDTH:0] fp_result_o
);
  logic iv,fv; logic [7:0] unused;
  packed_dot_pe #(.W_W(INT_W_W),.A_W(INT_A_W),.LANES(INT_LANES),.ACC_W(INT_ACC_W))
  u_int(.clk,.rst_n,.valid_i(valid_i&~mode_fp_i),.clear_i(clear_i),
        .w_vec_i(int_w_i),.a_vec_i(int_a_i),.valid_o(iv),.acc_o(int_result_o));
  fp_mac_dw #(.SIG_WIDTH(FP_SIG_WIDTH),.EXP_WIDTH(FP_EXP_WIDTH),.IEEE_COMPLIANCE(0))
  u_fp(.clk,.rst_n,.valid_i(valid_i&mode_fp_i),.a_i(fp_a_i),.b_i(fp_b_i),
       .c_i(fp_c_i),.rnd_i,.valid_o(fv),.z_o(fp_result_o),.status_o(unused));
  assign valid_o = mode_fp_i ? fv : iv;
endmodule

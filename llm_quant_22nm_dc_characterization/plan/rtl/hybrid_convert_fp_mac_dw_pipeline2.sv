// Three registered boundaries: converted operands, multiplier output, adder
// output. Throughput remains one result per cycle after fill.
module hybrid_convert_fp_mac_dw_pipeline2 #(
  parameter int SIG_WIDTH=7,EXP_WIDTH=8,IEEE_COMPLIANCE=0,INT_WIDTH=4
) (
  input logic clk,rst_n,valid_i,input logic [1:0] a_format_i,b_format_i,
  input logic [15:0] a_bits_i,b_bits_i,
  input logic [SIG_WIDTH+EXP_WIDTH:0] acc_i,input logic [2:0] rnd_i,
  output logic valid_o,output logic [SIG_WIDTH+EXP_WIDTH:0] z_o,
  output logic [7:0] status_o
);
  localparam int FP_W=SIG_WIDTH+EXP_WIDTH+1;
  logic [INT_WIDTH-1:0] a_int,b_int;
  logic [FP_W-1:0] a_ifp,b_ifp,a_sel,b_sel,a_q,b_q,acc_q;
  logic [FP_W-1:0] product_comb,product_q,acc_q2,z_comb;
  logic [2:0] rnd_q,rnd_q2;
  logic [7:0] as,bs,convert_status_q,mult_status_comb,mult_status_q,add_status;
  logic valid_q,valid_q2;
  assign a_int=a_bits_i[INT_WIDTH-1:0];assign b_int=b_bits_i[INT_WIDTH-1:0];
  DW_fp_i2flt #(SIG_WIDTH,EXP_WIDTH,INT_WIDTH,1) ua(.a(a_int),.rnd(rnd_i),.z(a_ifp),.status(as));
  DW_fp_i2flt #(SIG_WIDTH,EXP_WIDTH,INT_WIDTH,1) ub(.a(b_int),.rnd(rnd_i),.z(b_ifp),.status(bs));
  assign a_sel=(a_format_i<=1)?a_ifp:a_bits_i[FP_W-1:0];
  assign b_sel=(b_format_i<=1)?b_ifp:b_bits_i[FP_W-1:0];
  DW_fp_mult #(SIG_WIDTH,EXP_WIDTH,IEEE_COMPLIANCE) um(
    .a(a_q),.b(b_q),.rnd(rnd_q),.z(product_comb),.status(mult_status_comb));
  DW_fp_add #(SIG_WIDTH,EXP_WIDTH,IEEE_COMPLIANCE) ud(
    .a(product_q),.b(acc_q2),.rnd(rnd_q2),.z(z_comb),.status(add_status));
  always_ff @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
      a_q<='0;b_q<='0;acc_q<='0;rnd_q<='0;convert_status_q<='0;valid_q<=0;
      product_q<='0;acc_q2<='0;rnd_q2<='0;mult_status_q<='0;valid_q2<=0;
      valid_o<=0;z_o<='0;status_o<='0;
    end else begin
      a_q<=a_sel;b_q<=b_sel;acc_q<=acc_i;rnd_q<=rnd_i;convert_status_q<=as|bs;valid_q<=valid_i;
      product_q<=product_comb;acc_q2<=acc_q;rnd_q2<=rnd_q;
      mult_status_q<=convert_status_q|mult_status_comb;valid_q2<=valid_q;
      valid_o<=valid_q2;z_o<=z_comb;status_o<=mult_status_q|add_status;
    end
  end
endmodule

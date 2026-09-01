// Registers converted/raw operands before the DW_fp_mac stage.
module hybrid_convert_fp_mac_dw_pipeline #(
  parameter int SIG_WIDTH=3,
  parameter int EXP_WIDTH=4,
  parameter int IEEE_COMPLIANCE=0,
  parameter int INT_WIDTH=4
) (
  input logic clk,rst_n,valid_i,
  input logic [1:0] a_format_i,b_format_i,
  input logic [15:0] a_bits_i,b_bits_i,
  input logic [SIG_WIDTH+EXP_WIDTH:0] acc_i,
  input logic [2:0] rnd_i,
  output logic valid_o,
  output logic [SIG_WIDTH+EXP_WIDTH:0] z_o,
  output logic [7:0] status_o
);
  localparam int FP_W=SIG_WIDTH+EXP_WIDTH+1;
  logic [INT_WIDTH-1:0] a_int,b_int;
  logic [FP_W-1:0] a_int_fp,b_int_fp,a_selected,b_selected;
  logic [FP_W-1:0] a_q,b_q,acc_q,z_comb;
  logic [2:0] rnd_q;
  logic [7:0] a_status,b_status,convert_status_q,mac_status;
  logic valid_q;

  assign a_int=a_bits_i[INT_WIDTH-1:0];
  assign b_int=b_bits_i[INT_WIDTH-1:0];
  DW_fp_i2flt #(SIG_WIDTH,EXP_WIDTH,INT_WIDTH,1) u_a_i2f(
    .a(a_int),.rnd(rnd_i),.z(a_int_fp),.status(a_status));
  DW_fp_i2flt #(SIG_WIDTH,EXP_WIDTH,INT_WIDTH,1) u_b_i2f(
    .a(b_int),.rnd(rnd_i),.z(b_int_fp),.status(b_status));
  assign a_selected=(a_format_i<=2'd1)?a_int_fp:a_bits_i[FP_W-1:0];
  assign b_selected=(b_format_i<=2'd1)?b_int_fp:b_bits_i[FP_W-1:0];
  DW_fp_mac #(SIG_WIDTH,EXP_WIDTH,IEEE_COMPLIANCE) u_mac(
    .a(a_q),.b(b_q),.c(acc_q),.rnd(rnd_q),.z(z_comb),.status(mac_status));

  always_ff @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
      a_q<='0;b_q<='0;acc_q<='0;rnd_q<='0;convert_status_q<='0;valid_q<=1'b0;
      valid_o<=1'b0;z_o<='0;status_o<='0;
    end else begin
      a_q<=a_selected;b_q<=b_selected;acc_q<=acc_i;rnd_q<=rnd_i;
      convert_status_q<=a_status|b_status;valid_q<=valid_i;
      valid_o<=valid_q;z_o<=z_comb;status_o<=convert_status_q|mac_status;
    end
  end
endmodule

// Two arithmetic stages: DW_fp_mult, register, then DW_fp_add and output
// register. Throughput is one operation per cycle after pipeline fill.
module pipelined_fp_mac_dw #(
  parameter int SIG_WIDTH=7,
  parameter int EXP_WIDTH=8,
  parameter int IEEE_COMPLIANCE=0
) (
  input logic clk,rst_n,valid_i,
  input logic [SIG_WIDTH+EXP_WIDTH:0] a_i,b_i,c_i,
  input logic [2:0] rnd_i,
  output logic valid_o,
  output logic [SIG_WIDTH+EXP_WIDTH:0] z_o,
  output logic [7:0] status_o
);
  localparam int FP_W=SIG_WIDTH+EXP_WIDTH+1;
  logic [FP_W-1:0] product_comb,product_q,c_q,z_comb;
  logic [2:0] rnd_q;
  logic [7:0] mult_status_comb,mult_status_q,add_status_comb;
  logic valid_q;

  DW_fp_mult #(SIG_WIDTH,EXP_WIDTH,IEEE_COMPLIANCE) u_mult(
    .a(a_i),.b(b_i),.rnd(rnd_i),.z(product_comb),.status(mult_status_comb)
  );
  DW_fp_add #(SIG_WIDTH,EXP_WIDTH,IEEE_COMPLIANCE) u_add(
    .a(product_q),.b(c_q),.rnd(rnd_q),.z(z_comb),.status(add_status_comb)
  );

  always_ff @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
      product_q<='0; c_q<='0; rnd_q<='0; mult_status_q<='0; valid_q<=1'b0;
      z_o<='0; status_o<='0; valid_o<=1'b0;
    end else begin
      product_q<=product_comb; c_q<=c_i; rnd_q<=rnd_i;
      mult_status_q<=mult_status_comb; valid_q<=valid_i;
      z_o<=z_comb; status_o<=mult_status_q|add_status_comb; valid_o<=valid_q;
    end
  end
endmodule

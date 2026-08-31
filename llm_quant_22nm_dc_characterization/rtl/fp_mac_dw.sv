module fp_mac_dw #(
  parameter int SIG_WIDTH = 7,
  parameter int EXP_WIDTH = 8,
  parameter int IEEE_COMPLIANCE = 0
) (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic [SIG_WIDTH+EXP_WIDTH:0] a_i,
  input  logic [SIG_WIDTH+EXP_WIDTH:0] b_i,
  input  logic [SIG_WIDTH+EXP_WIDTH:0] c_i,
  input  logic [2:0] rnd_i,
  output logic valid_o,
  output logic [SIG_WIDTH+EXP_WIDTH:0] z_o,
  output logic [7:0] status_o
);
  logic [SIG_WIDTH+EXP_WIDTH:0] z_comb;
  logic [7:0] status_comb;

  DW_fp_mac #(SIG_WIDTH, EXP_WIDTH, IEEE_COMPLIANCE) u_dw_fp_mac (
    .a(a_i),
    .b(b_i),
    .c(c_i),
    .rnd(rnd_i),
    .z(z_comb),
    .status(status_comb)
  );

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      z_o      <= '0;
      status_o <= '0;
      valid_o  <= 1'b0;
    end else begin
      z_o      <= z_comb;
      status_o <= status_comb;
      valid_o  <= valid_i;
    end
  end
endmodule

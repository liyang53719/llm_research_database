module int_mac #(
  parameter int W_W = 4,
  parameter int A_W = 8,
  parameter int ACC_W = 24
) (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic clear_i,
  input  logic signed [W_W-1:0] w_i,
  input  logic signed [A_W-1:0] a_i,
  output logic valid_o,
  output logic signed [ACC_W-1:0] acc_o
);
  localparam int PROD_W = W_W + A_W;
  logic signed [PROD_W-1:0] product_comb;
  logic signed [PROD_W-1:0] product_q;
  logic valid_q;

  DW02_mult #(W_W, A_W) u_dw_mult (
    .A(w_i),
    .B(a_i),
    .TC(1'b1),
    .PRODUCT(product_comb)
  );

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      product_q <= '0;
      valid_q   <= 1'b0;
      acc_o     <= '0;
      valid_o   <= 1'b0;
    end else begin
      product_q <= product_comb;
      valid_q   <= valid_i;
      valid_o   <= valid_q;
      if (clear_i)
        acc_o <= '0;
      else if (valid_q)
        acc_o <= acc_o + {{(ACC_W-PROD_W){product_q[PROD_W-1]}}, product_q};
    end
  end
endmodule

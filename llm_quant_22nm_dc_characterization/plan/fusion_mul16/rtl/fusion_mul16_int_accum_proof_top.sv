module fusion_mul16_int_accum_proof_top (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic clear_i,
  input  logic [3:0] mode_i,
  input  logic signed [32:0] product_i [0:15],
  input  logic [15:0] product_valid_i,
  output logic valid_o,
  output logic signed [47:0] acc_o [0:3]
);
  fusion_mul16_int_accum #(.ACC_W(48)) u_acc (
    .clk, .rst_n, .valid_i, .clear_i, .mode_i,
    .product_i, .product_valid_i, .valid_o, .acc_o
  );
endmodule

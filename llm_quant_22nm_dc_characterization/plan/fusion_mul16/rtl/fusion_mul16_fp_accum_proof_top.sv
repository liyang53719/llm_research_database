module fusion_mul16_fp_accum_proof_top (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic clear_i,
  input  logic [3:0] mode_i,
  input  logic [31:0] product_i [0:15],
  input  logic [15:0] product_valid_i,
  input  logic [2:0] rnd_i,
  output logic valid_o,
  output logic [31:0] acc_o [0:3],
  output logic [7:0] status_o [0:3]
);
  fusion_mul16_fp32_accum_dw u_acc (
    .clk, .rst_n, .valid_i, .clear_i, .mode_i,
    .product_i, .product_valid_i, .rnd_i,
    .valid_o, .acc_o, .status_o
  );
endmodule

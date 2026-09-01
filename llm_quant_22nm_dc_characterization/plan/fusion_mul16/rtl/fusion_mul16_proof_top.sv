module fusion_mul16_proof_top (
  input  logic clk,
  input  logic rst_n,
  input  logic [3:0] mode_i,
  input  logic [15:0] lhs_i [0:15],
  input  logic [15:0] rhs_i [0:15],
  output logic [31:0] int_signature_o,
  output logic [31:0] fp_signature_o,
  output logic [15:0] valid_signature_o
);
  logic signed [32:0] int_product [0:15];
  logic [31:0] fp_product [0:15];
  logic [15:0] product_valid;
  logic [4:0] product_count;
  logic [31:0] int_signature_comb;
  logic [31:0] fp_signature_comb;
  integer i;

  fusion_mul16_product_core u_core (
    .mode_i,
    .lhs_i,
    .rhs_i,
    .int_product_o(int_product),
    .fp_product_o(fp_product),
    .product_valid_o(product_valid),
    .product_count_o(product_count)
  );

  always_comb begin
    int_signature_comb = {27'b0, product_count};
    fp_signature_comb = {27'b0, product_count};
    for (i = 0; i < 16; i = i + 1) begin
      int_signature_comb = int_signature_comb ^ int_product[i][31:0];
      fp_signature_comb = fp_signature_comb ^ fp_product[i];
    end
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      int_signature_o <= '0;
      fp_signature_o <= '0;
      valid_signature_o <= '0;
    end else begin
      int_signature_o <= int_signature_comb;
      fp_signature_o <= fp_signature_comb;
      valid_signature_o <= product_valid;
    end
  end
endmodule

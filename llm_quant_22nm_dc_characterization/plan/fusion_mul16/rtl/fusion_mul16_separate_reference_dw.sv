module fusion_mul16_separate_reference_dw #(
  parameter int INT_ACC_W = 48
) (
  input  logic clk,
  input  logic rst_n,
  input  logic [3:0] int_mode_i,
  input  logic int_valid_i,
  input  logic int_clear_i,
  input  logic [15:0] int_lhs_i [0:15],
  input  logic [15:0] int_rhs_i [0:15],
  input  logic fp8_valid_i,
  input  logic fp8_clear_i,
  input  logic [15:0] fp8_lhs_i [0:15],
  input  logic [15:0] fp8_rhs_i [0:15],
  input  logic bf16_valid_i,
  input  logic bf16_clear_i,
  input  logic [15:0] bf16_lhs_i [0:15],
  input  logic [15:0] bf16_rhs_i [0:15],
  input  logic [2:0] rnd_i,
  output logic int_valid_o,
  output logic fp8_valid_o,
  output logic bf16_valid_o,
  output logic signed [INT_ACC_W-1:0] int_acc_o [0:3],
  output logic [31:0] fp8_acc_o [0:3],
  output logic [31:0] bf16_acc_o [0:3],
  output logic [7:0] fp8_status_o [0:3],
  output logic [7:0] bf16_status_o [0:3]
);
  import fusion_mul16_pkg::*;

  logic signed [32:0] int_product [0:15];
  logic [31:0] int_fp_unused [0:15];
  logic [15:0] int_product_valid;
  logic [4:0] int_product_count;

  logic signed [32:0] fp8_int_unused [0:15];
  logic [31:0] fp8_product [0:15];
  logic [15:0] fp8_product_valid;
  logic [4:0] fp8_product_count;

  logic signed [32:0] bf16_int_unused [0:15];
  logic [31:0] bf16_product [0:15];
  logic [15:0] bf16_product_valid;
  logic [4:0] bf16_product_count;

  fusion_mul16_product_core u_int_core (
    .mode_i(int_mode_i), .lhs_i(int_lhs_i), .rhs_i(int_rhs_i),
    .int_product_o(int_product), .fp_product_o(int_fp_unused),
    .product_valid_o(int_product_valid), .product_count_o(int_product_count)
  );
  fusion_mul16_int_accum #(.ACC_W(INT_ACC_W)) u_int_acc (
    .clk, .rst_n, .valid_i(int_valid_i), .clear_i(int_clear_i),
    .mode_i(int_mode_i), .product_i(int_product),
    .product_valid_i(int_product_valid), .valid_o(int_valid_o), .acc_o(int_acc_o)
  );

  fusion_mul16_product_core u_fp8_core (
    .mode_i(MODE_FP8_FP8), .lhs_i(fp8_lhs_i), .rhs_i(fp8_rhs_i),
    .int_product_o(fp8_int_unused), .fp_product_o(fp8_product),
    .product_valid_o(fp8_product_valid), .product_count_o(fp8_product_count)
  );
  fusion_mul16_fp32_accum_dw u_fp8_acc (
    .clk, .rst_n, .valid_i(fp8_valid_i), .clear_i(fp8_clear_i),
    .mode_i(MODE_FP8_FP8), .product_i(fp8_product),
    .product_valid_i(fp8_product_valid), .rnd_i,
    .valid_o(fp8_valid_o), .acc_o(fp8_acc_o), .status_o(fp8_status_o)
  );

  fusion_mul16_product_core u_bf16_core (
    .mode_i(MODE_BF16_BF16), .lhs_i(bf16_lhs_i), .rhs_i(bf16_rhs_i),
    .int_product_o(bf16_int_unused), .fp_product_o(bf16_product),
    .product_valid_o(bf16_product_valid), .product_count_o(bf16_product_count)
  );
  fusion_mul16_fp32_accum_dw u_bf16_acc (
    .clk, .rst_n, .valid_i(bf16_valid_i), .clear_i(bf16_clear_i),
    .mode_i(MODE_BF16_BF16), .product_i(bf16_product),
    .product_valid_i(bf16_product_valid), .rnd_i,
    .valid_o(bf16_valid_o), .acc_o(bf16_acc_o), .status_o(bf16_status_o)
  );
endmodule

module fusion_mul16_cluster_dw #(
  parameter int INT_ACC_W = 48
) (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic clear_i,
  input  logic [3:0] mode_i,
  input  logic [15:0] lhs_i [0:15],
  input  logic [15:0] rhs_i [0:15],
  input  logic [2:0] rnd_i,
  output logic int_valid_o,
  output logic fp_valid_o,
  output logic signed [INT_ACC_W-1:0] int_acc_o [0:3],
  output logic [31:0] fp_acc_o [0:3],
  output logic [7:0] fp_status_o [0:3]
);
  import fusion_mul16_pkg::*;

  logic signed [32:0] int_product [0:15];
  logic [31:0] fp_product [0:15];
  logic [15:0] product_valid;
  logic [4:0] product_count;
  logic int_mode;
  logic fp_mode;

  assign int_mode = (mode_i <= MODE_I16_I16);
  assign fp_mode = (mode_i >= MODE_FP8_FP8);

  fusion_mul16_product_core u_core (
    .mode_i,
    .lhs_i,
    .rhs_i,
    .int_product_o(int_product),
    .fp_product_o(fp_product),
    .product_valid_o(product_valid),
    .product_count_o(product_count)
  );

  fusion_mul16_int_accum #(.ACC_W(INT_ACC_W)) u_int_acc (
    .clk,
    .rst_n,
    .valid_i(valid_i && int_mode),
    .clear_i,
    .mode_i,
    .product_i(int_product),
    .product_valid_i(product_valid),
    .valid_o(int_valid_o),
    .acc_o(int_acc_o)
  );

  fusion_mul16_fp32_accum_dw u_fp_acc (
    .clk,
    .rst_n,
    .valid_i(valid_i && fp_mode),
    .clear_i,
    .mode_i,
    .product_i(fp_product),
    .product_valid_i(product_valid),
    .rnd_i,
    .valid_o(fp_valid_o),
    .acc_o(fp_acc_o),
    .status_o(fp_status_o)
  );
endmodule

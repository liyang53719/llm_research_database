module fusion_mul16_v2_fp8_widen_bf16_top (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic clear_i,
  input  logic [127:0] lhs_fp8_packed_i,
  input  logic [127:0] rhs_fp8_packed_i,
  output logic valid_o,
  output logic [15:0] acc_o [0:3],
  output logic [7:0] status_o [0:3]
);
  import fusion_mul16_v2_pkg::*;
  logic [127:0] lhs_bf16_packed;
  logic [127:0] rhs_bf16_packed;
  logic [15:0] lhs_bf16 [0:3];
  logic [15:0] rhs_bf16 [0:3];
  logic cfg_ready_unused;
  logic cfg_error_unused;
  logic int_valid_unused;
  logic signed [47:0] int_acc_unused [0:3];
  logic [2:0] mode_unused;

  genvar g;
  generate
    for (g = 0; g < 4; g = g + 1) begin : G_WIDEN
      fp8_to_bf16_exact u_lhs (
        .fp8_i(lhs_fp8_packed_i[g*8 +: 8]),
        .bf16_o(lhs_bf16[g])
      );
      fp8_to_bf16_exact u_rhs (
        .fp8_i(rhs_fp8_packed_i[g*8 +: 8]),
        .bf16_o(rhs_bf16[g])
      );
    end
  endgenerate

  always_comb begin
    lhs_bf16_packed = '0;
    rhs_bf16_packed = '0;
    for (integer i = 0; i < 4; i = i + 1) begin
      lhs_bf16_packed[i*16 +: 16] = lhs_bf16[i];
      rhs_bf16_packed[i*16 +: 16] = rhs_bf16[i];
    end
  end

  fusion_mul16_v2_cluster #(
    .FIXED_MODE(MODE_BF16_BF16),
    .SUPPORT_FP8(1'b0),
    .SUPPORT_BF16(1'b1),
    .SUPPORT_I4_FP8(1'b0),
    .SUPPORT_I4_BF16(1'b0),
    .SUPPORT_I8_BF16(1'b0),
    .SUPPORT_SPECIALS(1'b0)
  ) u_cluster (
    .clk,
    .rst_n,
    .cfg_valid_i(1'b0),
    .cfg_mode_i('0),
    .cfg_rnd_i(3'b000),
    .cfg_ready_o(cfg_ready_unused),
    .cfg_error_o(cfg_error_unused),
    .valid_i,
    .clear_i,
    .lhs_packed_i(lhs_bf16_packed),
    .rhs_packed_i(rhs_bf16_packed),
    .int_valid_o(int_valid_unused),
    .fp_valid_o(valid_o),
    .int_acc_o(int_acc_unused),
    .bf16_acc_o(acc_o),
    .bf16_status_o(status_o),
    .active_mode_o(mode_unused)
  );
endmodule

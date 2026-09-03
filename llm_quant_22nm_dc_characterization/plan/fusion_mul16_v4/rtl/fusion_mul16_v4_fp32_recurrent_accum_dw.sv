module fusion_mul16_v4_fp32_recurrent_accum_dw #(
  parameter int IEEE_COMPLIANCE = 0
) (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic clear_i,
  input  logic [15:0] lane_item_i [0:3][0:3],
  input  logic [2:0] rnd_i,
  output logic valid_o,
  output logic clear_done_o,
  output logic [31:0] acc_fp32_o [0:3],
  output logic [7:0] status_o [0:3]
);
  logic tree_valid;
  logic tree_clear;
  logic [15:0] lane_sum [0:3];
  logic [31:0] lane_sum_fp32 [0:3];
  logic [7:0] tree_status [0:3];
  logic [31:0] acc_next_w [0:3];
  logic [7:0] acc_status [0:3];
  integer lane;

  fusion_mul16_v4_bf16_tree_dw #(.IEEE_COMPLIANCE(IEEE_COMPLIANCE)) u_tree (
    .clk, .rst_n, .valid_i, .clear_i, .lane_item_i, .rnd_i,
    .valid_o(tree_valid), .clear_o(tree_clear),
    .lane_sum_o(lane_sum), .status_o(tree_status)
  );

  genvar g;
  generate
    for (g = 0; g < 4; g = g + 1) begin : G_ACC
      // BF16 -> FP32 widening is exact: exponent is unchanged and fraction
      // bits are zero-extended. No converter macro is required.
      assign lane_sum_fp32[g] = {lane_sum[g], 16'b0};
      DW_fp_add #(23, 8, IEEE_COMPLIANCE) u_acc (
        .a(acc_fp32_o[g]), .b(lane_sum_fp32[g]), .rnd(rnd_i),
        .z(acc_next_w[g]), .status(acc_status[g])
      );
    end
  endgenerate

  // The FP32 recurrence is updated every accepted lane sum. It preserves II=1
  // only if this register-to-DW_fp_add-to-register path closes at 1 GHz.
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_o <= 1'b0;
      clear_done_o <= 1'b0;
      for (lane = 0; lane < 4; lane = lane + 1) begin
        acc_fp32_o[lane] <= '0;
        status_o[lane] <= '0;
      end
    end else begin
      valid_o <= tree_valid;
      clear_done_o <= tree_clear;
      for (lane = 0; lane < 4; lane = lane + 1) begin
        if (tree_clear) begin
          acc_fp32_o[lane] <= '0;
          status_o[lane] <= '0;
        end else if (tree_valid) begin
          acc_fp32_o[lane] <= acc_next_w[lane];
          status_o[lane] <= tree_status[lane] | acc_status[lane];
        end
      end
    end
  end
endmodule

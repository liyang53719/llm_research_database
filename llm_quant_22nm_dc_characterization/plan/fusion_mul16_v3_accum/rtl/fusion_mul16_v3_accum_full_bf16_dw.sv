module fusion_mul16_v3_accum_full_bf16_dw (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic clear_i,
  input  logic [15:0] lane_item_i [0:3][0:3],
  input  logic [2:0] rnd_i,
  output logic valid_o,
  output logic [15:0] acc_bf16_o [0:3],
  output logic [31:0] acc_fp32_view_o [0:3],
  output logic [7:0] status_o [0:3]
);
  logic tree_valid;
  logic tree_clear;
  logic [15:0] lane_sum [0:3];
  logic [7:0] tree_status [0:3];
  logic [15:0] acc_next_w [0:3];
  logic [7:0] acc_status [0:3];
  integer lane;

  fusion_mul16_v3_bf16_tree_dw u_tree (
    .clk, .rst_n, .valid_i, .clear_i, .lane_item_i, .rnd_i,
    .valid_o(tree_valid), .clear_o(tree_clear),
    .lane_sum_o(lane_sum), .status_o(tree_status)
  );

  genvar g;
  generate
    for (g = 0; g < 4; g = g + 1) begin : G_ACC
      DW_fp_add #(7, 8, 0) u_acc (
        .a(acc_bf16_o[g]), .b(lane_sum[g]), .rnd(rnd_i),
        .z(acc_next_w[g]), .status(acc_status[g])
      );
      assign acc_fp32_view_o[g] = {acc_bf16_o[g], 16'b0};
    end
  endgenerate

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_o <= 1'b0;
      for (lane = 0; lane < 4; lane = lane + 1) begin
        acc_bf16_o[lane] <= '0;
        status_o[lane] <= '0;
      end
    end else begin
      valid_o <= tree_valid;
      for (lane = 0; lane < 4; lane = lane + 1) begin
        if (tree_clear) begin
          acc_bf16_o[lane] <= '0;
          status_o[lane] <= '0;
        end else if (tree_valid) begin
          acc_bf16_o[lane] <= acc_next_w[lane];
          status_o[lane] <= tree_status[lane] | acc_status[lane];
        end
      end
    end
  end
endmodule

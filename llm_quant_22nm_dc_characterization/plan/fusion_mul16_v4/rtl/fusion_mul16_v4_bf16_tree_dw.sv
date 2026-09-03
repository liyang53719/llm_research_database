module fusion_mul16_v4_bf16_tree_dw #(
  parameter int IEEE_COMPLIANCE = 0
) (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic clear_i,
  input  logic [15:0] lane_item_i [0:3][0:3],
  input  logic [2:0] rnd_i,
  output logic valid_o,
  output logic clear_o,
  output logic [15:0] lane_sum_o [0:3],
  output logic [7:0] status_o [0:3]
);
  logic [15:0] pair01_w [0:3];
  logic [15:0] pair23_w [0:3];
  logic [15:0] pair01_q [0:3];
  logic [15:0] pair23_q [0:3];
  logic [15:0] lane_sum_w [0:3];
  logic [7:0] pair01_status [0:3];
  logic [7:0] pair23_status [0:3];
  logic [7:0] lane_status [0:3];
  logic [7:0] pair_status_q [0:3];
  logic valid_q1;
  logic clear_q1;
  integer lane;

  genvar g;
  generate
    for (g = 0; g < 4; g = g + 1) begin : G_TREE
      DW_fp_add #(7, 8, IEEE_COMPLIANCE) u_pair01 (
        .a(lane_item_i[g][0]),
        .b(lane_item_i[g][1]),
        .rnd(rnd_i),
        .z(pair01_w[g]),
        .status(pair01_status[g])
      );
      DW_fp_add #(7, 8, IEEE_COMPLIANCE) u_pair23 (
        .a(lane_item_i[g][2]),
        .b(lane_item_i[g][3]),
        .rnd(rnd_i),
        .z(pair23_w[g]),
        .status(pair23_status[g])
      );
      DW_fp_add #(7, 8, IEEE_COMPLIANCE) u_lane_sum (
        .a(pair01_q[g]),
        .b(pair23_q[g]),
        .rnd(rnd_i),
        .z(lane_sum_w[g]),
        .status(lane_status[g])
      );
    end
  endgenerate

  // Two-stage BF16 reduction. clear_i is a control bubble and is aligned
  // with lane_sum_o; clear takes priority over valid in downstream state.
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_q1 <= 1'b0;
      clear_q1 <= 1'b0;
      valid_o <= 1'b0;
      clear_o <= 1'b0;
      for (lane = 0; lane < 4; lane = lane + 1) begin
        pair01_q[lane] <= '0;
        pair23_q[lane] <= '0;
        pair_status_q[lane] <= '0;
        lane_sum_o[lane] <= '0;
        status_o[lane] <= '0;
      end
    end else begin
      valid_q1 <= valid_i;
      clear_q1 <= clear_i;
      valid_o <= valid_q1;
      clear_o <= clear_q1;
      for (lane = 0; lane < 4; lane = lane + 1) begin
        pair01_q[lane] <= pair01_w[lane];
        pair23_q[lane] <= pair23_w[lane];
        pair_status_q[lane] <= pair01_status[lane] | pair23_status[lane];
        lane_sum_o[lane] <= lane_sum_w[lane];
        status_o[lane] <= pair_status_q[lane] | lane_status[lane];
      end
    end
  end
endmodule

module fusion_mul16_fp32_accum_dw (
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
  import fusion_mul16_pkg::*;

  logic [31:0] lane_p [0:3][0:3];
  logic [31:0] pair01 [0:3];
  logic [31:0] pair23 [0:3];
  logic [31:0] lane_sum [0:3];
  logic [31:0] acc_next [0:3];
  logic [7:0] pair01_status [0:3];
  logic [7:0] pair23_status [0:3];
  logic [7:0] lane_status [0:3];
  logic [7:0] acc_status [0:3];

  logic [31:0] pair01_q [0:3];
  logic [31:0] pair23_q [0:3];
  logic [31:0] lane_sum_q [0:3];
  logic [7:0] status_stage1_q [0:3];
  logic [7:0] status_stage2_q [0:3];
  logic valid_q1;
  logic valid_q2;
  logic clear_q1;
  logic clear_q2;

  integer index;
  integer items_per_lane;

  always_comb begin
    unique case (mode_i)
      MODE_FP8_FP8, MODE_I4_FP8: items_per_lane = 4;
      MODE_I8_FP8, MODE_I4_BF16: items_per_lane = 2;
      MODE_BF16_BF16, MODE_I8_BF16: items_per_lane = 1;
      default: items_per_lane = 0;
    endcase

    for (integer lane = 0; lane < 4; lane = lane + 1)
      for (integer item = 0; item < 4; item = item + 1) begin
        if (items_per_lane == 4)
          index = (lane << 2) + item;
        else if (items_per_lane == 2)
          index = (lane << 1) + item;
        else
          index = lane;
        if ((item < items_per_lane) && (index < 16) && product_valid_i[index])
          lane_p[lane][item] = product_i[index];
        else
          lane_p[lane][item] = 32'b0;
      end
  end

  genvar g;
  generate
    for (g = 0; g < 4; g = g + 1) begin : G_FP_LANE
      DW_fp_add #(23, 8, 0) u_pair01 (
        .a(lane_p[g][0]), .b(lane_p[g][1]), .rnd(rnd_i),
        .z(pair01[g]), .status(pair01_status[g])
      );
      DW_fp_add #(23, 8, 0) u_pair23 (
        .a(lane_p[g][2]), .b(lane_p[g][3]), .rnd(rnd_i),
        .z(pair23[g]), .status(pair23_status[g])
      );
      DW_fp_add #(23, 8, 0) u_lane_sum (
        .a(pair01_q[g]), .b(pair23_q[g]), .rnd(rnd_i),
        .z(lane_sum[g]), .status(lane_status[g])
      );
      DW_fp_add #(23, 8, 0) u_acc (
        .a(acc_o[g]), .b(lane_sum_q[g]), .rnd(rnd_i),
        .z(acc_next[g]), .status(acc_status[g])
      );
    end
  endgenerate

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_q1 <= 1'b0;
      valid_q2 <= 1'b0;
      valid_o <= 1'b0;
      clear_q1 <= 1'b0;
      clear_q2 <= 1'b0;
      for (integer lane = 0; lane < 4; lane = lane + 1) begin
        pair01_q[lane] <= '0;
        pair23_q[lane] <= '0;
        lane_sum_q[lane] <= '0;
        status_stage1_q[lane] <= '0;
        status_stage2_q[lane] <= '0;
        acc_o[lane] <= '0;
        status_o[lane] <= '0;
      end
    end else begin
      valid_q1 <= valid_i;
      valid_q2 <= valid_q1;
      valid_o <= valid_q2;
      clear_q1 <= clear_i;
      clear_q2 <= clear_q1;
      for (integer lane = 0; lane < 4; lane = lane + 1) begin
        pair01_q[lane] <= pair01[lane];
        pair23_q[lane] <= pair23[lane];
        lane_sum_q[lane] <= lane_sum[lane];
        status_stage1_q[lane] <= pair01_status[lane] | pair23_status[lane];
        status_stage2_q[lane] <= status_stage1_q[lane] | lane_status[lane];
        if (clear_q2) begin
          acc_o[lane] <= '0;
          status_o[lane] <= '0;
        end else if (valid_q2) begin
          acc_o[lane] <= acc_next[lane];
          status_o[lane] <= status_stage2_q[lane] | acc_status[lane];
        end
      end
    end
  end
endmodule

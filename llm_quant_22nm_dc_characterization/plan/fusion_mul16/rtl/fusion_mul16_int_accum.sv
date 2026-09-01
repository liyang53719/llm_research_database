module fusion_mul16_int_accum #(
  parameter int ACC_W = 48
) (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic clear_i,
  input  logic [3:0] mode_i,
  input  logic signed [32:0] product_i [0:15],
  input  logic [15:0] product_valid_i,
  output logic valid_o,
  output logic signed [ACC_W-1:0] acc_o [0:3]
);
  import fusion_mul16_pkg::*;

  logic signed [ACC_W-1:0] lane_sum [0:3];
  integer index;
  integer items_per_lane;

  always_comb begin
    unique case (mode_i)
      MODE_I4_I4: items_per_lane = 4;
      MODE_I4_I8: items_per_lane = 2;
      MODE_I8_I8: items_per_lane = 1;
      MODE_I16_I16: items_per_lane = 1;
      default: items_per_lane = 0;
    endcase

    for (integer lane = 0; lane < 4; lane = lane + 1) begin
      lane_sum[lane] = '0;
      for (integer item = 0; item < 4; item = item + 1) begin
        if (items_per_lane == 4)
          index = (lane << 2) + item;
        else if (items_per_lane == 2)
          index = (lane << 1) + item;
        else
          index = lane;
        if ((item < items_per_lane) && (index < 16) && product_valid_i[index])
          lane_sum[lane] = lane_sum[lane] + product_i[index];
      end
    end
    if (mode_i == MODE_I16_I16) begin
      lane_sum[1] = '0;
      lane_sum[2] = '0;
      lane_sum[3] = '0;
    end
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_o <= 1'b0;
      for (integer lane = 0; lane < 4; lane = lane + 1)
        acc_o[lane] <= '0;
    end else begin
      valid_o <= valid_i;
      if (clear_i) begin
        for (integer lane = 0; lane < 4; lane = lane + 1)
          acc_o[lane] <= '0;
      end else if (valid_i) begin
        for (integer lane = 0; lane < 4; lane = lane + 1)
          acc_o[lane] <= acc_o[lane] + lane_sum[lane];
      end
    end
  end
endmodule

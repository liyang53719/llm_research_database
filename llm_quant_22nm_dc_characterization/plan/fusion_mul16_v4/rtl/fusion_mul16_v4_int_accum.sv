module fusion_mul16_v4_int_accum #(
  parameter int ACC_W = 48
) (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic clear_i,
  input  logic signed [17:0] lane_sum_i [0:3],
  output logic valid_o,
  output logic clear_done_o,
  output logic signed [ACC_W-1:0] acc_o [0:3]
);
  integer lane;
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_o <= 1'b0;
      clear_done_o <= 1'b0;
      for (lane = 0; lane < 4; lane = lane + 1)
        acc_o[lane] <= '0;
    end else begin
      valid_o <= valid_i;
      clear_done_o <= clear_i;
      if (clear_i) begin
        for (lane = 0; lane < 4; lane = lane + 1)
          acc_o[lane] <= '0;
      end else if (valid_i) begin
        for (lane = 0; lane < 4; lane = lane + 1)
          acc_o[lane] <= acc_o[lane]
                       + {{(ACC_W-18){lane_sum_i[lane][17]}}, lane_sum_i[lane]};
      end
    end
  end
endmodule

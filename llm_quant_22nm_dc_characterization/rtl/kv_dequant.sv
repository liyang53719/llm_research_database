module kv_dequant #(
  parameter int IN_W = 4,
  parameter int OUT_W = 8,
  parameter int LANES = 16,
  parameter int SCALE_W = 8,
  parameter int FRAC_BITS = 4,
  parameter bit ASYMMETRIC = 1'b0,
  parameter bit BYPASS = 1'b0
) (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic signed [LANES*IN_W-1:0] packed_i,
  input  logic signed [SCALE_W-1:0] scale_i,
  input  logic signed [IN_W-1:0] zero_point_i,
  output logic valid_o,
  output logic signed [LANES*OUT_W-1:0] unpacked_o
);
  integer i;
  logic signed [IN_W:0] centered;
  logic signed [IN_W+SCALE_W:0] scaled;
  logic signed [OUT_W-1:0] lane_out;

  always_comb begin
    unpacked_o = '0;
    centered = '0;
    scaled = '0;
    lane_out = '0;
    for (i = 0; i < LANES; i = i + 1) begin
      if (BYPASS)
        lane_out = {{(OUT_W-IN_W){packed_i[i*IN_W+IN_W-1]}}, packed_i[i*IN_W +: IN_W]};
      else begin
        if (ASYMMETRIC)
          centered = $signed(packed_i[i*IN_W +: IN_W]) - $signed(zero_point_i);
        else
          centered = $signed(packed_i[i*IN_W +: IN_W]);
        scaled = centered * scale_i;
        lane_out = scaled >>> FRAC_BITS;
      end
      unpacked_o[i*OUT_W +: OUT_W] = lane_out;
    end
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      valid_o <= 1'b0;
    else
      valid_o <= valid_i;
  end
endmodule

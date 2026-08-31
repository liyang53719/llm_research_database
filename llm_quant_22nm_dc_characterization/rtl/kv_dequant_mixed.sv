module kv_dequant_mixed #(
  parameter int LANES = 16,
  parameter int OUT_W = 8
) (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic [1:0] mode_i,
  input  logic signed [LANES*8-1:0] lane_slots_i,
  input  logic signed [7:0] scale_i,
  input  logic signed [7:0] zero_point_i,
  output logic valid_o,
  output logic signed [LANES*OUT_W-1:0] unpacked_o
);
  integer i;
  logic signed [8:0] centered;
  logic signed [16:0] scaled;
  logic signed [7:0] selected;
  logic signed [7:0] mask;

  always_comb begin
    unpacked_o = '0;
    centered = '0;
    scaled = '0;
    selected = '0;
    mask = '0;
    for (i = 0; i < LANES; i = i + 1) begin
      unique case (mode_i)
        2'b00: begin
          mask = 8'h03;
          selected = {{6{lane_slots_i[i*8+1]}}, lane_slots_i[i*8 +: 2]};
        end
        2'b01: begin
          mask = 8'h0F;
          selected = {{4{lane_slots_i[i*8+3]}}, lane_slots_i[i*8 +: 4]};
        end
        default: begin
          mask = 8'hFF;
          selected = lane_slots_i[i*8 +: 8] & mask;
        end
      endcase
      centered = selected - zero_point_i;
      scaled = centered * scale_i;
      unpacked_o[i*OUT_W +: OUT_W] = scaled >>> 4;
    end
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      valid_o <= 1'b0;
    else
      valid_o <= valid_i;
  end
endmodule

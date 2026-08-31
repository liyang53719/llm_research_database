module requant_int #(
  parameter int IN_W = 32,
  parameter int OUT_W = 8,
  parameter int SCALE_W = 16,
  parameter int SHIFT = 8
) (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic signed [IN_W-1:0] value_i,
  input  logic signed [SCALE_W-1:0] scale_i,
  input  logic signed [OUT_W-1:0] zero_point_i,
  output logic valid_o,
  output logic signed [OUT_W-1:0] value_o
);
  localparam int MUL_W = IN_W + SCALE_W;
  logic signed [MUL_W-1:0] scaled;
  logic signed [MUL_W-1:0] rounded;
  logic signed [MUL_W-1:0] shifted;
  logic signed [MUL_W-1:0] with_zp;
  logic signed [MUL_W-1:0] max_v;
  logic signed [MUL_W-1:0] min_v;

  always_comb begin
    scaled  = value_i * scale_i;
    rounded = scaled + ({{(MUL_W-1){1'b0}}, 1'b1} <<< (SHIFT-1));
    shifted = rounded >>> SHIFT;
    with_zp = shifted + zero_point_i;
    max_v   = (1 <<< (OUT_W-1)) - 1;
    min_v   = - (1 <<< (OUT_W-1));
    if (with_zp > max_v)
      value_o = max_v[OUT_W-1:0];
    else if (with_zp < min_v)
      value_o = min_v[OUT_W-1:0];
    else
      value_o = with_zp[OUT_W-1:0];
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      valid_o <= 1'b0;
    else
      valid_o <= valid_i;
  end
endmodule

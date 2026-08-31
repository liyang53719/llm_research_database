module mixed_mode_pe #(
  parameter int ACC_W = 40,
  parameter bit WITH_REQUANT = 1'b0
) (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic clear_i,
  input  logic [1:0] mode_i,
  input  logic [31:0] w_word_i,
  input  logic [31:0] a_word_i,
  input  logic signed [15:0] scale_i,
  output logic valid_o,
  output logic signed [ACC_W-1:0] acc_o,
  output logic signed [15:0] requant_o
);
  integer i;
  logic signed [ACC_W-1:0] sum_w4a4;
  logic signed [ACC_W-1:0] sum_w4a8;
  logic signed [ACC_W-1:0] sum_w8a8;
  logic signed [ACC_W-1:0] selected_sum;
  logic signed [ACC_W+15:0] scaled;

  always_comb begin
    sum_w4a4 = '0;
    sum_w4a8 = '0;
    sum_w8a8 = '0;
    for (i = 0; i < 8; i = i + 1)
      sum_w4a4 = sum_w4a4
        + $signed(w_word_i[i*4 +: 4]) * $signed(a_word_i[i*4 +: 4]);
    for (i = 0; i < 4; i = i + 1) begin
      sum_w4a8 = sum_w4a8
        + $signed(w_word_i[i*4 +: 4]) * $signed(a_word_i[i*8 +: 8]);
      sum_w8a8 = sum_w8a8
        + $signed(w_word_i[i*8 +: 8]) * $signed(a_word_i[i*8 +: 8]);
    end
    unique case (mode_i)
      2'b00: selected_sum = sum_w4a4;
      2'b01: selected_sum = sum_w4a8;
      default: selected_sum = sum_w8a8;
    endcase
    scaled = acc_o * scale_i;
    if (WITH_REQUANT)
      requant_o = scaled >>> 8;
    else
      requant_o = acc_o[15:0];
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      acc_o   <= '0;
      valid_o <= 1'b0;
    end else begin
      valid_o <= valid_i;
      if (clear_i)
        acc_o <= '0;
      else if (valid_i)
        acc_o <= acc_o + selected_sum;
    end
  end
endmodule

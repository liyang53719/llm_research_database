module fp8_to_bf16_exact (
  input  logic [7:0] fp8_i,
  output logic [15:0] bf16_o
);
  logic sign;
  logic [3:0] exponent;
  logic [2:0] fraction;
  logic [7:0] bf16_exponent;
  logic [6:0] bf16_fraction;

  always_comb begin
    sign = fp8_i[7];
    exponent = fp8_i[6:3];
    fraction = fp8_i[2:0];
    bf16_exponent = '0;
    bf16_fraction = '0;

    if ((exponent == 0) && (fraction == 0)) begin
      bf16_o = {sign, 15'b0};
    end else if ((exponent == 4'hf) && (fraction == 3'h7)) begin
      bf16_o = {sign, 8'hff, 7'h40};
    end else if (exponent != 0) begin
      bf16_exponent = {4'b0, exponent} + 8'd120;
      bf16_fraction = {fraction, 4'b0};
      bf16_o = {sign, bf16_exponent, bf16_fraction};
    end else begin
      case (fraction)
        3'd1: bf16_o = {sign, 8'd118, 7'h00};
        3'd2: bf16_o = {sign, 8'd119, 7'h00};
        3'd3: bf16_o = {sign, 8'd119, 7'h40};
        3'd4: bf16_o = {sign, 8'd120, 7'h00};
        3'd5: bf16_o = {sign, 8'd120, 7'h20};
        3'd6: bf16_o = {sign, 8'd120, 7'h40};
        default: bf16_o = {sign, 8'd120, 7'h60};
      endcase
    end
  end
endmodule

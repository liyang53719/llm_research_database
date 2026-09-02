module raw16_to_bf16_rne #(
  parameter bit SUPPORT_SPECIALS = 1'b0
) (
  input  logic sign_i,
  input  logic [15:0] raw_i,
  input  logic signed [10:0] scale_exp_i,
  input  logic zero_i,
  input  logic inf_i,
  input  logic nan_i,
  output logic [15:0] bf16_o
);
  integer bit_index;
  integer msb_index;
  integer shift_amount;
  integer unbiased_exp;
  integer biased_exp;
  logic found;
  logic [7:0] significand8;
  logic [8:0] rounded9;
  logic guard_bit;
  logic sticky_bit;
  logic round_up;

  always_comb begin
    msb_index = 0;
    found = 1'b0;
    for (bit_index = 15; bit_index >= 0; bit_index = bit_index - 1) begin
      if (!found && raw_i[bit_index]) begin
        msb_index = bit_index;
        found = 1'b1;
      end
    end

    shift_amount = 0;
    unbiased_exp = 0;
    biased_exp = 0;
    significand8 = '0;
    rounded9 = '0;
    guard_bit = 1'b0;
    sticky_bit = 1'b0;
    round_up = 1'b0;
    bf16_o = {sign_i, 15'b0};

    if (SUPPORT_SPECIALS && nan_i) begin
      bf16_o = {sign_i, 8'hff, 7'h40};
    end else if (SUPPORT_SPECIALS && inf_i) begin
      bf16_o = {sign_i, 8'hff, 7'h00};
    end else if (zero_i || !found) begin
      bf16_o = {sign_i, 15'b0};
    end else begin
      unbiased_exp = $signed(scale_exp_i) + msb_index;
      if (unbiased_exp > 127) begin
        bf16_o = {sign_i, 8'hff, 7'h00};
      end else if (unbiased_exp < -126) begin
        // Explicit FTZ contract. It matches the low-area inference path.
        bf16_o = {sign_i, 15'b0};
      end else begin
        if (msb_index > 7) begin
          shift_amount = msb_index - 7;
          significand8 = raw_i >> shift_amount;
          guard_bit = raw_i[shift_amount-1];
          sticky_bit = 1'b0;
          for (bit_index = 0; bit_index < 15; bit_index = bit_index + 1)
            if (bit_index < (shift_amount-1))
              sticky_bit = sticky_bit | raw_i[bit_index];
          round_up = guard_bit && (sticky_bit || significand8[0]);
          rounded9 = {1'b0, significand8} + round_up;
          if (rounded9[8]) begin
            significand8 = rounded9[8:1];
            unbiased_exp = unbiased_exp + 1;
          end else begin
            significand8 = rounded9[7:0];
          end
        end else begin
          significand8 = raw_i << (7-msb_index);
        end

        if (unbiased_exp > 127) begin
          bf16_o = {sign_i, 8'hff, 7'h00};
        end else begin
          biased_exp = unbiased_exp + 127;
          bf16_o = {sign_i, biased_exp[7:0], significand8[6:0]};
        end
      end
    end
  end
endmodule

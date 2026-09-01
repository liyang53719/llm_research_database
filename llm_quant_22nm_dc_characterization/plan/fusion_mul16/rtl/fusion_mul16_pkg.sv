package fusion_mul16_pkg;
  typedef enum logic [3:0] {
    MODE_I4_I4       = 4'd0,
    MODE_I4_I8       = 4'd1,
    MODE_I8_I8       = 4'd2,
    MODE_I16_I16     = 4'd3,
    MODE_FP8_FP8     = 4'd4,
    MODE_BF16_BF16   = 4'd5,
    MODE_I4_FP8      = 4'd6,
    MODE_I8_FP8      = 4'd7,
    MODE_I4_BF16     = 4'd8,
    MODE_I8_BF16     = 4'd9
  } fusion_mode_e;

  function automatic logic [3:0] abs_i4(input logic [3:0] raw);
    logic signed [4:0] value;
    begin
      value = {raw[3], raw};
      abs_i4 = value[4] ? -value : value;
    end
  endfunction

  function automatic logic [7:0] abs_i8(input logic [7:0] raw);
    logic signed [8:0] value;
    begin
      value = {raw[7], raw};
      abs_i8 = value[8] ? -value : value;
    end
  endfunction

  function automatic logic [15:0] abs_i16(input logic [15:0] raw);
    logic signed [16:0] value;
    begin
      value = {raw[15], raw};
      abs_i16 = value[16] ? -value : value;
    end
  endfunction

  function automatic logic signed [32:0] apply_sign33(
    input logic [31:0] magnitude,
    input logic sign
  );
    logic signed [32:0] positive;
    begin
      positive = $signed({1'b0, magnitude});
      apply_sign33 = sign ? -positive : positive;
    end
  endfunction

  function automatic logic [31:0] raw_binary_product_to_fp32(
    input logic sign,
    input logic [31:0] raw_product,
    input logic signed [11:0] scale_exp,
    input logic is_zero,
    input logic is_inf,
    input logic is_nan
  );
    integer n;
    integer msb_index;
    integer subnormal_shift;
    integer right_shift;
    logic signed [12:0] unbiased_exp;
    logic [7:0] biased_exp;
    logic [63:0] shifted;
    logic [22:0] fraction;
    logic [63:0] truncated;
    logic guard_bit;
    logic sticky_bit;
    logic round_up;
    begin
      msb_index = 0;
      subnormal_shift = 0;
      unbiased_exp = '0;
      biased_exp = '0;
      shifted = '0;
      truncated = '0;
      fraction = '0;
      right_shift = 0;
      guard_bit = 1'b0;
      sticky_bit = 1'b0;
      round_up = 1'b0;
      for (n = 0; n < 32; n = n + 1)
        if (raw_product[n])
          msb_index = n;

      unbiased_exp = scale_exp + msb_index;
      if (is_nan)
        raw_binary_product_to_fp32 = 32'h7fc00000;
      else if (is_inf)
        raw_binary_product_to_fp32 = {sign, 8'hff, 23'b0};
      else if (is_zero || (raw_product == 0) || (unbiased_exp < -150))
        raw_binary_product_to_fp32 = {sign, 31'b0};
      else if (unbiased_exp > 127)
        raw_binary_product_to_fp32 = {sign, 8'hff, 23'b0};
      else if (unbiased_exp >= -126) begin
        biased_exp = unbiased_exp + 127;
        shifted = {32'b0, raw_product} << (23 - msb_index);
        fraction = shifted[22:0];
        raw_binary_product_to_fp32 = {sign, biased_exp, fraction};
      end else begin
        subnormal_shift = scale_exp + 149;
        if (subnormal_shift >= 0)
          shifted = {32'b0, raw_product} << subnormal_shift;
        else begin
          right_shift = -subnormal_shift;
          truncated = {32'b0, raw_product} >> right_shift;
          guard_bit = raw_product[right_shift-1];
          for (n = 0; n < 32; n = n + 1)
            if (n < right_shift-1)
              sticky_bit = sticky_bit | raw_product[n];
          round_up = guard_bit && (sticky_bit || truncated[0]);
          shifted = truncated + round_up;
        end
        if (shifted[23])
          raw_binary_product_to_fp32 = {sign, 8'h01, 23'b0};
        else
          raw_binary_product_to_fp32 = {sign, 8'h00, shifted[22:0]};
      end
    end
  endfunction
endpackage

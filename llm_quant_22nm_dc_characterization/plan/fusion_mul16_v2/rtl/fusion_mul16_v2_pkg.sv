package fusion_mul16_v2_pkg;
  typedef enum logic [2:0] {
    MODE_I4_I8      = 3'd0,
    MODE_I8_I8      = 3'd1,
    MODE_FP8_FP8    = 3'd2,
    MODE_BF16_BF16  = 3'd3,
    MODE_I4_FP8     = 3'd4,
    MODE_I4_BF16    = 3'd5,
    MODE_I8_BF16    = 3'd6
  } fusion_v2_mode_e;

  typedef struct packed {
    logic sign;
    logic [7:0] significand;
    logic signed [10:0] scale_exp;
    logic is_zero;
    logic is_inf;
    logic is_nan;
  } fp_operand_t;

  function automatic logic [6:0] mode_to_onehot(input logic [2:0] mode);
    logic [6:0] value;
    begin
      value = '0;
      case (mode)
        MODE_I4_I8:     value[0] = 1'b1;
        MODE_I8_I8:     value[1] = 1'b1;
        MODE_FP8_FP8:   value[2] = 1'b1;
        MODE_BF16_BF16: value[3] = 1'b1;
        MODE_I4_FP8:    value[4] = 1'b1;
        MODE_I4_BF16:   value[5] = 1'b1;
        MODE_I8_BF16:   value[6] = 1'b1;
        default:        value = '0;
      endcase
      mode_to_onehot = value;
    end
  endfunction

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

  function automatic fp_operand_t decode_fp8(input logic [7:0] raw);
    fp_operand_t value;
    logic [3:0] exponent;
    logic [2:0] fraction;
    begin
      value = '0;
      exponent = raw[6:3];
      fraction = raw[2:0];
      value.sign = raw[7];
      value.is_zero = (exponent == 0) && (fraction == 0);
      value.is_nan = (exponent == 4'hf) && (fraction == 3'h7);
      value.is_inf = 1'b0;
      if (exponent == 0) begin
        value.significand = {5'b0, fraction};
        value.scale_exp = -11'sd9;
      end else begin
        value.significand = {4'b0, 1'b1, fraction};
        value.scale_exp = $signed({1'b0, exponent}) - 11'sd10;
      end
      decode_fp8 = value;
    end
  endfunction

  function automatic fp_operand_t decode_bf16(input logic [15:0] raw);
    fp_operand_t value;
    logic [7:0] exponent;
    logic [6:0] fraction;
    begin
      value = '0;
      exponent = raw[14:7];
      fraction = raw[6:0];
      value.sign = raw[15];
      value.is_zero = (exponent == 0) && (fraction == 0);
      value.is_inf = (exponent == 8'hff) && (fraction == 0);
      value.is_nan = (exponent == 8'hff) && (fraction != 0);
      if (exponent == 0) begin
        value.significand = {1'b0, fraction};
        value.scale_exp = -11'sd133;
      end else begin
        value.significand = {1'b1, fraction};
        value.scale_exp = $signed({1'b0, exponent}) - 11'sd134;
      end
      decode_bf16 = value;
    end
  endfunction

  function automatic logic signed [16:0] apply_sign17(
    input logic [15:0] magnitude,
    input logic sign
  );
    logic signed [16:0] positive;
    begin
      positive = $signed({1'b0, magnitude});
      apply_sign17 = sign ? -positive : positive;
    end
  endfunction
endpackage

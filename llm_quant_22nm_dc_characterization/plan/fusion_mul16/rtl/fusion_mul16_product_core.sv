module fusion_mul16_product_core (
  input  logic [3:0] mode_i,
  input  logic [15:0] lhs_i [0:15],
  input  logic [15:0] rhs_i [0:15],
  output logic signed [32:0] int_product_o [0:15],
  output logic [31:0] fp_product_o [0:15],
  output logic [15:0] product_valid_o,
  output logic [4:0] product_count_o
);
  import fusion_mul16_pkg::*;

  logic [3:0] brick_a [0:15];
  logic [3:0] brick_b [0:15];
  logic [7:0] brick_p [0:15];

  logic [3:0] lhs_i4_mag [0:15];
  logic [3:0] rhs_i4_mag [0:15];
  logic [7:0] lhs_i8_mag [0:15];
  logic [7:0] rhs_i8_mag [0:15];
  logic [15:0] lhs_i16_mag [0:15];
  logic [15:0] rhs_i16_mag [0:15];

  logic [3:0] lhs_fp8_sig [0:15];
  logic [3:0] rhs_fp8_sig [0:15];
  logic signed [11:0] lhs_fp8_scale [0:15];
  logic signed [11:0] rhs_fp8_scale [0:15];
  logic lhs_fp8_sign [0:15];
  logic rhs_fp8_sign [0:15];
  logic lhs_fp8_zero [0:15];
  logic rhs_fp8_zero [0:15];
  logic lhs_fp8_nan [0:15];
  logic rhs_fp8_nan [0:15];

  logic [7:0] lhs_bf16_sig [0:15];
  logic [7:0] rhs_bf16_sig [0:15];
  logic signed [11:0] lhs_bf16_scale [0:15];
  logic signed [11:0] rhs_bf16_scale [0:15];
  logic lhs_bf16_sign [0:15];
  logic rhs_bf16_sign [0:15];
  logic lhs_bf16_zero [0:15];
  logic rhs_bf16_zero [0:15];
  logic lhs_bf16_inf [0:15];
  logic rhs_bf16_inf [0:15];
  logic lhs_bf16_nan [0:15];
  logic rhs_bf16_nan [0:15];

  integer idx_decode;
  integer idx_output;
  logic [31:0] magnitude;
  logic product_sign;
  logic [3:0] exp4;
  logic [2:0] mant3;
  logic [7:0] exp8;
  logic [6:0] mant7;

  genvar g;
  generate
    for (g = 0; g < 16; g = g + 1) begin : G_BRICK
      mul4x4_brick u_brick (
        .a_i(brick_a[g]),
        .b_i(brick_b[g]),
        .p_o(brick_p[g])
      );
    end
  endgenerate

  always_comb begin
    for (integer i = 0; i < 16; i = i + 1) begin
      lhs_i4_mag[i] = abs_i4(lhs_i[i][3:0]);
      rhs_i4_mag[i] = abs_i4(rhs_i[i][3:0]);
      lhs_i8_mag[i] = abs_i8(lhs_i[i][7:0]);
      rhs_i8_mag[i] = abs_i8(rhs_i[i][7:0]);
      lhs_i16_mag[i] = abs_i16(lhs_i[i]);
      rhs_i16_mag[i] = abs_i16(rhs_i[i]);

      exp4 = lhs_i[i][6:3];
      mant3 = lhs_i[i][2:0];
      lhs_fp8_sign[i] = lhs_i[i][7];
      lhs_fp8_zero[i] = (exp4 == 0) && (mant3 == 0);
      lhs_fp8_nan[i] = (exp4 == 4'hf) && (mant3 == 3'h7);
      if (exp4 == 0) begin
        lhs_fp8_sig[i] = {1'b0, mant3};
        lhs_fp8_scale[i] = -9;
      end else begin
        lhs_fp8_sig[i] = {1'b1, mant3};
        lhs_fp8_scale[i] = $signed({1'b0, exp4}) - 10;
      end

      exp4 = rhs_i[i][6:3];
      mant3 = rhs_i[i][2:0];
      rhs_fp8_sign[i] = rhs_i[i][7];
      rhs_fp8_zero[i] = (exp4 == 0) && (mant3 == 0);
      rhs_fp8_nan[i] = (exp4 == 4'hf) && (mant3 == 3'h7);
      if (exp4 == 0) begin
        rhs_fp8_sig[i] = {1'b0, mant3};
        rhs_fp8_scale[i] = -9;
      end else begin
        rhs_fp8_sig[i] = {1'b1, mant3};
        rhs_fp8_scale[i] = $signed({1'b0, exp4}) - 10;
      end

      exp8 = lhs_i[i][14:7];
      mant7 = lhs_i[i][6:0];
      lhs_bf16_sign[i] = lhs_i[i][15];
      lhs_bf16_zero[i] = (exp8 == 0) && (mant7 == 0);
      lhs_bf16_inf[i] = (exp8 == 8'hff) && (mant7 == 0);
      lhs_bf16_nan[i] = (exp8 == 8'hff) && (mant7 != 0);
      if (exp8 == 0) begin
        lhs_bf16_sig[i] = {1'b0, mant7};
        lhs_bf16_scale[i] = -133;
      end else begin
        lhs_bf16_sig[i] = {1'b1, mant7};
        lhs_bf16_scale[i] = $signed({1'b0, exp8}) - 134;
      end

      exp8 = rhs_i[i][14:7];
      mant7 = rhs_i[i][6:0];
      rhs_bf16_sign[i] = rhs_i[i][15];
      rhs_bf16_zero[i] = (exp8 == 0) && (mant7 == 0);
      rhs_bf16_inf[i] = (exp8 == 8'hff) && (mant7 == 0);
      rhs_bf16_nan[i] = (exp8 == 8'hff) && (mant7 != 0);
      if (exp8 == 0) begin
        rhs_bf16_sig[i] = {1'b0, mant7};
        rhs_bf16_scale[i] = -133;
      end else begin
        rhs_bf16_sig[i] = {1'b1, mant7};
        rhs_bf16_scale[i] = $signed({1'b0, exp8}) - 134;
      end
    end
  end

  always_comb begin
    for (integer i = 0; i < 16; i = i + 1) begin
      brick_a[i] = '0;
      brick_b[i] = '0;
    end

    unique case (mode_i)
      MODE_I4_I4: begin
        for (integer i = 0; i < 16; i = i + 1) begin
          brick_a[i] = lhs_i4_mag[i];
          brick_b[i] = rhs_i4_mag[i];
        end
      end
      MODE_I4_I8: begin
        for (integer i = 0; i < 8; i = i + 1) begin
          idx_decode = i << 1;
          brick_a[idx_decode] = lhs_i4_mag[i];
          brick_a[idx_decode+1] = lhs_i4_mag[i];
          brick_b[idx_decode] = rhs_i8_mag[i][3:0];
          brick_b[idx_decode+1] = rhs_i8_mag[i][7:4];
        end
      end
      MODE_I8_I8: begin
        for (integer i = 0; i < 4; i = i + 1) begin
          idx_decode = i << 2;
          brick_a[idx_decode] = lhs_i8_mag[i][3:0];
          brick_a[idx_decode+1] = lhs_i8_mag[i][3:0];
          brick_a[idx_decode+2] = lhs_i8_mag[i][7:4];
          brick_a[idx_decode+3] = lhs_i8_mag[i][7:4];
          brick_b[idx_decode] = rhs_i8_mag[i][3:0];
          brick_b[idx_decode+1] = rhs_i8_mag[i][7:4];
          brick_b[idx_decode+2] = rhs_i8_mag[i][3:0];
          brick_b[idx_decode+3] = rhs_i8_mag[i][7:4];
        end
      end
      MODE_I16_I16: begin
        for (integer i = 0; i < 4; i = i + 1)
          for (integer j = 0; j < 4; j = j + 1) begin
            idx_decode = (i << 2) + j;
            brick_a[idx_decode] = lhs_i16_mag[0][i*4 +: 4];
            brick_b[idx_decode] = rhs_i16_mag[0][j*4 +: 4];
          end
      end
      MODE_FP8_FP8: begin
        for (integer i = 0; i < 16; i = i + 1) begin
          brick_a[i] = lhs_fp8_sig[i];
          brick_b[i] = rhs_fp8_sig[i];
        end
      end
      MODE_BF16_BF16: begin
        for (integer i = 0; i < 4; i = i + 1) begin
          idx_decode = i << 2;
          brick_a[idx_decode] = lhs_bf16_sig[i][3:0];
          brick_a[idx_decode+1] = lhs_bf16_sig[i][3:0];
          brick_a[idx_decode+2] = lhs_bf16_sig[i][7:4];
          brick_a[idx_decode+3] = lhs_bf16_sig[i][7:4];
          brick_b[idx_decode] = rhs_bf16_sig[i][3:0];
          brick_b[idx_decode+1] = rhs_bf16_sig[i][7:4];
          brick_b[idx_decode+2] = rhs_bf16_sig[i][3:0];
          brick_b[idx_decode+3] = rhs_bf16_sig[i][7:4];
        end
      end
      MODE_I4_FP8: begin
        for (integer i = 0; i < 16; i = i + 1) begin
          brick_a[i] = lhs_i4_mag[i];
          brick_b[i] = rhs_fp8_sig[i];
        end
      end
      MODE_I8_FP8: begin
        for (integer i = 0; i < 8; i = i + 1) begin
          idx_decode = i << 1;
          brick_a[idx_decode] = lhs_i8_mag[i][3:0];
          brick_a[idx_decode+1] = lhs_i8_mag[i][7:4];
          brick_b[idx_decode] = rhs_fp8_sig[i];
          brick_b[idx_decode+1] = rhs_fp8_sig[i];
        end
      end
      MODE_I4_BF16: begin
        for (integer i = 0; i < 8; i = i + 1) begin
          idx_decode = i << 1;
          brick_a[idx_decode] = lhs_i4_mag[i];
          brick_a[idx_decode+1] = lhs_i4_mag[i];
          brick_b[idx_decode] = rhs_bf16_sig[i][3:0];
          brick_b[idx_decode+1] = rhs_bf16_sig[i][7:4];
        end
      end
      MODE_I8_BF16: begin
        for (integer i = 0; i < 4; i = i + 1) begin
          idx_decode = i << 2;
          brick_a[idx_decode] = lhs_i8_mag[i][3:0];
          brick_a[idx_decode+1] = lhs_i8_mag[i][3:0];
          brick_a[idx_decode+2] = lhs_i8_mag[i][7:4];
          brick_a[idx_decode+3] = lhs_i8_mag[i][7:4];
          brick_b[idx_decode] = rhs_bf16_sig[i][3:0];
          brick_b[idx_decode+1] = rhs_bf16_sig[i][7:4];
          brick_b[idx_decode+2] = rhs_bf16_sig[i][3:0];
          brick_b[idx_decode+3] = rhs_bf16_sig[i][7:4];
        end
      end
      default: begin
      end
    endcase
  end

  always_comb begin
    magnitude = '0;
    product_sign = 1'b0;
    product_valid_o = '0;
    product_count_o = '0;
    for (integer i = 0; i < 16; i = i + 1) begin
      int_product_o[i] = '0;
      fp_product_o[i] = '0;
    end

    unique case (mode_i)
      MODE_I4_I4: begin
        product_valid_o = 16'hffff;
        product_count_o = 16;
        for (integer i = 0; i < 16; i = i + 1)
          int_product_o[i] = apply_sign33({24'b0, brick_p[i]}, lhs_i[i][3] ^ rhs_i[i][3]);
      end
      MODE_I4_I8: begin
        product_valid_o = 16'h00ff;
        product_count_o = 8;
        for (integer i = 0; i < 8; i = i + 1) begin
          idx_output = i << 1;
          magnitude = {24'b0, brick_p[idx_output]} + ({24'b0, brick_p[idx_output+1]} << 4);
          int_product_o[i] = apply_sign33(magnitude, lhs_i[i][3] ^ rhs_i[i][7]);
        end
      end
      MODE_I8_I8: begin
        product_valid_o = 16'h000f;
        product_count_o = 4;
        for (integer i = 0; i < 4; i = i + 1) begin
          idx_output = i << 2;
          magnitude = {24'b0, brick_p[idx_output]}
                    + ({24'b0, brick_p[idx_output+1]} << 4)
                    + ({24'b0, brick_p[idx_output+2]} << 4)
                    + ({24'b0, brick_p[idx_output+3]} << 8);
          int_product_o[i] = apply_sign33(magnitude, lhs_i[i][7] ^ rhs_i[i][7]);
        end
      end
      MODE_I16_I16: begin
        product_valid_o = 16'h0001;
        product_count_o = 1;
        magnitude = '0;
        for (integer i = 0; i < 4; i = i + 1)
          for (integer j = 0; j < 4; j = j + 1) begin
            idx_output = (i << 2) + j;
            magnitude = magnitude + ({24'b0, brick_p[idx_output]} << ((i+j) << 2));
          end
        int_product_o[0] = apply_sign33(magnitude, lhs_i[0][15] ^ rhs_i[0][15]);
      end
      MODE_FP8_FP8: begin
        product_valid_o = 16'hffff;
        product_count_o = 16;
        for (integer i = 0; i < 16; i = i + 1)
          fp_product_o[i] = raw_binary_product_to_fp32(
            lhs_fp8_sign[i] ^ rhs_fp8_sign[i],
            {24'b0, brick_p[i]},
            lhs_fp8_scale[i] + rhs_fp8_scale[i],
            lhs_fp8_zero[i] || rhs_fp8_zero[i],
            1'b0,
            lhs_fp8_nan[i] || rhs_fp8_nan[i]
          );
      end
      MODE_BF16_BF16: begin
        product_valid_o = 16'h000f;
        product_count_o = 4;
        for (integer i = 0; i < 4; i = i + 1) begin
          idx_output = i << 2;
          magnitude = {24'b0, brick_p[idx_output]}
                    + ({24'b0, brick_p[idx_output+1]} << 4)
                    + ({24'b0, brick_p[idx_output+2]} << 4)
                    + ({24'b0, brick_p[idx_output+3]} << 8);
          fp_product_o[i] = raw_binary_product_to_fp32(
            lhs_bf16_sign[i] ^ rhs_bf16_sign[i],
            magnitude,
            lhs_bf16_scale[i] + rhs_bf16_scale[i],
            lhs_bf16_zero[i] || rhs_bf16_zero[i],
            lhs_bf16_inf[i] || rhs_bf16_inf[i],
            lhs_bf16_nan[i] || rhs_bf16_nan[i]
              || ((lhs_bf16_zero[i] || rhs_bf16_zero[i])
              && (lhs_bf16_inf[i] || rhs_bf16_inf[i]))
          );
        end
      end
      MODE_I4_FP8: begin
        product_valid_o = 16'hffff;
        product_count_o = 16;
        for (integer i = 0; i < 16; i = i + 1)
          fp_product_o[i] = raw_binary_product_to_fp32(
            lhs_i[i][3] ^ rhs_fp8_sign[i],
            {24'b0, brick_p[i]},
            rhs_fp8_scale[i],
            (lhs_i[i][3:0] == 0) || rhs_fp8_zero[i],
            1'b0,
            rhs_fp8_nan[i]
          );
      end
      MODE_I8_FP8: begin
        product_valid_o = 16'h00ff;
        product_count_o = 8;
        for (integer i = 0; i < 8; i = i + 1) begin
          idx_output = i << 1;
          magnitude = {24'b0, brick_p[idx_output]} + ({24'b0, brick_p[idx_output+1]} << 4);
          fp_product_o[i] = raw_binary_product_to_fp32(
            lhs_i[i][7] ^ rhs_fp8_sign[i],
            magnitude,
            rhs_fp8_scale[i],
            (lhs_i[i][7:0] == 0) || rhs_fp8_zero[i],
            1'b0,
            rhs_fp8_nan[i]
          );
        end
      end
      MODE_I4_BF16: begin
        product_valid_o = 16'h00ff;
        product_count_o = 8;
        for (integer i = 0; i < 8; i = i + 1) begin
          idx_output = i << 1;
          magnitude = {24'b0, brick_p[idx_output]} + ({24'b0, brick_p[idx_output+1]} << 4);
          fp_product_o[i] = raw_binary_product_to_fp32(
            lhs_i[i][3] ^ rhs_bf16_sign[i],
            magnitude,
            rhs_bf16_scale[i],
            (lhs_i[i][3:0] == 0) || rhs_bf16_zero[i],
            rhs_bf16_inf[i],
            rhs_bf16_nan[i] || ((lhs_i[i][3:0] == 0) && rhs_bf16_inf[i])
          );
        end
      end
      MODE_I8_BF16: begin
        product_valid_o = 16'h000f;
        product_count_o = 4;
        for (integer i = 0; i < 4; i = i + 1) begin
          idx_output = i << 2;
          magnitude = {24'b0, brick_p[idx_output]}
                    + ({24'b0, brick_p[idx_output+1]} << 4)
                    + ({24'b0, brick_p[idx_output+2]} << 4)
                    + ({24'b0, brick_p[idx_output+3]} << 8);
          fp_product_o[i] = raw_binary_product_to_fp32(
            lhs_i[i][7] ^ rhs_bf16_sign[i],
            magnitude,
            rhs_bf16_scale[i],
            (lhs_i[i][7:0] == 0) || rhs_bf16_zero[i],
            rhs_bf16_inf[i],
            rhs_bf16_nan[i] || ((lhs_i[i][7:0] == 0) && rhs_bf16_inf[i])
          );
        end
      end
      default: begin
      end
    endcase
  end
endmodule

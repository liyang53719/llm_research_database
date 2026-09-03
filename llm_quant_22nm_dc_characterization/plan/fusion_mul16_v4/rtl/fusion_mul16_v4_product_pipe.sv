module fusion_mul16_v4_product_pipe #(
  parameter bit SUPPORT_FP8 = 1'b1,
  parameter bit SUPPORT_BF16 = 1'b1,
  parameter bit SUPPORT_I4_FP8 = 1'b1,
  parameter bit SUPPORT_I4_BF16 = 1'b1,
  parameter bit SUPPORT_I8_BF16 = 1'b1,
  parameter bit SUPPORT_SPECIALS = 1'b0
) (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic clear_i,
  input  logic [6:0] mode_onehot_i,
  input  logic [127:0] lhs_packed_i,
  input  logic [127:0] rhs_packed_i,
  output logic int_valid_o,
  output logic int_clear_o,
  output logic signed [17:0] int_lane_sum_o [0:3],
  output logic fp_valid_o,
  output logic fp_clear_o,
  output logic [15:0] bf16_lane_item_o [0:3][0:3]
);
  import fusion_mul16_v4_pkg::*;

  logic [3:0] brick_a_d [0:15];
  logic [3:0] brick_b_d [0:15];
  logic [3:0] brick_a_q [0:15];
  logic [3:0] brick_b_q [0:15];
  logic [7:0] brick_p_w [0:15];
  logic [7:0] brick_p_q [0:15];

  logic product_sign_d [0:15];
  logic product_zero_d [0:15];
  logic product_inf_d [0:15];
  logic product_nan_d [0:15];
  logic signed [10:0] product_scale_d [0:15];
  logic product_sign_q0 [0:15];
  logic product_zero_q0 [0:15];
  logic product_inf_q0 [0:15];
  logic product_nan_q0 [0:15];
  logic signed [10:0] product_scale_q0 [0:15];
  logic product_sign_q1 [0:15];
  logic product_zero_q1 [0:15];
  logic product_inf_q1 [0:15];
  logic product_nan_q1 [0:15];
  logic signed [10:0] product_scale_q1 [0:15];

  logic [6:0] mode_onehot_q0;
  logic [6:0] mode_onehot_q1;
  logic [6:0] mode_onehot_q2;
  logic valid_q0;
  logic valid_q1;
  logic valid_q2;
  logic clear_q0;
  logic clear_q1;
  logic clear_q2;

  logic signed [16:0] int_product_d [0:7];
  logic signed [17:0] int_lane_sum_d [0:3];

  logic [15:0] fp_raw_d [0:15];
  logic fp_sign_d [0:15];
  logic fp_zero_d [0:15];
  logic fp_inf_d [0:15];
  logic fp_nan_d [0:15];
  logic signed [10:0] fp_scale_d [0:15];
  logic [15:0] fp_raw_q [0:15];
  logic fp_sign_q [0:15];
  logic fp_zero_q [0:15];
  logic fp_inf_q [0:15];
  logic fp_nan_q [0:15];
  logic signed [10:0] fp_scale_q [0:15];
  logic [15:0] bf16_product_w [0:15];

  fp_operand_t lhs_fp;
  fp_operand_t rhs_fp;
  logic [3:0] lhs_i4_mag;
  logic [7:0] lhs_i8_mag;
  logic [7:0] rhs_i8_mag;
  logic [15:0] magnitude16;
  logic signed [16:0] signed17;
  integer base_s0;
  integer base_s2;
  integer flat_s2;

  genvar g;
  generate
    for (g = 0; g < 16; g = g + 1) begin : G_BRICK
      fusion_mul16_v4_mul4x4_brick u_brick (
        .a_i(brick_a_q[g]),
        .b_i(brick_b_q[g]),
        .p_o(brick_p_w[g])
      );
    end
  endgenerate

  // S0: mode-dependent unpack and operand routing. The mode is a predecoded
  // configuration register, not a cycle-by-cycle data input.
  always_comb begin
    for (int i = 0; i < 16; i = i + 1) begin
      brick_a_d[i] = '0;
      brick_b_d[i] = '0;
      product_sign_d[i] = 1'b0;
      product_zero_d[i] = 1'b1;
      product_inf_d[i] = 1'b0;
      product_nan_d[i] = 1'b0;
      product_scale_d[i] = '0;
    end
    lhs_fp = '0;
    rhs_fp = '0;
    lhs_i4_mag = '0;
    lhs_i8_mag = '0;
    rhs_i8_mag = '0;
    base_s0 = 0;

    if (mode_onehot_i[0]) begin
      for (int i = 0; i < 8; i = i + 1) begin
        lhs_i4_mag = abs_i4(lhs_packed_i[i*4 +: 4]);
        rhs_i8_mag = abs_i8(rhs_packed_i[i*8 +: 8]);
        base_s0 = i << 1;
        brick_a_d[base_s0] = lhs_i4_mag;
        brick_a_d[base_s0+1] = lhs_i4_mag;
        brick_b_d[base_s0] = rhs_i8_mag[3:0];
        brick_b_d[base_s0+1] = rhs_i8_mag[7:4];
        product_sign_d[i] = lhs_packed_i[i*4+3] ^ rhs_packed_i[i*8+7];
        product_zero_d[i] = (lhs_packed_i[i*4 +: 4] == 0)
                         || (rhs_packed_i[i*8 +: 8] == 0);
      end
    end else if (mode_onehot_i[1]) begin
      for (int i = 0; i < 4; i = i + 1) begin
        lhs_i8_mag = abs_i8(lhs_packed_i[i*8 +: 8]);
        rhs_i8_mag = abs_i8(rhs_packed_i[i*8 +: 8]);
        base_s0 = i << 2;
        brick_a_d[base_s0] = lhs_i8_mag[3:0];
        brick_a_d[base_s0+1] = lhs_i8_mag[3:0];
        brick_a_d[base_s0+2] = lhs_i8_mag[7:4];
        brick_a_d[base_s0+3] = lhs_i8_mag[7:4];
        brick_b_d[base_s0] = rhs_i8_mag[3:0];
        brick_b_d[base_s0+1] = rhs_i8_mag[7:4];
        brick_b_d[base_s0+2] = rhs_i8_mag[3:0];
        brick_b_d[base_s0+3] = rhs_i8_mag[7:4];
        product_sign_d[i] = lhs_packed_i[i*8+7] ^ rhs_packed_i[i*8+7];
        product_zero_d[i] = (lhs_packed_i[i*8 +: 8] == 0)
                         || (rhs_packed_i[i*8 +: 8] == 0);
      end
    end else if (mode_onehot_i[2] && SUPPORT_FP8) begin
      for (int i = 0; i < 16; i = i + 1) begin
        lhs_fp = decode_fp8(lhs_packed_i[i*8 +: 8]);
        rhs_fp = decode_fp8(rhs_packed_i[i*8 +: 8]);
        brick_a_d[i] = lhs_fp.significand[3:0];
        brick_b_d[i] = rhs_fp.significand[3:0];
        product_sign_d[i] = lhs_fp.sign ^ rhs_fp.sign;
        product_scale_d[i] = lhs_fp.scale_exp + rhs_fp.scale_exp;
        product_zero_d[i] = lhs_fp.is_zero || rhs_fp.is_zero;
        product_nan_d[i] = lhs_fp.is_nan || rhs_fp.is_nan;
      end
    end else if (mode_onehot_i[3] && SUPPORT_BF16) begin
      for (int i = 0; i < 4; i = i + 1) begin
        lhs_fp = decode_bf16(lhs_packed_i[i*16 +: 16]);
        rhs_fp = decode_bf16(rhs_packed_i[i*16 +: 16]);
        base_s0 = i << 2;
        brick_a_d[base_s0] = lhs_fp.significand[3:0];
        brick_a_d[base_s0+1] = lhs_fp.significand[3:0];
        brick_a_d[base_s0+2] = lhs_fp.significand[7:4];
        brick_a_d[base_s0+3] = lhs_fp.significand[7:4];
        brick_b_d[base_s0] = rhs_fp.significand[3:0];
        brick_b_d[base_s0+1] = rhs_fp.significand[7:4];
        brick_b_d[base_s0+2] = rhs_fp.significand[3:0];
        brick_b_d[base_s0+3] = rhs_fp.significand[7:4];
        product_sign_d[i] = lhs_fp.sign ^ rhs_fp.sign;
        product_scale_d[i] = lhs_fp.scale_exp + rhs_fp.scale_exp;
        product_zero_d[i] = lhs_fp.is_zero || rhs_fp.is_zero;
        product_inf_d[i] = (lhs_fp.is_inf || rhs_fp.is_inf)
                         && !(lhs_fp.is_zero || rhs_fp.is_zero);
        product_nan_d[i] = lhs_fp.is_nan || rhs_fp.is_nan
                         || ((lhs_fp.is_zero || rhs_fp.is_zero)
                         && (lhs_fp.is_inf || rhs_fp.is_inf));
      end
    end else if (mode_onehot_i[4] && SUPPORT_I4_FP8) begin
      for (int i = 0; i < 16; i = i + 1) begin
        lhs_i4_mag = abs_i4(lhs_packed_i[i*4 +: 4]);
        rhs_fp = decode_fp8(rhs_packed_i[i*8 +: 8]);
        brick_a_d[i] = lhs_i4_mag;
        brick_b_d[i] = rhs_fp.significand[3:0];
        product_sign_d[i] = lhs_packed_i[i*4+3] ^ rhs_fp.sign;
        product_scale_d[i] = rhs_fp.scale_exp;
        product_zero_d[i] = (lhs_packed_i[i*4 +: 4] == 0) || rhs_fp.is_zero;
        product_nan_d[i] = rhs_fp.is_nan;
      end
    end else if (mode_onehot_i[5] && SUPPORT_I4_BF16) begin
      for (int i = 0; i < 8; i = i + 1) begin
        lhs_i4_mag = abs_i4(lhs_packed_i[i*4 +: 4]);
        rhs_fp = decode_bf16(rhs_packed_i[i*16 +: 16]);
        base_s0 = i << 1;
        brick_a_d[base_s0] = lhs_i4_mag;
        brick_a_d[base_s0+1] = lhs_i4_mag;
        brick_b_d[base_s0] = rhs_fp.significand[3:0];
        brick_b_d[base_s0+1] = rhs_fp.significand[7:4];
        product_sign_d[i] = lhs_packed_i[i*4+3] ^ rhs_fp.sign;
        product_scale_d[i] = rhs_fp.scale_exp;
        product_zero_d[i] = (lhs_packed_i[i*4 +: 4] == 0) || rhs_fp.is_zero;
        product_inf_d[i] = rhs_fp.is_inf && (lhs_packed_i[i*4 +: 4] != 0);
        product_nan_d[i] = rhs_fp.is_nan
                         || (rhs_fp.is_inf && (lhs_packed_i[i*4 +: 4] == 0));
      end
    end else if (mode_onehot_i[6] && SUPPORT_I8_BF16) begin
      for (int i = 0; i < 4; i = i + 1) begin
        lhs_i8_mag = abs_i8(lhs_packed_i[i*8 +: 8]);
        rhs_fp = decode_bf16(rhs_packed_i[i*16 +: 16]);
        base_s0 = i << 2;
        brick_a_d[base_s0] = lhs_i8_mag[3:0];
        brick_a_d[base_s0+1] = lhs_i8_mag[3:0];
        brick_a_d[base_s0+2] = lhs_i8_mag[7:4];
        brick_a_d[base_s0+3] = lhs_i8_mag[7:4];
        brick_b_d[base_s0] = rhs_fp.significand[3:0];
        brick_b_d[base_s0+1] = rhs_fp.significand[7:4];
        brick_b_d[base_s0+2] = rhs_fp.significand[3:0];
        brick_b_d[base_s0+3] = rhs_fp.significand[7:4];
        product_sign_d[i] = lhs_packed_i[i*8+7] ^ rhs_fp.sign;
        product_scale_d[i] = rhs_fp.scale_exp;
        product_zero_d[i] = (lhs_packed_i[i*8 +: 8] == 0) || rhs_fp.is_zero;
        product_inf_d[i] = rhs_fp.is_inf && (lhs_packed_i[i*8 +: 8] != 0);
        product_nan_d[i] = rhs_fp.is_nan
                         || (rhs_fp.is_inf && (lhs_packed_i[i*8 +: 8] == 0));
      end
    end
  end

  // S1: register routed 4-bit operands. Configuration decode is now behind a flop.
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_q0 <= 1'b0;
      clear_q0 <= 1'b0;
      mode_onehot_q0 <= '0;
      for (int i = 0; i < 16; i = i + 1) begin
        brick_a_q[i] <= '0;
        brick_b_q[i] <= '0;
        product_sign_q0[i] <= 1'b0;
        product_zero_q0[i] <= 1'b1;
        product_inf_q0[i] <= 1'b0;
        product_nan_q0[i] <= 1'b0;
        product_scale_q0[i] <= '0;
      end
    end else begin
      valid_q0 <= valid_i;
      clear_q0 <= clear_i;
      mode_onehot_q0 <= mode_onehot_i;
      for (int i = 0; i < 16; i = i + 1) begin
        brick_a_q[i] <= brick_a_d[i];
        brick_b_q[i] <= brick_b_d[i];
        product_sign_q0[i] <= product_sign_d[i];
        product_zero_q0[i] <= product_zero_d[i];
        product_inf_q0[i] <= product_inf_d[i];
        product_nan_q0[i] <= product_nan_d[i];
        product_scale_q0[i] <= product_scale_d[i];
      end
    end
  end

  // S2: register all 16 brick results. This is the only multiplication stage.
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_q1 <= 1'b0;
      clear_q1 <= 1'b0;
      mode_onehot_q1 <= '0;
      for (int i = 0; i < 16; i = i + 1) begin
        brick_p_q[i] <= '0;
        product_sign_q1[i] <= 1'b0;
        product_zero_q1[i] <= 1'b1;
        product_inf_q1[i] <= 1'b0;
        product_nan_q1[i] <= 1'b0;
        product_scale_q1[i] <= '0;
      end
    end else begin
      valid_q1 <= valid_q0;
      clear_q1 <= clear_q0;
      mode_onehot_q1 <= mode_onehot_q0;
      for (int i = 0; i < 16; i = i + 1) begin
        brick_p_q[i] <= brick_p_w[i];
        product_sign_q1[i] <= product_sign_q0[i];
        product_zero_q1[i] <= product_zero_q0[i];
        product_inf_q1[i] <= product_inf_q0[i];
        product_nan_q1[i] <= product_nan_q0[i];
        product_scale_q1[i] <= product_scale_q0[i];
      end
    end
  end

  // S3: narrow integer fusion and <=16-bit floating raw product fusion.
  always_comb begin
    for (int i = 0; i < 8; i = i + 1)
      int_product_d[i] = '0;
    for (int lane = 0; lane < 4; lane = lane + 1)
      int_lane_sum_d[lane] = '0;
    for (int i = 0; i < 16; i = i + 1) begin
      fp_raw_d[i] = '0;
      fp_sign_d[i] = 1'b0;
      fp_zero_d[i] = 1'b1;
      fp_inf_d[i] = 1'b0;
      fp_nan_d[i] = 1'b0;
      fp_scale_d[i] = '0;
    end
    magnitude16 = '0;
    signed17 = '0;
    base_s2 = 0;
    flat_s2 = 0;

    if (mode_onehot_q1[0]) begin
      for (int i = 0; i < 8; i = i + 1) begin
        base_s2 = i << 1;
        magnitude16 = {8'b0, brick_p_q[base_s2]}
                    + ({8'b0, brick_p_q[base_s2+1]} << 4);
        int_product_d[i] = apply_sign17(magnitude16, product_sign_q1[i]);
      end
      for (int lane = 0; lane < 4; lane = lane + 1)
        int_lane_sum_d[lane] = int_product_d[lane<<1] + int_product_d[(lane<<1)+1];
    end else if (mode_onehot_q1[1]) begin
      for (int i = 0; i < 4; i = i + 1) begin
        base_s2 = i << 2;
        magnitude16 = {8'b0, brick_p_q[base_s2]}
                    + ({8'b0, brick_p_q[base_s2+1]} << 4)
                    + ({8'b0, brick_p_q[base_s2+2]} << 4)
                    + ({8'b0, brick_p_q[base_s2+3]} << 8);
        int_product_d[i] = apply_sign17(magnitude16, product_sign_q1[i]);
        int_lane_sum_d[i] = int_product_d[i];
      end
    end else if (mode_onehot_q1[2] && SUPPORT_FP8) begin
      for (int i = 0; i < 16; i = i + 1) begin
        fp_raw_d[i] = {8'b0, brick_p_q[i]};
        fp_sign_d[i] = product_sign_q1[i];
        fp_zero_d[i] = product_zero_q1[i];
        fp_nan_d[i] = product_nan_q1[i];
        fp_scale_d[i] = product_scale_q1[i];
      end
    end else if (mode_onehot_q1[3] && SUPPORT_BF16) begin
      for (int i = 0; i < 4; i = i + 1) begin
        base_s2 = i << 2;
        flat_s2 = i << 2;
        fp_raw_d[flat_s2] = {8'b0, brick_p_q[base_s2]}
                       + ({8'b0, brick_p_q[base_s2+1]} << 4)
                       + ({8'b0, brick_p_q[base_s2+2]} << 4)
                       + ({8'b0, brick_p_q[base_s2+3]} << 8);
        fp_sign_d[flat_s2] = product_sign_q1[i];
        fp_zero_d[flat_s2] = product_zero_q1[i];
        fp_inf_d[flat_s2] = product_inf_q1[i];
        fp_nan_d[flat_s2] = product_nan_q1[i];
        fp_scale_d[flat_s2] = product_scale_q1[i];
      end
    end else if (mode_onehot_q1[4] && SUPPORT_I4_FP8) begin
      for (int i = 0; i < 16; i = i + 1) begin
        fp_raw_d[i] = {8'b0, brick_p_q[i]};
        fp_sign_d[i] = product_sign_q1[i];
        fp_zero_d[i] = product_zero_q1[i];
        fp_nan_d[i] = product_nan_q1[i];
        fp_scale_d[i] = product_scale_q1[i];
      end
    end else if (mode_onehot_q1[5] && SUPPORT_I4_BF16) begin
      for (int i = 0; i < 8; i = i + 1) begin
        base_s2 = i << 1;
        flat_s2 = ((i >> 1) << 2) + (i & 1);
        fp_raw_d[flat_s2] = {8'b0, brick_p_q[base_s2]}
                       + ({8'b0, brick_p_q[base_s2+1]} << 4);
        fp_sign_d[flat_s2] = product_sign_q1[i];
        fp_zero_d[flat_s2] = product_zero_q1[i];
        fp_inf_d[flat_s2] = product_inf_q1[i];
        fp_nan_d[flat_s2] = product_nan_q1[i];
        fp_scale_d[flat_s2] = product_scale_q1[i];
      end
    end else if (mode_onehot_q1[6] && SUPPORT_I8_BF16) begin
      for (int i = 0; i < 4; i = i + 1) begin
        base_s2 = i << 2;
        flat_s2 = i << 2;
        fp_raw_d[flat_s2] = {8'b0, brick_p_q[base_s2]}
                       + ({8'b0, brick_p_q[base_s2+1]} << 4)
                       + ({8'b0, brick_p_q[base_s2+2]} << 4)
                       + ({8'b0, brick_p_q[base_s2+3]} << 8);
        fp_sign_d[flat_s2] = product_sign_q1[i];
        fp_zero_d[flat_s2] = product_zero_q1[i];
        fp_inf_d[flat_s2] = product_inf_q1[i];
        fp_nan_d[flat_s2] = product_nan_q1[i];
        fp_scale_d[flat_s2] = product_scale_q1[i];
      end
    end
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_q2 <= 1'b0;
      clear_q2 <= 1'b0;
      mode_onehot_q2 <= '0;
      for (int lane = 0; lane < 4; lane = lane + 1)
        int_lane_sum_o[lane] <= '0;
      for (int i = 0; i < 16; i = i + 1) begin
        fp_raw_q[i] <= '0;
        fp_sign_q[i] <= 1'b0;
        fp_zero_q[i] <= 1'b1;
        fp_inf_q[i] <= 1'b0;
        fp_nan_q[i] <= 1'b0;
        fp_scale_q[i] <= '0;
      end
    end else begin
      valid_q2 <= valid_q1;
      clear_q2 <= clear_q1;
      mode_onehot_q2 <= mode_onehot_q1;
      for (int lane = 0; lane < 4; lane = lane + 1)
        int_lane_sum_o[lane] <= int_lane_sum_d[lane];
      for (int i = 0; i < 16; i = i + 1) begin
        fp_raw_q[i] <= fp_raw_d[i];
        fp_sign_q[i] <= fp_sign_d[i];
        fp_zero_q[i] <= fp_zero_d[i];
        fp_inf_q[i] <= fp_inf_d[i];
        fp_nan_q[i] <= fp_nan_d[i];
        fp_scale_q[i] <= fp_scale_d[i];
      end
    end
  end

  // S4: direct narrow product normalization to BF16. No FP32 product bus/register.
  generate
    for (g = 0; g < 16; g = g + 1) begin : G_BF16_PACK
      fusion_mul16_v4_raw16_to_bf16_rne #(.SUPPORT_SPECIALS(SUPPORT_SPECIALS)) u_pack (
        .sign_i(fp_sign_q[g]),
        .raw_i(fp_raw_q[g]),
        .scale_exp_i(fp_scale_q[g]),
        .zero_i(fp_zero_q[g]),
        .inf_i(fp_inf_q[g]),
        .nan_i(fp_nan_q[g]),
        .bf16_o(bf16_product_w[g])
      );
    end
  endgenerate

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      fp_valid_o <= 1'b0;
      fp_clear_o <= 1'b0;
      for (int lane = 0; lane < 4; lane = lane + 1)
        for (int item = 0; item < 4; item = item + 1)
          bf16_lane_item_o[lane][item] <= '0;
    end else begin
      fp_valid_o <= valid_q2 && (|mode_onehot_q2[6:2]);
      fp_clear_o <= clear_q2;
      for (int lane = 0; lane < 4; lane = lane + 1)
        for (int item = 0; item < 4; item = item + 1) begin
          bf16_lane_item_o[lane][item] <= bf16_product_w[(lane << 2) + item];
        end
    end
  end

  assign int_valid_o = valid_q2 && (mode_onehot_q2[0] || mode_onehot_q2[1]);
  assign int_clear_o = clear_q2;
endmodule

module fusion_mul16_v3_accum_block64_fp32_checkpoint_dw #(
  parameter int BLOCK_PRODUCTS = 64,
  parameter int CHECKPOINT_WAIT_CYCLES = 2
) (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic clear_i,
  input  logic flush_i,
  input  logic [2:0] items_per_lane_i,
  input  logic [15:0] lane_item_i [0:3][0:3],
  input  logic [2:0] rnd_i,
  output logic checkpoint_valid_o,
  output logic flush_done_o,
  output logic protocol_error_o,
  output logic [31:0] checkpoint_fp32_o [0:3],
  output logic [15:0] partial_bf16_o [0:3],
  output logic [6:0] products_in_partial_o,
  output logic [7:0] status_o [0:3]
);
  localparam int WAIT_W = (CHECKPOINT_WAIT_CYCLES < 1) ? 1 : CHECKPOINT_WAIT_CYCLES;

  logic tree_valid;
  logic tree_clear;
  logic [15:0] lane_sum [0:3];
  logic [7:0] tree_status [0:3];

  logic [15:0] partial_next_w [0:3];
  logic [7:0] partial_status [0:3];
  logic [31:0] checkpoint_term_q [0:3];
  logic [31:0] checkpoint_base_q [0:3];
  logic [31:0] checkpoint_next_w [0:3];
  logic [7:0] checkpoint_status [0:3];
  logic [WAIT_W-1:0] checkpoint_wait_q;
  logic checkpoint_busy;
  logic boundary_w;
  logic flush_accept_w;
  logic items_legal_w;
  logic [7:0] next_product_count_w;
  logic flush_tag_q;
  integer lane;

  fusion_mul16_v3_bf16_tree_dw u_tree (
    .clk, .rst_n, .valid_i, .clear_i, .lane_item_i, .rnd_i,
    .valid_o(tree_valid), .clear_o(tree_clear),
    .lane_sum_o(lane_sum), .status_o(tree_status)
  );

  assign checkpoint_busy = |checkpoint_wait_q;
  assign items_legal_w = (items_per_lane_i == 3'd1)
                      || (items_per_lane_i == 3'd2)
                      || (items_per_lane_i == 3'd4);
  assign next_product_count_w = {1'b0, products_in_partial_o}
                              + {5'b0, items_per_lane_i};
  assign boundary_w = tree_valid && items_legal_w
                   && (next_product_count_w == BLOCK_PRODUCTS);
  // flush_i is a separate control beat. The caller must assert it only after
  // the two-stage BF16 tree has drained and with valid_i=0.
  assign flush_accept_w = flush_i && !valid_i && !tree_valid
                       && (products_in_partial_o != 0) && !checkpoint_busy;

  genvar g;
  generate
    for (g = 0; g < 4; g = g + 1) begin : G_ACC
      DW_fp_add #(7, 8, 0) u_partial_acc (
        .a(partial_bf16_o[g]), .b(lane_sum[g]), .rnd(rnd_i),
        .z(partial_next_w[g]), .status(partial_status[g])
      );
      DW_fp_add #(23, 8, 0) u_checkpoint_acc (
        .a(checkpoint_base_q[g]), .b(checkpoint_term_q[g]), .rnd(rnd_i),
        .z(checkpoint_next_w[g]), .status(checkpoint_status[g])
      );
    end
  endgenerate

  // A checkpoint term is captured only once per 64 products/lane (or on an
  // explicit tail flush). The FP32 operands remain stable while wait_q shifts.
  // Local DC must apply the matching multicycle path if WAIT_CYCLES > 1.
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      checkpoint_valid_o <= 1'b0;
      flush_done_o <= 1'b0;
      protocol_error_o <= 1'b0;
      products_in_partial_o <= '0;
      checkpoint_wait_q <= '0;
      flush_tag_q <= 1'b0;
      for (lane = 0; lane < 4; lane = lane + 1) begin
        checkpoint_fp32_o[lane] <= '0;
        partial_bf16_o[lane] <= '0;
        checkpoint_term_q[lane] <= '0;
        checkpoint_base_q[lane] <= '0;
        status_o[lane] <= '0;
      end
    end else begin
      checkpoint_valid_o <= 1'b0;
      flush_done_o <= 1'b0;
      protocol_error_o <= 1'b0;

      if (checkpoint_wait_q[WAIT_W-1]) begin
        checkpoint_valid_o <= 1'b1;
        flush_done_o <= flush_tag_q;
        flush_tag_q <= 1'b0;
        checkpoint_wait_q <= '0;
        for (lane = 0; lane < 4; lane = lane + 1) begin
          checkpoint_fp32_o[lane] <= checkpoint_next_w[lane];
          status_o[lane] <= status_o[lane] | checkpoint_status[lane];
        end
      end else if (checkpoint_wait_q != 0) begin
        checkpoint_wait_q <= checkpoint_wait_q << 1;
      end

      if (tree_clear) begin
        products_in_partial_o <= '0;
        checkpoint_wait_q <= '0;
        flush_tag_q <= 1'b0;
        for (lane = 0; lane < 4; lane = lane + 1) begin
          checkpoint_fp32_o[lane] <= '0;
          partial_bf16_o[lane] <= '0;
          checkpoint_term_q[lane] <= '0;
          checkpoint_base_q[lane] <= '0;
          status_o[lane] <= '0;
        end
      end else begin
        if (tree_valid && !items_legal_w)
          protocol_error_o <= 1'b1;
        if (tree_valid && (next_product_count_w > BLOCK_PRODUCTS))
          protocol_error_o <= 1'b1;
        if ((boundary_w || flush_accept_w) && checkpoint_busy)
          protocol_error_o <= 1'b1;

        if (tree_valid && items_legal_w) begin
          if (boundary_w && !checkpoint_busy) begin
            products_in_partial_o <= '0;
            checkpoint_wait_q <= {{(WAIT_W-1){1'b0}}, 1'b1};
            flush_tag_q <= 1'b0;
            for (lane = 0; lane < 4; lane = lane + 1) begin
              checkpoint_base_q[lane] <= checkpoint_fp32_o[lane];
              checkpoint_term_q[lane] <= {partial_next_w[lane], 16'b0};
              partial_bf16_o[lane] <= '0;
              status_o[lane] <= status_o[lane]
                              | tree_status[lane] | partial_status[lane];
            end
          end else if (boundary_w && checkpoint_busy) begin
            protocol_error_o <= 1'b1;
          end else if (next_product_count_w < BLOCK_PRODUCTS) begin
            products_in_partial_o <= next_product_count_w[6:0];
            for (lane = 0; lane < 4; lane = lane + 1) begin
              partial_bf16_o[lane] <= partial_next_w[lane];
              status_o[lane] <= status_o[lane]
                              | tree_status[lane] | partial_status[lane];
            end
          end
        end

        if (flush_accept_w) begin
          products_in_partial_o <= '0;
          checkpoint_wait_q <= {{(WAIT_W-1){1'b0}}, 1'b1};
          flush_tag_q <= 1'b1;
          for (lane = 0; lane < 4; lane = lane + 1) begin
            checkpoint_base_q[lane] <= checkpoint_fp32_o[lane];
            checkpoint_term_q[lane] <= {partial_bf16_o[lane], 16'b0};
            partial_bf16_o[lane] <= '0;
          end
        end else if (flush_i && !flush_accept_w) begin
          protocol_error_o <= 1'b1;
        end
      end
    end
  end
endmodule

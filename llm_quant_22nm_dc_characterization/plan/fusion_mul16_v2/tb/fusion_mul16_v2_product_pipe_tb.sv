`timescale 1ns/1ps
module fusion_mul16_v2_product_pipe_tb;
  localparam int MAX_VECTORS = 8192;
  logic clk = 1'b0;
  logic rst_n = 1'b0;
  logic valid_i = 1'b0;
  logic clear_i = 1'b0;
  logic [6:0] mode_onehot_i;
  logic [127:0] lhs_packed_i;
  logic [127:0] rhs_packed_i;
  logic int_valid_o;
  logic int_clear_o;
  logic signed [17:0] int_lane_sum_o [0:3];
  logic fp_valid_o;
  logic fp_clear_o;
  logic [15:0] bf16_lane_item_o [0:3][0:3];

  logic [127:0] lhs_mem [0:MAX_VECTORS-1];
  logic [127:0] rhs_mem [0:MAX_VECTORS-1];
  logic [17:0] int_mem [0:MAX_VECTORS-1][0:3];
  logic [15:0] fp_mem [0:MAX_VECTORS-1][0:15];

  integer vector_count;
  integer issue_index;
  integer check_index;
  integer failures;
  integer fd;
  integer rc;
  integer mode_index;
  integer lane;
  integer item;
  integer timeout_cycles;
  string vector_file;

  always #0.5 clk = ~clk;

  fusion_mul16_v2_product_pipe #(
    .SUPPORT_FP8(1'b1),
    .SUPPORT_BF16(1'b1),
    .SUPPORT_I4_FP8(1'b1),
    .SUPPORT_I4_BF16(1'b1),
    .SUPPORT_I8_BF16(1'b1),
    .SUPPORT_SPECIALS(1'b1)
  ) u_dut (
    .clk, .rst_n, .valid_i, .clear_i, .mode_onehot_i,
    .lhs_packed_i, .rhs_packed_i,
    .int_valid_o, .int_clear_o, .int_lane_sum_o,
    .fp_valid_o, .fp_clear_o, .bf16_lane_item_o
  );

  initial begin
    if (!$value$plusargs("MODE=%d", mode_index))
      $fatal(1, "Missing +MODE=<0..6>");
    if (!$value$plusargs("VECTORS=%s", vector_file))
      $fatal(1, "Missing +VECTORS=<path>");
    if ((mode_index < 0) || (mode_index > 6))
      $fatal(1, "Invalid mode index %0d", mode_index);
    mode_onehot_i = 7'b1 << mode_index;
    lhs_packed_i = '0;
    rhs_packed_i = '0;
    vector_count = 0;
    issue_index = 0;
    check_index = 0;
    failures = 0;
    timeout_cycles = 0;

    fd = $fopen(vector_file, "r");
    if (fd == 0)
      $fatal(1, "Could not open %s", vector_file);
    while (!$feof(fd) && (vector_count < MAX_VECTORS)) begin
      rc = $fscanf(fd, "%h %h", lhs_mem[vector_count], rhs_mem[vector_count]);
      if (rc != 2)
        break;
      for (lane = 0; lane < 4; lane = lane + 1) begin
        rc = $fscanf(fd, "%h", int_mem[vector_count][lane]);
        if (rc != 1) $fatal(1, "Malformed integer expected field");
      end
      for (item = 0; item < 16; item = item + 1) begin
        rc = $fscanf(fd, "%h", fp_mem[vector_count][item]);
        if (rc != 1) $fatal(1, "Malformed floating expected field");
      end
      vector_count = vector_count + 1;
    end
    $fclose(fd);
    if (vector_count == 0)
      $fatal(1, "No vectors loaded");

    repeat (5) @(negedge clk);
    rst_n = 1'b1;
  end

  always @(negedge clk) begin
    if (!rst_n) begin
      valid_i <= 1'b0;
      lhs_packed_i <= '0;
      rhs_packed_i <= '0;
    end else begin
      timeout_cycles = timeout_cycles + 1;

      if ((mode_index <= 1) && int_valid_o) begin
        for (lane = 0; lane < 4; lane = lane + 1)
          if (int_lane_sum_o[lane] !== int_mem[check_index][lane]) begin
            $display("INT mismatch vector=%0d lane=%0d got=%h exp=%h",
                     check_index, lane, int_lane_sum_o[lane], int_mem[check_index][lane]);
            failures = failures + 1;
          end
        check_index = check_index + 1;
      end

      if ((mode_index >= 2) && fp_valid_o) begin
        for (lane = 0; lane < 4; lane = lane + 1)
          for (item = 0; item < 4; item = item + 1)
            if (bf16_lane_item_o[lane][item] !== fp_mem[check_index][lane*4+item]) begin
              $display("FP mismatch vector=%0d lane=%0d item=%0d got=%h exp=%h",
                       check_index, lane, item, bf16_lane_item_o[lane][item],
                       fp_mem[check_index][lane*4+item]);
              failures = failures + 1;
            end
        check_index = check_index + 1;
      end

      if (issue_index < vector_count) begin
        valid_i <= 1'b1;
        lhs_packed_i <= lhs_mem[issue_index];
        rhs_packed_i <= rhs_mem[issue_index];
        issue_index = issue_index + 1;
      end else begin
        valid_i <= 1'b0;
        lhs_packed_i <= '0;
        rhs_packed_i <= '0;
      end

      if (check_index == vector_count) begin
        if (failures == 0)
          $display("PASS mode=%0d vectors=%0d failures=0", mode_index, vector_count);
        else
          $display("FAIL mode=%0d vectors=%0d failures=%0d", mode_index, vector_count, failures);
        $finish;
      end
      if (timeout_cycles > vector_count + 50)
        $fatal(1, "Timeout: issued=%0d checked=%0d vectors=%0d", issue_index, check_index, vector_count);
    end
  end
endmodule

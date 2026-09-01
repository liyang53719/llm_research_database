module fusion_mul16_latency_tb;
  logic clk = 0;
  logic rst_n = 0;
  logic valid_i = 0;
  logic clear_i = 0;
  logic [3:0] mode_i = 0;
  logic [15:0] lhs_i [0:15];
  logic [15:0] rhs_i [0:15];
  logic [2:0] rnd_i = 3'b000;
  logic int_valid_o;
  logic fp_valid_o;
  logic signed [47:0] int_acc_o [0:3];
  logic [31:0] fp_acc_o [0:3];
  logic [7:0] fp_status_o [0:3];
  integer cycle = 0;
  integer i;
  integer int_in_cycle;
  integer fp_in_cycle;

  always #5 clk = ~clk;
  always @(posedge clk) cycle = cycle + 1;

  fusion_mul16_cluster_dw_pipe dut (.*);

  initial begin
    for (i = 0; i < 16; i = i + 1) begin
      lhs_i[i] = 0;
      rhs_i[i] = 0;
    end
    repeat (2) @(posedge clk);
    @(negedge clk) rst_n = 1;

    @(negedge clk);
    mode_i = 0;
    valid_i = 1;
    for (i = 0; i < 16; i = i + 1) begin
      lhs_i[i] = 1;
      rhs_i[i] = 1;
    end
    @(posedge clk); #1; int_in_cycle = cycle;
    @(negedge clk) valid_i = 0;
    wait (int_valid_o === 1'b1); #1;
    for (i = 0; i < 4; i = i + 1)
      if (int_acc_o[i] !== 48'd4) $fatal(1, "integer accumulator mismatch");
    $display("INT_LATENCY_CYCLES=%0d", cycle - int_in_cycle);

    @(negedge clk);
    mode_i = 4;
    valid_i = 1;
    for (i = 0; i < 16; i = i + 1) begin
      lhs_i[i] = 16'h0038;
      rhs_i[i] = 16'h0038;
    end
    @(posedge clk); #1; fp_in_cycle = cycle;
    @(negedge clk) valid_i = 0;
    wait (fp_valid_o === 1'b1); #1;
    for (i = 0; i < 4; i = i + 1)
      if (fp_acc_o[i] !== 32'h40800000) $fatal(1, "FP accumulator mismatch");
    $display("FP_LATENCY_CYCLES=%0d", cycle - fp_in_cycle);
    $display("LATENCY_TEST_PASS");
    $finish;
  end
endmodule

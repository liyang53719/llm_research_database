`timescale 1ns/1ps
module fusion_mul16_v2_config_tb;
  logic clk=1'b0, rst_n=1'b0;
  logic cfg_valid_i;
  logic [2:0] cfg_mode_i;
  logic [2:0] cfg_rnd_i;
  logic cfg_ready_o, cfg_error_o;
  logic valid_i, accept_data_o;
  logic [2:0] active_mode_o, active_rnd_o;
  logic [6:0] active_onehot_o;
  integer failures=0;

  always #0.5 clk=~clk;

  fusion_mul16_v2_config #(.FIXED_MODE(-1),.INFLIGHT_DEPTH(10)) u_dut (
    .clk,.rst_n,.cfg_valid_i,.cfg_mode_i,.cfg_rnd_i,
    .cfg_ready_o,.cfg_error_o,.valid_i,.accept_data_o,
    .active_mode_o,.active_onehot_o,.active_rnd_o
  );

  task check(input logic condition, input string message);
    if (!condition) begin $display("FAIL: %s",message); failures=failures+1; end
  endtask

  initial begin
    cfg_valid_i=0; cfg_mode_i=0; cfg_rnd_i=0; valid_i=0;
    repeat(4) @(negedge clk); rst_n=1;
    @(negedge clk);
    check(cfg_ready_o===1'b1,"config must be ready after reset");

    // Initial configuration; a simultaneous data beat must not be accepted.
    cfg_valid_i=1; cfg_mode_i=3'd2; cfg_rnd_i=3'b011; valid_i=1;
    #0.1; check(accept_data_o===1'b0,"configuration must have priority over data");
    @(negedge clk); cfg_valid_i=0; valid_i=1;
    #0.1;
    check(active_mode_o==3'd2,"new mode not active");
    check(active_onehot_o==7'b0000100,"onehot not registered");
    check(accept_data_o===1'b1,"data should be accepted after configuration");

    // Pipeline is now non-empty; reconfiguration must be blocked.
    @(negedge clk); valid_i=0; cfg_valid_i=1; cfg_mode_i=3'd3;
    #0.1; check(cfg_ready_o===1'b0,"reconfiguration allowed with inflight data");
    cfg_valid_i=0;
    repeat(12) @(negedge clk);
    #0.1; check(cfg_ready_o===1'b1,"pipeline did not become reconfigurable");

    if(failures==0) $display("PASS config_protocol failures=0");
    else $display("FAIL config_protocol failures=%0d",failures);
    $finish;
  end
endmodule

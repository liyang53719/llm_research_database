`timescale 1ns/1ps
module fusion_mul16_v4_protocol_tb;
  logic clk=0,rst_n=0,cfg_valid_i,valid_i,clear_i,last_i;
  logic [2:0] cfg_mode_i; logic [127:0] lhs_packed_i,rhs_packed_i;
  logic cfg_ready_o,cfg_error_o,in_ready_o,busy_o,protocol_error_o;
  logic int_valid_o,int_last_o,fp_valid_o,fp_last_o,clear_done_o;
  logic signed [47:0] int_acc_o[0:3]; logic [31:0] fp_acc_o[0:3]; logic [7:0] fp_status_o[0:3]; logic [2:0] active_mode_o;
  integer failures; logic saw_clear_done;
  always #0.5 clk=~clk;
  fusion_mul16_v4 #(.INT_ACC_W(48),.SUPPORT_SPECIALS(0),.IEEE_COMPLIANCE(0)) dut(.*);

  always @(posedge clk) begin
    #0.01;
    if (clear_done_o) saw_clear_done <= 1'b1;
  end

  task automatic expect_protocol_error(input string label);
    begin
      #0.01;
      if(!protocol_error_o) begin $display("missing protocol error: %s",label); failures=failures+1; end
    end
  endtask

  initial begin
    cfg_valid_i=0; cfg_mode_i=0; valid_i=0; clear_i=0; last_i=0; lhs_packed_i=0; rhs_packed_i=0; failures=0; saw_clear_done=0;
    repeat(4) @(negedge clk); rst_n=1;

    // Data before configuration.
    valid_i=1; @(posedge clk); expect_protocol_error("data before config"); @(negedge clk); valid_i=0;

    // Unsupported configuration code 7.
    while(!cfg_ready_o) @(negedge clk);
    cfg_mode_i=3'd7; cfg_valid_i=1; @(posedge clk); #0.01;
    if(!cfg_error_o) begin $display("missing cfg_error"); failures=failures+1; end
    @(negedge clk); cfg_valid_i=0;

    // Legal configuration, then data before required clear.
    while(!cfg_ready_o) @(negedge clk);
    cfg_mode_i=3'd0; cfg_valid_i=1; @(negedge clk); cfg_valid_i=0;
    valid_i=1; @(posedge clk); expect_protocol_error("data before clear"); @(negedge clk); valid_i=0;

    // Illegal valid + clear.
    valid_i=1; clear_i=1; @(posedge clk); expect_protocol_error("valid plus clear"); @(negedge clk); valid_i=0; clear_i=0;

    // Illegal last without valid.
    last_i=1; @(posedge clk); expect_protocol_error("last without valid"); @(negedge clk); last_i=0;

    // Legal clear. Data may follow on the immediately next cycle because the
    // clear and data events remain ordered in the fixed-latency pipeline.
    clear_i=1; @(negedge clk); clear_i=0;

    // Continuous II=1 input, last on second beat.
    if(!in_ready_o) begin $display("not ready one cycle after clear"); failures=failures+1; end
    lhs_packed_i=128'h1; rhs_packed_i=128'h1; valid_i=1; last_i=0; @(negedge clk);
    if(!in_ready_o) begin $display("II=1 violated"); failures=failures+1; end
    lhs_packed_i=128'h2; rhs_packed_i=128'h2; valid_i=1; last_i=1; @(negedge clk);
    valid_i=0; last_i=0;

    // While data is in flight, configuration must not be ready.
    if(cfg_ready_o) begin $display("cfg_ready asserted while busy"); failures=failures+1; end
    wait(int_last_o); @(negedge clk);
    repeat(5) @(negedge clk);
    if(!saw_clear_done) begin $display("clear_done missing"); failures=failures+1; end

    // Last closes transaction; data before another clear is rejected.
    valid_i=1; @(posedge clk); expect_protocol_error("data after last before clear"); @(negedge clk); valid_i=0;

    if(failures==0) $display("PASS protocol failures=0"); else $display("FAIL protocol failures=%0d",failures);
    $finish;
  end
endmodule

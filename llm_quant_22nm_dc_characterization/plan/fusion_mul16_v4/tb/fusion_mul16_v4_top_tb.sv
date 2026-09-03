`timescale 1ns/1ps
module fusion_mul16_v4_top_tb;
  localparam int MAX_BEATS=128;
  logic clk=0,rst_n=0;
  logic cfg_valid_i; logic [2:0] cfg_mode_i; logic cfg_ready_o,cfg_error_o;
  logic valid_i,in_ready_o,clear_i,last_i;
  logic [127:0] lhs_packed_i,rhs_packed_i;
  logic busy_o,protocol_error_o,int_valid_o,int_last_o,fp_valid_o,fp_last_o,clear_done_o;
  logic signed [47:0] int_acc_o[0:3]; logic [31:0] fp_acc_o[0:3]; logic [7:0] fp_status_o[0:3]; logic [2:0] active_mode_o;
  logic [255:0] vectors[0:MAX_BEATS-1];
  string vector_file,result_kind; integer mode,beats,latency_stages,clear_latency_stages;
  logic [47:0] exp_int[0:3]; logic [31:0] exp_fp[0:3];
  integer lane,idx,cycle_count,last_accept_cycle,clear_accept_cycle,failures;
  logic saw_last,saw_clear;
  always #0.5 clk=~clk;

  fusion_mul16_v4 #(.INT_ACC_W(48),.SUPPORT_SPECIALS(1'b0),.IEEE_COMPLIANCE(0)) dut(.*);

  always @(posedge clk) begin
    cycle_count <= cycle_count+1;
    #0.01;
    if(clear_done_o) begin
      saw_clear<=1'b1;
      if((cycle_count-clear_accept_cycle+1)!=clear_latency_stages) begin
        $display("CLEAR latency got=%0d expected=%0d",cycle_count-clear_accept_cycle+1,clear_latency_stages); failures<=failures+1;
      end
    end
    if(int_last_o||fp_last_o) begin
      saw_last<=1'b1;
      if((cycle_count-last_accept_cycle+1)!=latency_stages) begin
        $display("LAST latency got=%0d expected=%0d",cycle_count-last_accept_cycle+1,latency_stages); failures<=failures+1;
      end
    end
    if(protocol_error_o||cfg_error_o) begin
      $display("protocol/config error"); failures<=failures+1;
    end
  end

  initial begin
    if(!$value$plusargs("VECTORS=%s",vector_file)) $fatal(1,"missing VECTORS");
    if(!$value$plusargs("MODE=%d",mode)) $fatal(1,"missing MODE");
    if(!$value$plusargs("BEATS=%d",beats)) $fatal(1,"missing BEATS");
    if(!$value$plusargs("KIND=%s",result_kind)) $fatal(1,"missing KIND");
    if(!$value$plusargs("LAT=%d",latency_stages)) $fatal(1,"missing LAT");
    if(!$value$plusargs("CLAT=%d",clear_latency_stages)) $fatal(1,"missing CLAT");
    for(lane=0;lane<4;lane=lane+1) begin
      if(!$value$plusargs($sformatf("INT%0d=%%h",lane),exp_int[lane])) $fatal(1,"missing INT");
      if(!$value$plusargs($sformatf("FP%0d=%%h",lane),exp_fp[lane])) $fatal(1,"missing FP");
    end
    $readmemh(vector_file,vectors);
    cfg_valid_i=0; cfg_mode_i=0; valid_i=0; clear_i=0; last_i=0; lhs_packed_i=0; rhs_packed_i=0;
    cycle_count=0; last_accept_cycle=0; clear_accept_cycle=0; failures=0; saw_last=0; saw_clear=0;
    repeat(5) @(negedge clk); rst_n=1;

    @(negedge clk); while(!cfg_ready_o) @(negedge clk);
    cfg_mode_i=mode[2:0]; cfg_valid_i=1;
    @(negedge clk); cfg_valid_i=0;

    while(!in_ready_o) @(negedge clk);
    clear_i=1; clear_accept_cycle=cycle_count+1;
    @(negedge clk); clear_i=0;
    wait(clear_done_o===1'b1); @(negedge clk);

    for(idx=0;idx<beats;idx=idx+1) begin
      while(!in_ready_o) @(negedge clk);
      lhs_packed_i=vectors[idx][255:128]; rhs_packed_i=vectors[idx][127:0];
      valid_i=1; last_i=(idx==beats-1);
      if(idx==beats-1) last_accept_cycle=cycle_count+1;
      @(negedge clk);
    end
    valid_i=0; last_i=0; lhs_packed_i=0; rhs_packed_i=0;
    repeat(16) @(negedge clk);
    if(!saw_clear) begin $display("clear_done missing"); failures=failures+1; end
    if(!saw_last) begin $display("last missing"); failures=failures+1; end
    for(lane=0;lane<4;lane=lane+1) begin
      if(result_kind=="int" && int_acc_o[lane]!==exp_int[lane]) begin
        $display("INT mismatch lane=%0d got=%h exp=%h",lane,int_acc_o[lane],exp_int[lane]); failures=failures+1;
      end
      if(result_kind=="fp" && fp_acc_o[lane]!==exp_fp[lane]) begin
        $display("FP mismatch lane=%0d got=%h exp=%h",lane,fp_acc_o[lane],exp_fp[lane]); failures=failures+1;
      end
    end
    if(failures==0) $display("PASS mode=%0d beats=%0d",mode,beats);
    else $display("FAIL failures=%0d",failures);
    $finish;
  end
endmodule

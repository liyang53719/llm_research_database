// Area upper-bound surrogate for FP4 E2M1.
//
// The installed DW_fp_mac implementation does not support E2M1 or E2M2. Map
// each E2M1 operand into the minimum supported E3M2 encoding, perform the MAC
// in E3M2, then truncate/saturate back to E2M1. This is not a bit-exact FP4
// arithmetic implementation and results must remain labeled as a padded
// DesignWare surrogate.
module fp4_e2m1_mac_dw_surrogate (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic [3:0] a_i,
  input  logic [3:0] b_i,
  input  logic [3:0] c_i,
  input  logic [2:0] rnd_i,
  output logic valid_o,
  output logic [3:0] z_o,
  output logic [7:0] status_o
);
  logic [5:0] a_e3m2;
  logic [5:0] b_e3m2;
  logic [5:0] c_e3m2;
  logic [5:0] z_e3m2;
  logic [7:0] status_comb;

  function automatic logic [5:0] fp4_to_fp6(input logic [3:0] value);
    case (value[2:1])
      2'b00: fp4_to_fp6 = value[0] ? {value[3], 3'b010, 2'b00} : {value[3], 5'b0};
      2'b01: fp4_to_fp6 = {value[3], 3'b011, value[0], 1'b0};
      2'b10: fp4_to_fp6 = {value[3], 3'b100, value[0], 1'b0};
      default: fp4_to_fp6 = {value[3], 3'b111, value[0], 1'b0};
    endcase
  endfunction

  function automatic logic [3:0] fp6_to_fp4(input logic [5:0] value);
    case (value[4:2])
      3'b000, 3'b001: fp6_to_fp4 = {value[5], 3'b000};
      3'b010: fp6_to_fp4 = {value[5], 3'b001};
      3'b011: fp6_to_fp4 = {value[5], 2'b01, value[1]};
      3'b100: fp6_to_fp4 = {value[5], 2'b10, value[1]};
      3'b111: fp6_to_fp4 = {value[5], 2'b11, |value[1:0]};
      default: fp6_to_fp4 = {value[5], 3'b110};
    endcase
  endfunction

  always_comb begin
    a_e3m2 = fp4_to_fp6(a_i);
    b_e3m2 = fp4_to_fp6(b_i);
    c_e3m2 = fp4_to_fp6(c_i);
  end

  DW_fp_mac #(2, 3, 0) u_dw_fp_mac (
    .a(a_e3m2),
    .b(b_e3m2),
    .c(c_e3m2),
    .rnd(rnd_i),
    .z(z_e3m2),
    .status(status_comb)
  );

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      z_o      <= '0;
      status_o <= '0;
      valid_o  <= 1'b0;
    end else begin
      z_o      <= fp6_to_fp4(z_e3m2);
      status_o <= status_comb;
      valid_o  <= valid_i;
    end
  end
endmodule

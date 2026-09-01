// Conversion-based mixed MAC. INT operands use DW_fp_i2flt and then a
// same-format DW_fp_mac. INT4->FP8 and INT4/INT8->BF16 are exact input
// conversions; INT8->FP8 is not exact.
module hybrid_convert_fp_mac_dw #(
  parameter int SIG_WIDTH = 3,
  parameter int EXP_WIDTH = 4,
  parameter int IEEE_COMPLIANCE = 0,
  parameter int INT_WIDTH = 8
) (
  input logic clk, rst_n, valid_i,
  input logic [1:0] a_format_i, b_format_i,
  input logic [15:0] a_bits_i, b_bits_i,
  input logic [SIG_WIDTH+EXP_WIDTH:0] acc_i,
  input logic [2:0] rnd_i,
  output logic valid_o,
  output logic [SIG_WIDTH+EXP_WIDTH:0] z_o,
  output logic [7:0] status_o
);
  localparam int FP_W = SIG_WIDTH + EXP_WIDTH + 1;
  logic [INT_WIDTH-1:0] a_int, b_int;
  logic [FP_W-1:0] a_int_fp, b_int_fp, a_fp, b_fp, z_comb;
  logic [7:0] a_status, b_status, mac_status;

  assign a_int = a_bits_i[INT_WIDTH-1:0];
  assign b_int = b_bits_i[INT_WIDTH-1:0];

  DW_fp_i2flt #(SIG_WIDTH, EXP_WIDTH, INT_WIDTH, 1) u_a_i2f (
    .a(a_int), .rnd(rnd_i), .z(a_int_fp), .status(a_status)
  );
  DW_fp_i2flt #(SIG_WIDTH, EXP_WIDTH, INT_WIDTH, 1) u_b_i2f (
    .a(b_int), .rnd(rnd_i), .z(b_int_fp), .status(b_status)
  );

  always_comb begin
    a_fp = (a_format_i <= 2'd1) ? a_int_fp : a_bits_i[FP_W-1:0];
    b_fp = (b_format_i <= 2'd1) ? b_int_fp : b_bits_i[FP_W-1:0];
  end

  DW_fp_mac #(SIG_WIDTH, EXP_WIDTH, IEEE_COMPLIANCE) u_mac (
    .a(a_fp), .b(b_fp), .c(acc_i), .rnd(rnd_i), .z(z_comb), .status(mac_status)
  );

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_o <= 1'b0; z_o <= '0; status_o <= '0;
    end else begin
      valid_o <= valid_i; z_o <= z_comb;
      status_o <= mac_status | a_status | b_status;
    end
  end
endmodule

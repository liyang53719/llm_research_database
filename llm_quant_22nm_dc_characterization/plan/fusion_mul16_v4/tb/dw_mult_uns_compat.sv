// Simulation-only compatibility model for the unsigned 4x4 DesignWare
// primitive.  The installed DWBB release exposes DW02_mult.v but does not
// ship a DW_mult_uns Verilog simulation model; DC still resolves the native
// DW_mult_uns operator from its synthetic library.  This shim preserves the
// exact unsigned product semantics for VCS without changing synthesizable RTL.
module DW_mult_uns #(
  parameter integer a_width = 8,
  parameter integer b_width = 8
) (
  input  logic [a_width-1:0] a,
  input  logic [b_width-1:0] b,
  output logic [a_width+b_width-1:0] product
);
  assign product = a * b;
endmodule

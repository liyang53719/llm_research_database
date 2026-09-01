module DW_mult_uns #(
  parameter integer a_width = 4,
  parameter integer b_width = 4
) (
  input  logic [a_width-1:0] a,
  input  logic [b_width-1:0] b,
  output logic [a_width+b_width-1:0] product
);
  assign product = a * b;
endmodule

module mul4x4_brick (
  input  logic [3:0] a_i,
  input  logic [3:0] b_i,
  output logic [7:0] p_o
);
`ifdef FUSION_USE_DW
  DW_mult_uns #(4, 4) u_dw_mult (
    .a(a_i),
    .b(b_i),
    .product(p_o)
  );
`else
  assign p_o = a_i * b_i;
`endif
endmodule

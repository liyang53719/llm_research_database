module mul4x4_array16_proof (
  input  logic clk,
  input  logic rst_n,
  input  logic [3:0] a_i [0:15],
  input  logic [3:0] b_i [0:15],
  output logic [7:0] p_o [0:15]
);
  logic [7:0] p_comb [0:15];
  integer i;
  genvar g;
  generate
    for (g = 0; g < 16; g = g + 1) begin : G_BRICK
      mul4x4_brick u_brick (.a_i(a_i[g]), .b_i(b_i[g]), .p_o(p_comb[g]));
    end
  endgenerate
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      for (i = 0; i < 16; i = i + 1)
        p_o[i] <= '0;
    else
      for (i = 0; i < 16; i = i + 1)
        p_o[i] <= p_comb[i];
  end
endmodule

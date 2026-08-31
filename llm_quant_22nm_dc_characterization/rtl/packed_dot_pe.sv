module packed_dot_pe #(
  parameter int W_W = 4,
  parameter int A_W = 8,
  parameter int LANES = 4,
  parameter int ACC_W = 40
) (
  input  logic clk,
  input  logic rst_n,
  input  logic valid_i,
  input  logic clear_i,
  input  logic signed [LANES*W_W-1:0] w_vec_i,
  input  logic signed [LANES*A_W-1:0] a_vec_i,
  output logic valid_o,
  output logic signed [ACC_W-1:0] acc_o
);
  integer i;
  logic signed [ACC_W-1:0] dot_comb;
  logic signed [W_W-1:0] w_lane;
  logic signed [A_W-1:0] a_lane;

  always_comb begin
    dot_comb = '0;
    w_lane = '0;
    a_lane = '0;
    for (i = 0; i < LANES; i = i + 1) begin
      w_lane = $signed(w_vec_i[i*W_W +: W_W]);
      a_lane = $signed(a_vec_i[i*A_W +: A_W]);
      dot_comb = dot_comb + w_lane * a_lane;
    end
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      acc_o   <= '0;
      valid_o <= 1'b0;
    end else begin
      valid_o <= valid_i;
      if (clear_i)
        acc_o <= '0;
      else if (valid_i)
        acc_o <= acc_o + dot_comb;
    end
  end
endmodule

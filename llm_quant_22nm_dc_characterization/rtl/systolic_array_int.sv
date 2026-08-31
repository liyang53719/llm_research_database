module systolic_array_int #(
  parameter int ROWS = 4,
  parameter int COLS = 4,
  parameter int W_W = 4,
  parameter int A_W = 8,
  parameter int ACC_W = 28
) (
  input  logic clk,
  input  logic rst_n,
  input  logic clear_i,
  input  logic signed [ROWS*A_W-1:0] a_left_i,
  input  logic signed [COLS*W_W-1:0] w_top_i,
  output logic [ACC_W-1:0] signature_o
);
  logic signed [A_W-1:0] a_pipe [0:ROWS-1][0:COLS-1];
  logic signed [W_W-1:0] w_pipe [0:ROWS-1][0:COLS-1];
  logic signed [ACC_W-1:0] acc [0:ROWS-1][0:COLS-1];
  integer r, c;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      for (r = 0; r < ROWS; r = r + 1)
        for (c = 0; c < COLS; c = c + 1) begin
          a_pipe[r][c] <= '0;
          w_pipe[r][c] <= '0;
          acc[r][c] <= '0;
        end
    end else begin
      for (r = 0; r < ROWS; r = r + 1)
        for (c = 0; c < COLS; c = c + 1) begin
          if (c == 0)
            a_pipe[r][c] <= $signed(a_left_i[r*A_W +: A_W]);
          else
            a_pipe[r][c] <= a_pipe[r][c-1];

          if (r == 0)
            w_pipe[r][c] <= $signed(w_top_i[c*W_W +: W_W]);
          else
            w_pipe[r][c] <= w_pipe[r-1][c];

          if (clear_i)
            acc[r][c] <= '0;
          else
            acc[r][c] <= acc[r][c] + a_pipe[r][c] * w_pipe[r][c];
        end
    end
  end

  always_comb begin
    signature_o = '0;
    for (r = 0; r < ROWS; r = r + 1)
      for (c = 0; c < COLS; c = c + 1)
        signature_o = signature_o ^ acc[r][c];
  end
endmodule

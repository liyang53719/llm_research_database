module systolic_array_fp_dw #(
  parameter int ROWS = 4,
  parameter int COLS = 4,
  parameter int SIG_WIDTH = 7,
  parameter int EXP_WIDTH = 8,
  parameter int IEEE_COMPLIANCE = 0
) (
  input  logic clk,
  input  logic rst_n,
  input  logic clear_i,
  input  logic [(SIG_WIDTH+EXP_WIDTH+1)*ROWS-1:0] a_left_i,
  input  logic [(SIG_WIDTH+EXP_WIDTH+1)*COLS-1:0] b_top_i,
  input  logic [2:0] rnd_i,
  output logic [SIG_WIDTH+EXP_WIDTH:0] signature_o
);
  localparam int FP_W = SIG_WIDTH + EXP_WIDTH + 1;
  logic [FP_W-1:0] a_pipe [0:ROWS-1][0:COLS-1];
  logic [FP_W-1:0] b_pipe [0:ROWS-1][0:COLS-1];
  logic [FP_W-1:0] acc [0:ROWS-1][0:COLS-1];
  logic [FP_W-1:0] z_comb [0:ROWS-1][0:COLS-1];
  logic [7:0] status_unused [0:ROWS-1][0:COLS-1];
  integer r, c;
  genvar gr, gc;

  generate
    for (gr = 0; gr < ROWS; gr = gr + 1) begin : G_R
      for (gc = 0; gc < COLS; gc = gc + 1) begin : G_C
        DW_fp_mac #(SIG_WIDTH, EXP_WIDTH, IEEE_COMPLIANCE) u_mac (
          .a(a_pipe[gr][gc]),
          .b(b_pipe[gr][gc]),
          .c(acc[gr][gc]),
          .rnd(rnd_i),
          .z(z_comb[gr][gc]),
          .status(status_unused[gr][gc])
        );
      end
    end
  endgenerate

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      for (r = 0; r < ROWS; r = r + 1)
        for (c = 0; c < COLS; c = c + 1) begin
          a_pipe[r][c] <= '0;
          b_pipe[r][c] <= '0;
          acc[r][c] <= '0;
        end
    end else begin
      for (r = 0; r < ROWS; r = r + 1)
        for (c = 0; c < COLS; c = c + 1) begin
          if (c == 0)
            a_pipe[r][c] <= a_left_i[r*FP_W +: FP_W];
          else
            a_pipe[r][c] <= a_pipe[r][c-1];

          if (r == 0)
            b_pipe[r][c] <= b_top_i[c*FP_W +: FP_W];
          else
            b_pipe[r][c] <= b_pipe[r-1][c];

          if (clear_i)
            acc[r][c] <= '0;
          else
            acc[r][c] <= z_comb[r][c];
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

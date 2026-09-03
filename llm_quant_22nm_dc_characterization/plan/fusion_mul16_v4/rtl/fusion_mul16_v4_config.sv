module fusion_mul16_v4_config #(
  parameter int FIXED_MODE = -1,
  parameter bit SUPPORT_FP8 = 1'b1,
  parameter bit SUPPORT_BF16 = 1'b1,
  parameter bit SUPPORT_I4_FP8 = 1'b1,
  parameter bit SUPPORT_I4_BF16 = 1'b1,
  parameter bit SUPPORT_I8_BF16 = 1'b1,
  parameter int INFLIGHT_DEPTH = 8
) (
  input  logic clk,
  input  logic rst_n,
  input  logic cfg_valid_i,
  input  logic [2:0] cfg_mode_i,
  output logic cfg_ready_o,
  output logic cfg_error_o,
  input  logic valid_i,
  input  logic clear_i,
  input  logic last_i,
  output logic in_ready_o,
  output logic accept_data_o,
  output logic accept_clear_o,
  output logic protocol_error_o,
  output logic busy_o,
  output logic [2:0] active_mode_o,
  output logic [6:0] active_onehot_o
);
  import fusion_mul16_v4_pkg::*;

  logic [2:0] mode_q;
  logic [6:0] onehot_q;
  logic cfg_loaded_q;
  logic needs_clear_q;
  logic [INFLIGHT_DEPTH-1:0] inflight_q;
  logic selected_mode_supported;
  logic configuration_beat;
  logic event_accept;
  logic protocol_error_w;

  always_comb begin
    selected_mode_supported = 1'b0;
    case (cfg_mode_i)
      MODE_I4_I8, MODE_I8_I8: selected_mode_supported = 1'b1;
      MODE_FP8_FP8:           selected_mode_supported = SUPPORT_FP8;
      MODE_BF16_BF16:         selected_mode_supported = SUPPORT_BF16;
      MODE_I4_FP8:            selected_mode_supported = SUPPORT_I4_FP8;
      MODE_I4_BF16:           selected_mode_supported = SUPPORT_I4_BF16;
      MODE_I8_BF16:           selected_mode_supported = SUPPORT_I8_BF16;
      default:                 selected_mode_supported = 1'b0;
    endcase
  end

  generate
    if (FIXED_MODE >= 0) begin : G_FIXED
      always_comb begin
        cfg_ready_o = 1'b0;
        cfg_error_o = cfg_valid_i;
        configuration_beat = 1'b0;
        active_mode_o = FIXED_MODE[2:0];
        active_onehot_o = mode_to_onehot(FIXED_MODE[2:0]);
        in_ready_o = 1'b1;
      end
    end else begin : G_DYNAMIC
      always_comb begin
        cfg_ready_o = !(|inflight_q);
        configuration_beat = cfg_valid_i && cfg_ready_o;
        cfg_error_o = configuration_beat && !selected_mode_supported;
        active_mode_o = mode_q;
        active_onehot_o = onehot_q;
        in_ready_o = cfg_loaded_q && !configuration_beat;
      end
    end
  endgenerate

  always_comb begin
    accept_clear_o = clear_i && !valid_i && in_ready_o;
    accept_data_o = valid_i && !clear_i && in_ready_o && !needs_clear_q;
    protocol_error_w = (valid_i && clear_i)
                     || (last_i && !valid_i)
                     || (valid_i && needs_clear_q)
                     || ((valid_i || clear_i) && !in_ready_o && !configuration_beat)
                     || ((valid_i || clear_i) && configuration_beat);
    event_accept = accept_data_o || accept_clear_o;
    busy_o = |inflight_q;
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mode_q <= MODE_I4_I8;
      onehot_q <= mode_to_onehot(MODE_I4_I8);
      cfg_loaded_q <= (FIXED_MODE >= 0);
      needs_clear_q <= 1'b0;
      inflight_q <= '0;
      protocol_error_o <= 1'b0;
    end else begin
      // Register the error decision at the accepting edge.  This prevents a
      // legal last beat from becoming an apparent error after the sequential
      // logic raises needs_clear_q for the following transaction.
      protocol_error_o <= protocol_error_w;
      inflight_q <= {inflight_q[INFLIGHT_DEPTH-2:0], event_accept};
      if ((FIXED_MODE < 0) && configuration_beat && selected_mode_supported) begin
        mode_q <= cfg_mode_i;
        onehot_q <= mode_to_onehot(cfg_mode_i);
        cfg_loaded_q <= 1'b1;
        needs_clear_q <= 1'b1;
      end else if (accept_clear_o) begin
        needs_clear_q <= 1'b0;
      end else if (accept_data_o && last_i) begin
        needs_clear_q <= 1'b1;
      end
    end
  end
endmodule

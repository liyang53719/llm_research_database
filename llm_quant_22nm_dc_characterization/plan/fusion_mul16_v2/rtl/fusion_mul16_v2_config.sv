module fusion_mul16_v2_config #(
  parameter int FIXED_MODE = -1,
  parameter bit SUPPORT_FP8 = 1'b1,
  parameter bit SUPPORT_BF16 = 1'b1,
  parameter bit SUPPORT_I4_FP8 = 1'b1,
  parameter bit SUPPORT_I4_BF16 = 1'b1,
  parameter bit SUPPORT_I8_BF16 = 1'b1,
  parameter int INFLIGHT_DEPTH = 10
) (
  input  logic clk,
  input  logic rst_n,
  input  logic cfg_valid_i,
  input  logic [2:0] cfg_mode_i,
  input  logic [2:0] cfg_rnd_i,
  output logic cfg_ready_o,
  output logic cfg_error_o,
  input  logic valid_i,
  output logic accept_data_o,
  output logic [2:0] active_mode_o,
  output logic [6:0] active_onehot_o,
  output logic [2:0] active_rnd_o
);
  import fusion_mul16_v2_pkg::*;

  logic [2:0] mode_q;
  logic [6:0] mode_onehot_q;
  logic [2:0] rnd_q;
  logic cfg_loaded_q;
  logic [INFLIGHT_DEPTH-1:0] inflight_q;
  logic selected_mode_supported;
  logic configuration_beat;

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
        cfg_error_o = 1'b0;
        accept_data_o = valid_i;
        active_mode_o = FIXED_MODE[2:0];
        active_onehot_o = mode_to_onehot(FIXED_MODE[2:0]);
        active_rnd_o = 3'b000;
        configuration_beat = 1'b0;
      end
    end else begin : G_DYNAMIC
      always_comb begin
        cfg_ready_o = !(|inflight_q);
        configuration_beat = cfg_valid_i && cfg_ready_o;
        cfg_error_o = configuration_beat && !selected_mode_supported;
        // A configuration beat has priority over data. Data in the same cycle
        // is not accepted under the previous tile mode.
        accept_data_o = valid_i && cfg_loaded_q && !configuration_beat;
        active_mode_o = mode_q;
        active_onehot_o = mode_onehot_q;
        active_rnd_o = rnd_q;
      end
    end
  endgenerate

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mode_q <= MODE_I4_I8;
      mode_onehot_q <= mode_to_onehot(MODE_I4_I8);
      rnd_q <= 3'b000;
      cfg_loaded_q <= (FIXED_MODE >= 0);
      inflight_q <= '0;
    end else begin
      inflight_q <= {inflight_q[INFLIGHT_DEPTH-2:0], accept_data_o};
      if ((FIXED_MODE < 0) && configuration_beat && selected_mode_supported) begin
        mode_q <= cfg_mode_i;
        mode_onehot_q <= mode_to_onehot(cfg_mode_i);
        rnd_q <= cfg_rnd_i;
        cfg_loaded_q <= 1'b1;
      end
    end
  end
endmodule

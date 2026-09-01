// Width-compatible simulation stubs used only for open-source structural
// compilation. Real synthesis must resolve these modules from DesignWare.
module DW_fp_mac #(
  parameter int sig_width=23, exp_width=8, ieee_compliance=0
) (
  input logic [sig_width+exp_width:0] a,b,c,
  input logic [2:0] rnd,
  output logic [sig_width+exp_width:0] z,
  output logic [7:0] status
);
  assign z='0; assign status='0;
endmodule

module DW_fp_i2flt #(
  parameter int sig_width=23, exp_width=8, isize=32, isign=1
) (
  input logic [isize-1:0] a,
  input logic [2:0] rnd,
  output logic [sig_width+exp_width:0] z,
  output logic [7:0] status
);
  assign z='0; assign status='0;
endmodule

module DW_fp_add #(
  parameter int sig_width=23, exp_width=8, ieee_compliance=0
) (
  input logic [sig_width+exp_width:0] a,b,
  input logic [2:0] rnd,
  output logic [sig_width+exp_width:0] z,
  output logic [7:0] status
);
  assign z=b; assign status='0;
endmodule

module DW_fp_mult #(
  parameter int sig_width=23, exp_width=8, ieee_compliance=0
) (
  input logic [sig_width+exp_width:0] a,b,
  input logic [2:0] rnd,
  output logic [sig_width+exp_width:0] z,
  output logic [7:0] status
);
  assign z='0; assign status='0;
endmodule

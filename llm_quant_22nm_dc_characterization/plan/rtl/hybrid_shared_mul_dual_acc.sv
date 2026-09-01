// Experimental native-shared candidate.
// Shares one unsigned 8x8 magnitude/significand multiplier.
// Integer pairs use INT40 accumulation; floating-containing pairs use FP32 accumulation.
// This is a DSE RTL candidate, not IEEE signoff RTL.
module hybrid_shared_mul_dual_acc #(
  parameter int INT_ACC_W=40,
  parameter bit ENABLE_FP8=1'b1,
  parameter bit ENABLE_BF16=1'b1,
  parameter bit PIPELINE_PRODUCT=1'b0
) (
  input logic clk,rst_n,valid_i,clear_i,
  input logic [1:0] a_format_i,b_format_i,
  input logic [15:0] a_bits_i,b_bits_i,
  input logic [2:0] rnd_i,
  output logic valid_o,
  output logic signed [INT_ACC_W-1:0] int_acc_o,
  output logic [31:0] fp_acc_o,
  output logic [7:0] fp_status_o
);
  logic [7:0] a_mag,b_mag;
  logic a_sign,b_sign;
  logic signed [11:0] a_scale,b_scale;
  logic [15:0] magnitude_product;
  logic product_sign;
  logic int_mode;
  logic signed [16:0] signed_product;
  logic [31:0] product_fp32,fp_sum;
  logic [7:0] fp_status;
  integer product_msb;
  integer i;
  logic [15:0] normalized;
  logic signed [12:0] unbiased_exp;
  logic signed [13:0] product_exp;
  logic [7:0] biased_exp;
  logic a_zero,b_zero,a_inf,b_inf,a_nan,b_nan;
  logic [31:0] subnormal_fraction;
  integer subnormal_shift;
  logic [31:0] product_fp32_q,fp_add_operand;
  logic signed [16:0] signed_product_q;
  logic int_mode_q,valid_q,clear_q;

  task automatic decode_operand(
    input logic [1:0] fmt,input logic [15:0] bits,
    output logic sign,output logic [7:0] magnitude,
    output logic signed [11:0] scale_exp,
    output logic is_zero,output logic is_inf,output logic is_nan
  );
    logic signed [8:0] iv;
    logic [3:0] e4; logic [2:0] m3;
    begin
      sign=1'b0; magnitude='0; scale_exp='0; iv='0; e4='0; m3='0;
      is_zero=1'b0; is_inf=1'b0; is_nan=1'b0;
      if(fmt==2'd0) begin
        iv={{5{bits[3]}},bits[3:0]}; sign=iv[8]; magnitude=sign ? -iv : iv;
        is_zero=(magnitude==0);
      end else if(fmt==2'd1) begin
        iv={bits[7],bits[7:0]}; sign=iv[8]; magnitude=sign ? -iv : iv;
        is_zero=(magnitude==0);
      end else if((fmt==2'd2) && ENABLE_FP8) begin
        sign=bits[7]; e4=bits[6:3]; m3=bits[2:0];
        if((e4==0) && (m3==0)) is_zero=1'b1;
        else if((e4==4'hf) && (m3==3'h7)) is_nan=1'b1;
        else if(e4==0) begin magnitude={m3,5'b0}; scale_exp=-14; end
        else begin magnitude={1'b1,m3,4'b0}; scale_exp=$signed({1'b0,e4})-14; end
      end else if((fmt==2'd3) && ENABLE_BF16) begin
        sign=bits[15];
        if((bits[14:7]==0) && (bits[6:0]==0)) is_zero=1'b1;
        else if(bits[14:7]==8'hff) begin
          is_inf=(bits[6:0]==0); is_nan=(bits[6:0]!=0);
        end else if(bits[14:7]==0) begin
          magnitude={1'b0,bits[6:0]}; scale_exp=-133;
        end else begin
          magnitude={1'b1,bits[6:0]};
          scale_exp=$signed({1'b0,bits[14:7]})-134;
        end
      end else begin
        is_zero=1'b1;
      end
    end
  endtask

  always_comb begin
    decode_operand(a_format_i,a_bits_i,a_sign,a_mag,a_scale,a_zero,a_inf,a_nan);
    decode_operand(b_format_i,b_bits_i,b_sign,b_mag,b_scale,b_zero,b_inf,b_nan);
    magnitude_product=a_mag*b_mag;
    product_sign=a_sign^b_sign;
    int_mode=(a_format_i<=2'd1)&&(b_format_i<=2'd1);
    signed_product=product_sign ? -$signed({1'b0,magnitude_product})
                                :  $signed({1'b0,magnitude_product});
    product_msb=0;
    for(i=0;i<16;i=i+1) if(magnitude_product[i]) product_msb=i;
    normalized=magnitude_product<<(15-product_msb);
    product_exp=product_msb+a_scale+b_scale;
    unbiased_exp=product_exp;
    biased_exp=product_exp+127;
    subnormal_fraction='0;
    subnormal_shift=a_scale+b_scale+149;
    if(subnormal_shift>=0)
      subnormal_fraction=magnitude_product<<subnormal_shift;
    else
      subnormal_fraction=magnitude_product>>(-subnormal_shift);
    if(a_nan || b_nan || ((a_zero || b_zero) && (a_inf || b_inf)))
      product_fp32=32'h7fc00000;
    else if(a_inf || b_inf)
      product_fp32={product_sign,8'hff,23'b0};
    else if(a_zero || b_zero || product_exp < -149)
      product_fp32={product_sign,31'b0};
    else if(product_exp < -126)
      product_fp32={product_sign,8'h00,subnormal_fraction[22:0]};
    else if(product_exp > 127)
      product_fp32={product_sign,8'hff,23'b0};
    else
      product_fp32={product_sign,biased_exp,normalized[14:0],8'b0};
  end

  assign fp_add_operand=PIPELINE_PRODUCT?product_fp32_q:product_fp32;
  DW_fp_add #(23,8,0) u_fp_add(
    .a(fp_acc_o),.b(fp_add_operand),.rnd(rnd_i),.z(fp_sum),.status(fp_status)
  );

  generate
    if(PIPELINE_PRODUCT) begin : G_PIPE
      always_ff @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
          valid_o<=1'b0; int_acc_o<='0; fp_acc_o<='0; fp_status_o<='0;
          product_fp32_q<='0; signed_product_q<='0; int_mode_q<=1'b0;
          valid_q<=1'b0; clear_q<=1'b0;
        end else begin
          product_fp32_q<=product_fp32; signed_product_q<=signed_product;
          int_mode_q<=int_mode; valid_q<=valid_i; clear_q<=clear_i;
          valid_o<=valid_q;
          if(clear_q) begin int_acc_o<='0; fp_acc_o<='0; fp_status_o<='0; end
          else if(valid_q) begin
            if(int_mode_q)
              int_acc_o<=int_acc_o+{{(INT_ACC_W-17){signed_product_q[16]}},signed_product_q};
            else begin fp_acc_o<=fp_sum; fp_status_o<=fp_status; end
          end
        end
      end
    end else begin : G_BASE
      always_ff @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
          valid_o<=1'b0; int_acc_o<='0; fp_acc_o<='0; fp_status_o<='0;
        end else begin
          valid_o<=valid_i;
          if(clear_i) begin int_acc_o<='0; fp_acc_o<='0; fp_status_o<='0; end
          else if(valid_i) begin
            if(int_mode)
              int_acc_o<=int_acc_o+{{(INT_ACC_W-17){signed_product[16]}},signed_product};
            else begin fp_acc_o<=fp_sum; fp_status_o<=fp_status; end
          end
        end
      end
    end
  endgenerate
endmodule

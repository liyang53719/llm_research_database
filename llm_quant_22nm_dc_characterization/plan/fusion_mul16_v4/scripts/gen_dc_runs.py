#!/usr/bin/env python3
from __future__ import annotations
import csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def final_wrapper(row):
    if row['fixed_mode'] in {'0','1'}:
        return integer_final_wrapper(row)
    return f'''module char_top(
  input logic clk,rst_n,cfg_valid_i,valid_i,clear_i,last_i,
  input logic [2:0] cfg_mode_i,
  input logic [127:0] lhs_packed_i,rhs_packed_i,
  output logic cfg_ready_o,cfg_error_o,in_ready_o,busy_o,protocol_error_o,
  output logic int_valid_o,int_last_o,fp_valid_o,fp_last_o,clear_done_o,
  output logic [191:0] int_acc_packed_o,
  output logic [127:0] fp_acc_packed_o,
  output logic [31:0] fp_status_packed_o,
  output logic [2:0] active_mode_o
);
  fusion_mul16_v4_flat #(.INT_ACC_W(48),.FIXED_MODE({row['fixed_mode']}),
    .SUPPORT_SPECIALS({row['support_specials']}),.IEEE_COMPLIANCE({row['ieee_compliance']})) u_dut(.*);
endmodule
'''

def integer_final_wrapper(row):
    # Fixed INT4xINT8/I8xI8 characterization observes only the integer bank.
    # Leave floating outputs unconnected at the integration boundary so DC can
    # constant-prune the unused BF16/FP32 datapath; dynamic and FP fixed-mode
    # groups still use the complete flat wrapper above.
    return f'''module char_top(
  input logic clk,rst_n,cfg_valid_i,valid_i,clear_i,last_i,
  input logic [2:0] cfg_mode_i,
  input logic [127:0] lhs_packed_i,rhs_packed_i,
  output logic cfg_ready_o,cfg_error_o,in_ready_o,busy_o,protocol_error_o,
  output logic int_valid_o,int_last_o,fp_valid_o,fp_last_o,clear_done_o,
  output logic [191:0] int_acc_packed_o,
  output logic [127:0] fp_acc_packed_o,
  output logic [31:0] fp_status_packed_o,
  output logic [2:0] active_mode_o
);
  logic [6:0] active_onehot;
  logic accept_data, accept_clear, product_int_valid, product_int_clear;
  logic signed [17:0] int_lane_sum [0:3];
  logic signed [47:0] int_acc [0:3];
  logic int_clear_done;
  fusion_mul16_v4_config #(.FIXED_MODE({row['fixed_mode']})) u_config(
    .clk,.rst_n,.cfg_valid_i,.cfg_mode_i,.cfg_ready_o,.cfg_error_o,
    .valid_i,.clear_i,.last_i,.in_ready_o,.accept_data_o(accept_data),
    .accept_clear_o(accept_clear),.protocol_error_o,.busy_o,
    .active_mode_o,.active_onehot_o(active_onehot));
  fusion_mul16_v4_product_pipe #(.SUPPORT_SPECIALS(0)) u_product_pipe(
    .clk,.rst_n,.valid_i(accept_data),.clear_i(accept_clear),
    .mode_onehot_i(active_onehot),.lhs_packed_i,.rhs_packed_i,
    .int_valid_o(product_int_valid),.int_clear_o(product_int_clear),
    .int_lane_sum_o(int_lane_sum),.fp_valid_o(),.fp_clear_o(),.bf16_lane_item_o());
  fusion_mul16_v4_int_accum #(.ACC_W(48)) u_int_accum(
    .clk,.rst_n,.valid_i(product_int_valid),.clear_i(product_int_clear),
    .lane_sum_i(int_lane_sum),.valid_o(int_valid_o),.clear_done_o(int_clear_done),.acc_o(int_acc));
  genvar g; generate for(g=0;g<4;g=g+1) begin:G_INT_PACK
    assign int_acc_packed_o[g*48+:48]=int_acc[g];
  end endgenerate
  assign int_last_o=1'b0;
  assign fp_valid_o=1'b0;
  assign fp_last_o=1'b0;
  assign clear_done_o=1'b0;
  assign fp_acc_packed_o='0;
  assign fp_status_packed_o='0;
endmodule
'''

def brick_wrapper(row):
    return '''module char_top(
  input logic clk,
  input logic [63:0] a_i,b_i,
  output logic [127:0] product_o
);
  genvar g;
  generate for(g=0;g<16;g=g+1) begin:G
    fusion_mul16_v4_mul4x4_brick u_brick(.a_i(a_i[g*4+:4]),.b_i(b_i[g*4+:4]),.p_o(product_o[g*8+:8]));
  end endgenerate
endmodule
'''

def product_wrapper(row):
    return '''module char_top(
  input logic clk,rst_n,valid_i,clear_i,
  input logic [6:0] mode_onehot_i,
  input logic [127:0] lhs_packed_i,rhs_packed_i,
  output logic int_valid_o,int_clear_o,fp_valid_o,fp_clear_o,
  output logic [71:0] int_lane_packed_o,
  output logic [255:0] bf16_item_packed_o
);
  logic signed [17:0] int_lane[0:3]; logic [15:0] item[0:3][0:3];
  fusion_mul16_v4_product_pipe #(.SUPPORT_SPECIALS(0)) u_dut(
    .clk,.rst_n,.valid_i,.clear_i,.mode_onehot_i,.lhs_packed_i,.rhs_packed_i,
    .int_valid_o,.int_clear_o,.int_lane_sum_o(int_lane),.fp_valid_o,.fp_clear_o,.bf16_lane_item_o(item));
  genvar l,i; generate for(l=0;l<4;l=l+1) begin:GL
    assign int_lane_packed_o[l*18+:18]=int_lane[l];
    for(i=0;i<4;i=i+1) begin:GI assign bf16_item_packed_o[(l*4+i)*16+:16]=item[l][i]; end
  end endgenerate
endmodule
'''

def accum_wrapper(row):
    return '''module char_top(
  input logic clk,rst_n,valid_i,clear_i,
  input logic [255:0] lane_item_packed_i,
  output logic valid_o,clear_done_o,
  output logic [127:0] acc_packed_o,
  output logic [31:0] status_packed_o
);
  logic [15:0] item[0:3][0:3]; logic [31:0] acc[0:3]; logic [7:0] status[0:3];
  genvar l,i; generate for(l=0;l<4;l=l+1) begin:GL
    for(i=0;i<4;i=i+1) begin:GI assign item[l][i]=lane_item_packed_i[(l*4+i)*16+:16]; end
    assign acc_packed_o[l*32+:32]=acc[l]; assign status_packed_o[l*8+:8]=status[l];
  end endgenerate
  fusion_mul16_v4_fp32_recurrent_accum_dw #(.IEEE_COMPLIANCE(0)) u_dut(
    .clk,.rst_n,.valid_i,.clear_i,.lane_item_i(item),.rnd_i(3'b000),
    .valid_o,.clear_done_o,.acc_fp32_o(acc),.status_o(status));
endmodule
'''

def main():
    cfg=json.loads((ROOT/'config/characterization_1ghz.json').read_text())
    with (ROOT/'config/dc_experiments_1ghz.csv').open(encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    if len(rows)!=cfg['expected_groups']: raise SystemExit('experiment count mismatch')
    build=ROOT/'build_dc_1ghz'; build.mkdir(exist_ok=True)
    rtl=[ROOT/'rtl'/x.strip() for x in (ROOT/'rtl/fusion_mul16_v4.f').read_text().splitlines() if x.strip()]
    runs=[]
    for row in rows:
        rd=build/row['group_id']; rd.mkdir(parents=True,exist_ok=True)
        wrapper={'final':final_wrapper,'brick_proof':brick_wrapper,'product_pipe':product_wrapper,'accum_only':accum_wrapper}[row['top_kind']](row)
        wp=rd/'char_top.sv'; wp.write_text(wrapper)
        filelist=[*rtl,wp]
        (rd/'rtl_files.list').write_text('\n'.join(str(p.resolve()) for p in filelist)+'\n')
        h=hashlib.sha256()
        for p in filelist: h.update(p.name.encode()+b'\0'+p.read_bytes())
        meta={**row,'run_id':row['group_id'],'clock_period_ns':1.0,'clock_mhz':1000.0,'run_dir':str(rd.resolve()),'rtl_input_sha256':h.hexdigest()}
        (rd/'meta.json').write_text(json.dumps(meta,indent=2)); runs.append(meta)
    with (build/'runs.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(runs[0])); w.writeheader(); w.writerows(runs)
    print(f'generated {len(runs)} DC runs')
if __name__=='__main__': main()

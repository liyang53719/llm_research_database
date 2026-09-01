#!/usr/bin/env python3
from __future__ import annotations

import argparse,csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT.parent
BUILD=ROOT/"build_pipeline"


def bundle_hash() -> str:
    digest=hashlib.sha256()
    paths=sorted((ROOT/"rtl").glob("*.sv"))+sorted((PARENT/"rtl").glob("*.sv"))
    for path in paths:
        digest.update(path.relative_to(PARENT).as_posix().encode());digest.update(b"\0")
        digest.update(path.read_bytes());digest.update(b"\0")
    return digest.hexdigest()


def fp_wrapper(sig:int,exp:int) -> str:
    w=sig+exp+1
    return f"""module char_top(
 input logic clk,rst_n,valid_i,input logic [{w-1}:0] a_i,b_i,c_i,input logic [2:0] rnd_i,
 output logic valid_o,output logic [{w-1}:0] signature_o,output logic [7:0] status_o);
 pipelined_fp_mac_dw #(.SIG_WIDTH({sig}),.EXP_WIDTH({exp}),.IEEE_COMPLIANCE(0)) u_dut(
  .clk,.rst_n,.valid_i,.a_i,.b_i,.c_i,.rnd_i,.valid_o,.z_o(signature_o),.status_o);
endmodule"""


def conv_wrapper(sig:int,exp:int,intw:int) -> str:
    w=sig+exp+1
    return f"""module char_top(
 input logic clk,rst_n,valid_i,input logic [1:0] a_format_i,b_format_i,
 input logic [15:0] a_bits_i,b_bits_i,input logic [{w-1}:0] acc_i,input logic [2:0] rnd_i,
 output logic valid_o,output logic [{w-1}:0] signature_o,output logic [7:0] status_o);
 hybrid_convert_fp_mac_dw_pipeline #(.SIG_WIDTH({sig}),.EXP_WIDTH({exp}),.INT_WIDTH({intw})) u_dut(
  .clk,.rst_n,.valid_i,.a_format_i,.b_format_i,.a_bits_i,.b_bits_i,.acc_i,.rnd_i,
  .valid_o,.z_o(signature_o),.status_o);
endmodule"""


def shared_wrapper() -> str:
    return """module char_top(
 input logic clk,rst_n,valid_i,clear_i,input logic [1:0] a_format_i,b_format_i,
 input logic [15:0] a_bits_i,b_bits_i,input logic [2:0] rnd_i,
 output logic valid_o,output logic signed [39:0] int_acc_o,
 output logic [31:0] fp_acc_o,output logic [7:0] fp_status_o);
 hybrid_shared_mul_dual_acc #(.INT_ACC_W(40),.ENABLE_FP8(1),.ENABLE_BF16(1),.PIPELINE_PRODUCT(1)) u_dut(.*);
endmodule"""


def int_l1_wrapper() -> str:
    return """module char_top(
 input logic clk,rst_n,valid_i,clear_i,input logic signed [3:0] w_vec_i,
 input logic signed [7:0] a_vec_i,output logic valid_o,output logic signed [39:0] signature_o);
 packed_dot_pe #(.W_W(4),.A_W(8),.LANES(1),.ACC_W(40)) u_dut(
  .clk,.rst_n,.valid_i,.clear_i,.w_vec_i,.a_vec_i,.valid_o,.acc_o(signature_o));
endmodule"""


def array_wrapper() -> str:
    return """module char_top(
 input logic clk,rst_n,input logic [15:0] mode_fp_i,valid_i,clear_i,
 input logic signed [63:0] int_w_i,input logic signed [127:0] int_a_i,
 input logic [127:0] fp_a_i,fp_b_i,fp_c_i,input logic [47:0] rnd_i,
 output logic [15:0] int_valid_o,fp_valid_o,
 output logic signed [639:0] int_result_o,output logic [127:0] fp_result_o,
 output logic [127:0] fp_status_o);
 genvar i;
 generate for(i=0;i<16;i=i+1) begin:G
  packed_dot_pe #(.W_W(4),.A_W(8),.LANES(1),.ACC_W(40)) u_int(
   .clk,.rst_n,.valid_i(valid_i[i]&~mode_fp_i[i]),.clear_i(clear_i[i]),
   .w_vec_i(int_w_i[i*4+:4]),.a_vec_i(int_a_i[i*8+:8]),
   .valid_o(int_valid_o[i]),.acc_o(int_result_o[i*40+:40]));
  pipelined_fp_mac_dw #(.SIG_WIDTH(3),.EXP_WIDTH(4),.IEEE_COMPLIANCE(0)) u_fp(
   .clk,.rst_n,.valid_i(valid_i[i]&mode_fp_i[i]),.a_i(fp_a_i[i*8+:8]),
   .b_i(fp_b_i[i*8+:8]),.c_i(fp_c_i[i*8+:8]),.rnd_i(rnd_i[i*3+:3]),
   .valid_o(fp_valid_o[i]),.z_o(fp_result_o[i*8+:8]),.status_o(fp_status_o[i*8+:8]));
 end endgenerate
endmodule"""


def array_sep_wrapper() -> str:
    return """module char_top(
 input logic clk,rst_n,input logic [15:0] int_valid_i,int_clear_i,fp_valid_i,
 input logic signed [63:0] int_w_i,input logic signed [127:0] int_a_i,
 input logic [127:0] fp_a_i,fp_b_i,fp_c_i,input logic [47:0] rnd_i,
 output logic [15:0] int_valid_o,fp_valid_o,
 output logic signed [639:0] int_result_o,output logic [127:0] fp_result_o,
 output logic [127:0] fp_status_o);
 genvar i;
 generate for(i=0;i<16;i=i+1) begin:G
  packed_dot_pe #(.W_W(4),.A_W(8),.LANES(1),.ACC_W(40)) u_int(
   .clk,.rst_n,.valid_i(int_valid_i[i]),.clear_i(int_clear_i[i]),
   .w_vec_i(int_w_i[i*4+:4]),.a_vec_i(int_a_i[i*8+:8]),
   .valid_o(int_valid_o[i]),.acc_o(int_result_o[i*40+:40]));
  pipelined_fp_mac_dw #(.SIG_WIDTH(3),.EXP_WIDTH(4),.IEEE_COMPLIANCE(0)) u_fp(
   .clk,.rst_n,.valid_i(fp_valid_i[i]),.a_i(fp_a_i[i*8+:8]),
   .b_i(fp_b_i[i*8+:8]),.c_i(fp_c_i[i*8+:8]),.rnd_i(rnd_i[i*3+:3]),
   .valid_o(fp_valid_o[i]),.z_o(fp_result_o[i*8+:8]),.status_o(fp_status_o[i*8+:8]));
 end endgenerate
endmodule"""


def emit(row:dict[str,str]) -> tuple[str,list[Path]]:
    topology=row["rtl_topology"]
    if topology=="pipelined_fp_mac_dw":
        return fp_wrapper(int(row["fp_sig_width"]),int(row["fp_exp_width"])),[ROOT/"rtl/pipelined_fp_mac_dw.sv"]
    if topology=="hybrid_convert_fp_mac_dw_pipeline":
        return conv_wrapper(int(row["fp_sig_width"]),int(row["fp_exp_width"]),int(row["int_w_bits"])),[ROOT/"rtl/hybrid_convert_fp_mac_dw_pipeline.sv"]
    if topology=="hybrid_convert_fp_mac_dw_pipeline2":
        wrapper=conv_wrapper(int(row["fp_sig_width"]),int(row["fp_exp_width"]),int(row["int_w_bits"]))
        wrapper=wrapper.replace("hybrid_convert_fp_mac_dw_pipeline #", "hybrid_convert_fp_mac_dw_pipeline2 #")
        return wrapper,[ROOT/"rtl/hybrid_convert_fp_mac_dw_pipeline2.sv"]
    if topology=="hybrid_shared_mul_dual_acc_pipeline":
        return shared_wrapper(),[ROOT/"rtl/hybrid_shared_mul_dual_acc.sv"]
    if topology=="int_l1_reference":
        return int_l1_wrapper(),[PARENT/"rtl/packed_dot_pe.sv"]
    if topology=="generated_4x4_dual_pipeline":
        return array_wrapper(),[PARENT/"rtl/packed_dot_pe.sv",ROOT/"rtl/pipelined_fp_mac_dw.sv"]
    if topology=="generated_4x4_sep_pipeline":
        return array_sep_wrapper(),[PARENT/"rtl/packed_dot_pe.sv",ROOT/"rtl/pipelined_fp_mac_dw.sv"]
    raise ValueError(topology)


def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument("--group",action="append");args=parser.parse_args()
    cfg=json.loads((ROOT/"config/pipeline_characterization.json").read_text())
    with (ROOT/"config/pipeline_followup_groups.csv").open(encoding="utf-8-sig") as f:
        groups=list(csv.DictReader(f))
    requested=set(args.group or [])
    if requested:
        groups=[g for g in groups if g["group_id"] in requested]
        missing=requested-{g["group_id"] for g in groups}
        if missing:raise SystemExit(f"Unknown groups: {sorted(missing)}")
    sha=bundle_hash();BUILD.mkdir(exist_ok=True);runs=[]
    for group in groups:
        wrapper,sources=emit(group)
        for period in cfg["clock_periods_ns"]:
            run_id=f'{group["group_id"]}__T{str(period).replace(".","p")}ns'
            run_dir=(BUILD/run_id).resolve();run_dir.mkdir(parents=True,exist_ok=True)
            top=run_dir/"char_top.sv";top.write_text(wrapper+"\n")
            rtl_list=run_dir/"rtl_files.list";rtl_list.write_text("\n".join(str(p.resolve()) for p in sources+[top])+"\n")
            meta={**group,"run_id":run_id,"clock_period_ns":period,"clock_mhz":1000.0/period,
                  "run_dir":str(run_dir),"rtl_list":str(rtl_list.resolve()),"rtl_bundle_sha256":sha}
            (run_dir/"meta.json").write_text(json.dumps(meta,indent=2));runs.append(meta)
    with (BUILD/"runs.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(runs[0]));w.writeheader();w.writerows(runs)
    print(f"Generated {len(groups)} pipeline groups and {len(runs)} runs; RTL SHA={sha}")


if __name__=="__main__": main()

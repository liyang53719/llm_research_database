#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def b(row: dict, key: str) -> int:
    return int(row[key])


def fixed_cluster_wrapper(row: dict) -> str:
    return f'''module char_top (
  input logic clk, rst_n, valid_i, clear_i,
  input logic [127:0] lhs_packed_i, rhs_packed_i,
  output logic int_valid_o, fp_valid_o,
  output logic signed [47:0] int_acc_o [0:3],
  output logic [15:0] bf16_acc_o [0:3],
  output logic [7:0] bf16_status_o [0:3]
);
  logic cfg_ready_unused, cfg_error_unused;
  logic [2:0] mode_unused;
  fusion_mul16_v2_cluster #(
    .FIXED_MODE({row["fixed_mode"]}),
    .SUPPORT_FP8({b(row,"support_fp8")}),
    .SUPPORT_BF16({b(row,"support_bf16")}),
    .SUPPORT_I4_FP8({b(row,"support_i4_fp8")}),
    .SUPPORT_I4_BF16({b(row,"support_i4_bf16")}),
    .SUPPORT_I8_BF16({b(row,"support_i8_bf16")}),
    .SUPPORT_SPECIALS({b(row,"support_specials")})
  ) u_dut (
    .clk, .rst_n,
    .cfg_valid_i(1'b0), .cfg_mode_i('0), .cfg_rnd_i(3'b000),
    .cfg_ready_o(cfg_ready_unused), .cfg_error_o(cfg_error_unused),
    .valid_i, .clear_i, .lhs_packed_i, .rhs_packed_i,
    .int_valid_o, .fp_valid_o, .int_acc_o, .bf16_acc_o,
    .bf16_status_o, .active_mode_o(mode_unused)
  );
endmodule
'''


def shared_cluster_wrapper(row: dict) -> str:
    return f'''module char_top (
  input logic clk, rst_n,
  input logic cfg_valid_i,
  input logic [2:0] cfg_mode_i, cfg_rnd_i,
  output logic cfg_ready_o, cfg_error_o,
  input logic valid_i, clear_i,
  input logic [127:0] lhs_packed_i, rhs_packed_i,
  output logic int_valid_o, fp_valid_o,
  output logic signed [47:0] int_acc_o [0:3],
  output logic [15:0] bf16_acc_o [0:3],
  output logic [7:0] bf16_status_o [0:3],
  output logic [2:0] active_mode_o
);
  fusion_mul16_v2_cluster #(
    .FIXED_MODE(-1),
    .SUPPORT_FP8({b(row,"support_fp8")}),
    .SUPPORT_BF16({b(row,"support_bf16")}),
    .SUPPORT_I4_FP8({b(row,"support_i4_fp8")}),
    .SUPPORT_I4_BF16({b(row,"support_i4_bf16")}),
    .SUPPORT_I8_BF16({b(row,"support_i8_bf16")}),
    .SUPPORT_SPECIALS({b(row,"support_specials")})
  ) u_dut (.*);
endmodule
'''.replace('(.*);', '''(
    .clk, .rst_n, .cfg_valid_i, .cfg_mode_i, .cfg_rnd_i,
    .cfg_ready_o, .cfg_error_o, .valid_i, .clear_i,
    .lhs_packed_i, .rhs_packed_i, .int_valid_o, .fp_valid_o,
    .int_acc_o, .bf16_acc_o, .bf16_status_o, .active_mode_o
  );''')


def product_core_wrapper(row: dict) -> str:
    return f'''module char_top (
  input logic clk, rst_n, valid_i, clear_i,
  input logic [6:0] mode_onehot_i,
  input logic [127:0] lhs_packed_i, rhs_packed_i,
  output logic int_valid_o, int_clear_o,
  output logic signed [17:0] int_lane_sum_o [0:3],
  output logic fp_valid_o, fp_clear_o,
  output logic [15:0] bf16_lane_item_o [0:3][0:3]
);
  fusion_mul16_v2_product_pipe #(
    .SUPPORT_FP8({b(row,"support_fp8")}),
    .SUPPORT_BF16({b(row,"support_bf16")}),
    .SUPPORT_I4_FP8({b(row,"support_i4_fp8")}),
    .SUPPORT_I4_BF16({b(row,"support_i4_bf16")}),
    .SUPPORT_I8_BF16({b(row,"support_i8_bf16")}),
    .SUPPORT_SPECIALS({b(row,"support_specials")})
  ) u_dut (.*);
endmodule
'''.replace('(.*);', '''(
    .clk, .rst_n, .valid_i, .clear_i, .mode_onehot_i,
    .lhs_packed_i, .rhs_packed_i,
    .int_valid_o, .int_clear_o, .int_lane_sum_o,
    .fp_valid_o, .fp_clear_o, .bf16_lane_item_o
  );''')


def brick_proof_wrapper() -> str:
    return '''module char_top (
  input logic clk, rst_n,
  input logic [63:0] a_i, b_i,
  output logic [127:0] p_o
);
  logic [7:0] product [0:15];
  logic [127:0] p_comb;
  genvar g;
  generate
    for (g=0; g<16; g=g+1) begin : G_BRICK
      mul4x4_brick u_brick(
        .a_i(a_i[g*4 +: 4]), .b_i(b_i[g*4 +: 4]), .p_o(product[g])
      );
      assign p_comb[g*8 +: 8] = product[g];
    end
  endgenerate
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) p_o <= '0;
    else p_o <= p_comb;
  end
endmodule
'''


def bf16_accum_wrapper() -> str:
    return '''module char_top (
  input logic clk, rst_n, valid_i, clear_i,
  input logic [255:0] lane_item_packed_i,
  input logic [2:0] rnd_i,
  output logic valid_o,
  output logic [63:0] acc_packed_o,
  output logic [31:0] status_packed_o
);
  logic [15:0] lane_item [0:3][0:3];
  logic [15:0] acc [0:3];
  logic [7:0] status [0:3];
  genvar lane,item;
  generate
    for(lane=0;lane<4;lane=lane+1) begin:G_L
      for(item=0;item<4;item=item+1) begin:G_I
        assign lane_item[lane][item]=lane_item_packed_i[(lane*4+item)*16 +: 16];
      end
      assign acc_packed_o[lane*16 +: 16]=acc[lane];
      assign status_packed_o[lane*8 +: 8]=status[lane];
    end
  endgenerate
  fusion_mul16_v2_bf16_accum_dw u_dut(
    .clk,.rst_n,.valid_i,.clear_i,.lane_item_i(lane_item),.rnd_i,
    .valid_o,.acc_o(acc),.status_o(status)
  );
endmodule
'''


def fp8_widen_wrapper() -> str:
    return '''module char_top (
  input logic clk,rst_n,valid_i,clear_i,
  input logic [127:0] lhs_fp8_packed_i,rhs_fp8_packed_i,
  output logic valid_o,
  output logic [15:0] acc_o [0:3],
  output logic [7:0] status_o [0:3]
);
  fusion_mul16_v2_fp8_widen_bf16_top u_dut(.*);
endmodule
'''.replace('(.*);', '''(
    .clk,.rst_n,.valid_i,.clear_i,.lhs_fp8_packed_i,.rhs_fp8_packed_i,
    .valid_o,.acc_o,.status_o
  );''')


def separate_wrapper() -> str:
    return '''module char_top (
  input logic clk,rst_n,
  input logic int_cfg_valid_i,
  input logic [2:0] int_cfg_mode_i,
  output logic int_cfg_ready_o,int_cfg_error_o,
  input logic int_valid_i,int_clear_i,
  input logic [127:0] int_lhs_i,int_rhs_i,
  input logic fp8_valid_i,fp8_clear_i,
  input logic [127:0] fp8_lhs_i,fp8_rhs_i,
  input logic bf16_valid_i,bf16_clear_i,
  input logic [127:0] bf16_lhs_i,bf16_rhs_i,
  output logic int_valid_o,fp8_valid_o,bf16_valid_o,
  output logic signed [47:0] int_acc_o [0:3],
  output logic [15:0] fp8_acc_o [0:3],bf16_acc_o [0:3]
);
  fusion_mul16_v2_separate_full_top u_dut(.*);
endmodule
'''.replace('(.*);', '''(
    .clk,.rst_n,.int_cfg_valid_i,.int_cfg_mode_i,.int_cfg_ready_o,.int_cfg_error_o,
    .int_valid_i,.int_clear_i,.int_lhs_i,.int_rhs_i,
    .fp8_valid_i,.fp8_clear_i,.fp8_lhs_i,.fp8_rhs_i,
    .bf16_valid_i,.bf16_clear_i,.bf16_lhs_i,.bf16_rhs_i,
    .int_valid_o,.fp8_valid_o,.bf16_valid_o,.int_acc_o,.fp8_acc_o,.bf16_acc_o
  );''')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=str(ROOT))
    parser.add_argument('--build-dir', default='build_dc_1ghz')
    args = parser.parse_args()
    root = Path(args.root).resolve()
    build = root / args.build_dir
    build.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((root/'config/characterization_1ghz.json').read_text())
    with (root/'config/dc_experiments_1ghz.csv').open(encoding='utf-8-sig') as f:
        groups = list(csv.DictReader(f))
    if len(groups) != cfg['expected_runs']:
        raise SystemExit('expected_runs mismatch')

    rtl_order = [
        'fusion_mul16_v2_pkg.sv','fusion_mul16_v2_config.sv','mul4x4_brick.sv','raw16_to_bf16_rne.sv',
        'fp8_to_bf16_exact.sv','fusion_mul16_v2_product_pipe.sv',
        'fusion_mul16_v2_int_accum.sv','fusion_mul16_v2_bf16_accum_dw.sv',
        'fusion_mul16_v2_cluster.sv','fusion_mul16_v2_fp8_widen_bf16_top.sv',
        'fusion_mul16_v2_separate_full_top.sv'
    ]
    rtl_files = [str((root/'rtl'/name).resolve()) for name in rtl_order]
    missing = [path for path in rtl_files if not Path(path).exists()]
    if missing:
        raise SystemExit('Missing RTL:\n'+'\n'.join(missing))

    wrappers = {
        'brick_proof': lambda row: brick_proof_wrapper(),
        'product_core': product_core_wrapper,
        'bf16_accum': lambda row: bf16_accum_wrapper(),
        'fixed_cluster': fixed_cluster_wrapper,
        'shared_cluster': shared_cluster_wrapper,
        'fp8_widen_bf16': lambda row: fp8_widen_wrapper(),
        'separate_full': lambda row: separate_wrapper(),
    }
    runs=[]
    for row in groups:
        run_id=row['group_id']
        run_dir=build/run_id
        run_dir.mkdir(parents=True,exist_ok=True)
        wrapper=run_dir/'char_top.sv'
        wrapper.write_text(wrappers[row['top_kind']](row),encoding='utf-8')
        file_list=rtl_files+[str(wrapper.resolve())]
        (run_dir/'rtl_files.list').write_text('\n'.join(file_list)+'\n',encoding='utf-8')
        meta={**row,'run_id':run_id,'run_dir':str(run_dir.resolve()),
              'clock_period_ns':cfg['clock_period_ns'],'clock_mhz':1000.0,
              'top_module':'char_top','keep_bricks':1 if row['top_kind']=='brick_proof' else 0}
        digest=hashlib.sha256()
        for path in file_list:
            rel=Path(path).relative_to(root).as_posix() if Path(path).is_relative_to(root) else Path(path).name
            digest.update(rel.encode()+b'\0'+Path(path).read_bytes())
        meta['rtl_input_sha256']=digest.hexdigest()
        (run_dir/'meta.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
        runs.append(meta)
    with (build/'runs.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=list(runs[0])); writer.writeheader(); writer.writerows(runs)
    print(f'Generated {len(runs)} one-GHz DC runs in {build}')


if __name__=='__main__':
    main()

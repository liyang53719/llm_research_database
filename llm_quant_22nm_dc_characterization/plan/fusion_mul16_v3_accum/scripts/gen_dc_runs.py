#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def b(row: dict[str, str], key: str) -> int:
    return int(row[key])


def accum_wrapper(style: int) -> str:
    common = '''
  logic [15:0] lane_item [0:3][0:3];
  genvar lane,item;
  generate
    for(lane=0;lane<4;lane=lane+1) begin:G_L
      for(item=0;item<4;item=item+1) begin:G_I
        assign lane_item[lane][item] = lane_item_packed_i[(lane*4+item)*16 +: 16];
      end
    end
  endgenerate
'''
    if style == 0:
        return '''module char_top(
  input logic clk,rst_n,valid_i,clear_i,
  input logic [255:0] lane_item_packed_i,
  input logic [2:0] rnd_i,
  output logic valid_o,
  output logic [63:0] bf16_acc_packed_o,
  output logic [127:0] fp32_view_packed_o,
  output logic [31:0] status_packed_o
);''' + common + '''
  logic [15:0] acc_bf16[0:3]; logic [31:0] view[0:3]; logic [7:0] status[0:3];
  generate for(lane=0;lane<4;lane=lane+1) begin:G_O
    assign bf16_acc_packed_o[lane*16+:16]=acc_bf16[lane];
    assign fp32_view_packed_o[lane*32+:32]=view[lane];
    assign status_packed_o[lane*8+:8]=status[lane];
  end endgenerate
  fusion_mul16_v3_accum_full_bf16_dw u_dut(
    .clk,.rst_n,.valid_i,.clear_i,.lane_item_i(lane_item),.rnd_i,
    .valid_o,.acc_bf16_o(acc_bf16),.acc_fp32_view_o(view),.status_o(status));
endmodule
'''
    if style == 1:
        return '''module char_top(
  input logic clk,rst_n,valid_i,clear_i,
  input logic [255:0] lane_item_packed_i,
  input logic [2:0] rnd_i,
  output logic valid_o,
  output logic [127:0] fp32_acc_packed_o,
  output logic [31:0] status_packed_o
);''' + common + '''
  logic [31:0] acc[0:3]; logic [7:0] status[0:3];
  generate for(lane=0;lane<4;lane=lane+1) begin:G_O
    assign fp32_acc_packed_o[lane*32+:32]=acc[lane];
    assign status_packed_o[lane*8+:8]=status[lane];
  end endgenerate
  fusion_mul16_v3_accum_fp32_recurrent_dw u_dut(
    .clk,.rst_n,.valid_i,.clear_i,.lane_item_i(lane_item),.rnd_i,
    .valid_o,.acc_fp32_o(acc),.status_o(status));
endmodule
'''
    return '''module char_top(
  input logic clk,rst_n,valid_i,clear_i,flush_i,
  input logic [2:0] items_per_lane_i,
  input logic [255:0] lane_item_packed_i,
  input logic [2:0] rnd_i,
  output logic checkpoint_valid_o,flush_done_o,protocol_error_o,
  output logic [127:0] fp32_acc_packed_o,
  output logic [63:0] partial_packed_o,
  output logic [6:0] products_in_partial_o,
  output logic [31:0] status_packed_o
);''' + common + '''
  logic [31:0] acc[0:3]; logic [15:0] partial[0:3]; logic [7:0] status[0:3];
  generate for(lane=0;lane<4;lane=lane+1) begin:G_O
    assign fp32_acc_packed_o[lane*32+:32]=acc[lane];
    assign partial_packed_o[lane*16+:16]=partial[lane];
    assign status_packed_o[lane*8+:8]=status[lane];
  end endgenerate
  fusion_mul16_v3_accum_block64_fp32_checkpoint_dw u_dut(
    .clk,.rst_n,.valid_i,.clear_i,.flush_i,.items_per_lane_i,
    .lane_item_i(lane_item),.rnd_i,.checkpoint_valid_o,.flush_done_o,
    .protocol_error_o,.checkpoint_fp32_o(acc),.partial_bf16_o(partial),
    .products_in_partial_o,.status_o(status));
endmodule
'''


def cluster_wrapper(row: dict[str, str]) -> str:
    fixed_mode = int(row['fixed_mode'])
    cfg_ports = '' if fixed_mode >= 0 else '''
  input logic cfg_valid_i,
  input logic [2:0] cfg_mode_i,cfg_rnd_i,
  output logic cfg_ready_o,cfg_error_o,'''
    cfg_conn = '''.cfg_valid_i(1'b0),.cfg_mode_i('0),.cfg_rnd_i(3'b000),
    .cfg_ready_o(cfg_ready_unused),.cfg_error_o(cfg_error_unused),''' if fixed_mode >= 0 else '''.cfg_valid_i,.cfg_mode_i,.cfg_rnd_i,.cfg_ready_o,.cfg_error_o,'''
    return f'''module char_top(
  input logic clk,rst_n,{cfg_ports}
  input logic valid_i,clear_i,flush_i,
  input logic [127:0] lhs_packed_i,rhs_packed_i,
  output logic int_valid_o,fp_valid_o,flush_done_o,protocol_error_o,
  output logic signed [47:0] int_acc_o[0:3],
  output logic [31:0] fp_acc_o[0:3],
  output logic [7:0] fp_status_o[0:3],
  output logic [2:0] active_mode_o
);
  logic cfg_ready_unused,cfg_error_unused;
  fusion_mul16_v3_cluster #(
    .FIXED_MODE({fixed_mode}),.ACCUM_STYLE({row['accum_style']}),
    .SUPPORT_FP8({b(row,'support_fp8')}),.SUPPORT_BF16({b(row,'support_bf16')}),
    .SUPPORT_I4_FP8({b(row,'support_i4_fp8')}),
    .SUPPORT_I4_BF16({b(row,'support_i4_bf16')}),
    .SUPPORT_I8_BF16({b(row,'support_i8_bf16')}),
    .SUPPORT_SPECIALS({b(row,'support_specials')}),.BLOCK_PRODUCTS(64)
  ) u_dut(
    .clk,.rst_n,{cfg_conn}.valid_i,.clear_i,.flush_i,
    .lhs_packed_i,.rhs_packed_i,.int_valid_o,.fp_valid_o,.flush_done_o,
    .protocol_error_o,.int_acc_o,.fp_acc_o,.fp_status_o,.active_mode_o);
endmodule
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--v2-root', required=True)
    parser.add_argument('--build-dir', default=str(ROOT / 'build_dc_1ghz'))
    args = parser.parse_args()
    v2_root = Path(args.v2_root).resolve()
    build = Path(args.build_dir).resolve()
    build.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((ROOT / 'config/characterization_1ghz.json').read_text())
    with (ROOT / 'config/dc_experiments_1ghz.csv').open(encoding='utf-8-sig') as f:
        groups = list(csv.DictReader(f))
    if len(groups) != cfg['expected_runs']:
        raise SystemExit('experiment count mismatch')

    v2_names = [
        'fusion_mul16_v2_pkg.sv','fusion_mul16_v2_config.sv','mul4x4_brick.sv',
        'raw16_to_bf16_rne.sv','fusion_mul16_v2_product_pipe.sv',
        'fusion_mul16_v2_int_accum.sv'
    ]
    v3_names = [
        'fusion_mul16_v3_accum_pkg.sv','fusion_mul16_v3_bf16_tree_dw.sv',
        'fusion_mul16_v3_accum_full_bf16_dw.sv',
        'fusion_mul16_v3_accum_fp32_recurrent_dw.sv',
        'fusion_mul16_v3_accum_block64_fp32_checkpoint_dw.sv',
        'fusion_mul16_v3_cluster.sv'
    ]
    rtl = [v2_root / 'rtl' / name for name in v2_names]
    rtl += [ROOT / 'rtl' / name for name in v3_names]
    missing = [str(path) for path in rtl if not path.exists()]
    if missing:
        raise SystemExit('missing RTL:\n' + '\n'.join(missing))

    runs = []
    for row in groups:
        run_dir = build / row['group_id']
        run_dir.mkdir(parents=True, exist_ok=True)
        if row['top_kind'].startswith('accum_'):
            wrapper = accum_wrapper(int(row['accum_style']))
        else:
            wrapper = cluster_wrapper(row)
        wrapper_path = run_dir / 'char_top.sv'
        wrapper_path.write_text(wrapper, encoding='utf-8')
        file_list = [*rtl, wrapper_path]
        (run_dir / 'rtl_files.list').write_text(
            '\n'.join(str(path.resolve()) for path in file_list) + '\n',
            encoding='utf-8'
        )
        digest = hashlib.sha256()
        for path in file_list:
            digest.update(path.name.encode() + b'\0' + path.read_bytes())
        extra_constraint = ''
        if row['constraint_profile'] == 'checkpoint_mc2':
            extra_constraint = str((ROOT / 'config/checkpoint_multicycle.tcl').resolve())
        meta = {
            **row,
            'run_id': row['group_id'],
            'clock_period_ns': 1.0,
            'clock_mhz': 1000.0,
            'run_dir': str(run_dir),
            'rtl_input_sha256': digest.hexdigest(),
            'extra_constraint_tcl': extra_constraint,
        }
        (run_dir / 'meta.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
        runs.append(meta)
    with (build / 'runs.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(runs[0]))
        writer.writeheader()
        writer.writerows(runs)
    print(f'generated {len(runs)} one-GHz DC runs in {build}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"
BUILD = ROOT / "build"
RTL_DIR = ROOT / "rtl"

SMOKE_GROUPS = {
    "INT_MAC_W4_A4_N64",
    "INT_MAC_W4_A8_N64",
    "INT_MAC_W8_A8_N64",
    "INT_MAC_W4_A16_N64",
    "FP_MAC_FP8_E4M3",
    "FP_MAC_BF16_E8M7",
    "PE_W4A8_L4",
    "ARRAY_W4A8_4X4",
}

TEMPLATE_RTL = {
    "int_mac": "int_mac.sv",
    "fp_mac_dw": "fp_mac_dw.sv",
    "fp4_dw_surrogate": "fp4_e2m1_mac_dw_surrogate.sv",
    "packed_dot": "packed_dot_pe.sv",
    "mixed_mode": "mixed_mode_pe.sv",
    "array_int": "systolic_array_int.sv",
    "array_fp": "systolic_array_fp_dw.sv",
    "requant": "requant_int.sv",
    "kv_dequant": "kv_dequant.sv",
    "kv_dequant_mixed": "kv_dequant_mixed.sv",
}

def as_int(row, key, default=0):
    value = row.get(key, "")
    return default if value in ("", None) else int(value)

def emit_wrapper(row: dict) -> str:
    t = row["template"]
    if t == "int_mac":
        w = as_int(row, "w_bits")
        a = as_int(row, "a_bits")
        acc = as_int(row, "acc_width")
        return f"""
module char_top(
  input logic clk, rst_n, valid_i, clear_i,
  input logic signed [{w-1}:0] w_i,
  input logic signed [{a-1}:0] a_i,
  output logic valid_o,
  output logic signed [{acc-1}:0] signature_o
);
  int_mac #(.W_W({w}), .A_W({a}), .ACC_W({acc})) u_dut (
    .clk, .rst_n, .valid_i, .clear_i, .w_i, .a_i,
    .valid_o, .acc_o(signature_o)
  );
endmodule
"""
    if t == "fp_mac_dw":
        sig = as_int(row, "sig_width")
        exp = as_int(row, "exp_width")
        ieee = as_int(row, "ieee_compliance")
        width = sig + exp + 1
        return f"""
module char_top(
  input logic clk, rst_n, valid_i,
  input logic [{width-1}:0] a_i, b_i, c_i,
  input logic [2:0] rnd_i,
  output logic valid_o,
  output logic [{width-1}:0] signature_o,
  output logic [7:0] status_o
);
  fp_mac_dw #(.SIG_WIDTH({sig}), .EXP_WIDTH({exp}), .IEEE_COMPLIANCE({ieee})) u_dut (
    .clk, .rst_n, .valid_i, .a_i, .b_i, .c_i, .rnd_i,
    .valid_o, .z_o(signature_o), .status_o
  );
endmodule
"""
    if t == "fp4_dw_surrogate":
        return """
module char_top(
  input logic clk, rst_n, valid_i,
  input logic [3:0] a_i, b_i, c_i,
  input logic [2:0] rnd_i,
  output logic valid_o,
  output logic [3:0] signature_o,
  output logic [7:0] status_o
);
  fp4_e2m1_mac_dw_surrogate u_dut (
    .clk, .rst_n, .valid_i, .a_i, .b_i, .c_i, .rnd_i,
    .valid_o, .z_o(signature_o), .status_o
  );
endmodule
"""
    if t == "packed_dot":
        w = as_int(row, "w_bits")
        a = as_int(row, "a_bits")
        lanes = as_int(row, "lanes")
        acc = as_int(row, "acc_width")
        return f"""
module char_top(
  input logic clk, rst_n, valid_i, clear_i,
  input logic signed [{lanes*w-1}:0] w_vec_i,
  input logic signed [{lanes*a-1}:0] a_vec_i,
  output logic valid_o,
  output logic signed [{acc-1}:0] signature_o
);
  packed_dot_pe #(.W_W({w}), .A_W({a}), .LANES({lanes}), .ACC_W({acc})) u_dut (
    .clk, .rst_n, .valid_i, .clear_i, .w_vec_i, .a_vec_i,
    .valid_o, .acc_o(signature_o)
  );
endmodule
"""
    if t == "mixed_mode":
        acc = as_int(row, "acc_width")
        req = as_int(row, "with_requant")
        return f"""
module char_top(
  input logic clk, rst_n, valid_i, clear_i,
  input logic [1:0] mode_i,
  input logic [31:0] w_word_i, a_word_i,
  input logic signed [15:0] scale_i,
  output logic valid_o,
  output logic signed [{acc-1}:0] signature_o,
  output logic signed [15:0] requant_o
);
  mixed_mode_pe #(.ACC_W({acc}), .WITH_REQUANT({req})) u_dut (
    .clk, .rst_n, .valid_i, .clear_i, .mode_i,
    .w_word_i, .a_word_i, .scale_i,
    .valid_o, .acc_o(signature_o), .requant_o
  );
endmodule
"""
    if t == "array_int":
        rows = as_int(row, "rows")
        cols = as_int(row, "cols")
        w = as_int(row, "w_bits")
        a = as_int(row, "a_bits")
        acc = as_int(row, "acc_width")
        return f"""
module char_top(
  input logic clk, rst_n, clear_i,
  input logic signed [{rows*a-1}:0] a_left_i,
  input logic signed [{cols*w-1}:0] w_top_i,
  output logic [{acc-1}:0] signature_o
);
  systolic_array_int #(.ROWS({rows}), .COLS({cols}), .W_W({w}), .A_W({a}), .ACC_W({acc})) u_dut (
    .clk, .rst_n, .clear_i, .a_left_i, .w_top_i, .signature_o
  );
endmodule
"""
    if t == "array_fp":
        rows = as_int(row, "rows")
        cols = as_int(row, "cols")
        sig = as_int(row, "sig_width")
        exp = as_int(row, "exp_width")
        ieee = as_int(row, "ieee_compliance")
        fpw = sig + exp + 1
        return f"""
module char_top(
  input logic clk, rst_n, clear_i,
  input logic [{rows*fpw-1}:0] a_left_i,
  input logic [{cols*fpw-1}:0] b_top_i,
  input logic [2:0] rnd_i,
  output logic [{fpw-1}:0] signature_o
);
  systolic_array_fp_dw #(.ROWS({rows}), .COLS({cols}), .SIG_WIDTH({sig}), .EXP_WIDTH({exp}), .IEEE_COMPLIANCE({ieee})) u_dut (
    .clk, .rst_n, .clear_i, .a_left_i, .b_top_i, .rnd_i, .signature_o
  );
endmodule
"""
    if t == "requant":
        inw = as_int(row, "in_bits")
        outw = as_int(row, "out_bits")
        return f"""
module char_top(
  input logic clk, rst_n, valid_i,
  input logic signed [{inw-1}:0] value_i,
  input logic signed [15:0] scale_i,
  input logic signed [{outw-1}:0] zero_point_i,
  output logic valid_o,
  output logic signed [{outw-1}:0] signature_o
);
  requant_int #(.IN_W({inw}), .OUT_W({outw}), .SCALE_W(16), .SHIFT(8)) u_dut (
    .clk, .rst_n, .valid_i, .value_i, .scale_i, .zero_point_i,
    .valid_o, .value_o(signature_o)
  );
endmodule
"""
    if t == "kv_dequant":
        inw = as_int(row, "in_bits")
        outw = as_int(row, "out_bits")
        lanes = as_int(row, "lanes")
        asym = as_int(row, "asymmetric")
        bypass = 1 if inw == outw and asym == 0 else 0
        return f"""
module char_top(
  input logic clk, rst_n, valid_i,
  input logic signed [{lanes*inw-1}:0] packed_i,
  input logic signed [7:0] scale_i,
  input logic signed [{inw-1}:0] zero_point_i,
  output logic valid_o,
  output logic signed [{lanes*outw-1}:0] signature_o
);
  kv_dequant #(.IN_W({inw}), .OUT_W({outw}), .LANES({lanes}),
               .SCALE_W(8), .FRAC_BITS(4), .ASYMMETRIC({asym}), .BYPASS({bypass})) u_dut (
    .clk, .rst_n, .valid_i, .packed_i, .scale_i, .zero_point_i,
    .valid_o, .unpacked_o(signature_o)
  );
endmodule
"""
    if t == "kv_dequant_mixed":
        lanes = as_int(row, "lanes")
        outw = as_int(row, "out_bits")
        return f"""
module char_top(
  input logic clk, rst_n, valid_i,
  input logic [1:0] mode_i,
  input logic signed [{lanes*8-1}:0] lane_slots_i,
  input logic signed [7:0] scale_i, zero_point_i,
  output logic valid_o,
  output logic signed [{lanes*outw-1}:0] signature_o
);
  kv_dequant_mixed #(.LANES({lanes}), .OUT_W({outw})) u_dut (
    .clk, .rst_n, .valid_i, .mode_i, .lane_slots_i, .scale_i, .zero_point_i,
    .valid_o, .unpacked_o(signature_o)
  );
endmodule
"""
    raise ValueError(f"Unsupported template: {t}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", choices=["L1", "L2"], default="L2")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--periods", nargs="*", type=float)
    ap.add_argument("--group", action="append", help="Generate only the named group; may be repeated.")
    args = ap.parse_args()

    cfg = json.loads((CONFIG / "characterization.json").read_text(encoding="utf-8"))
    periods = args.periods or cfg["default_clock_periods_ns"]
    tier_rank = {"L1": 1, "L2": 2}

    with (CONFIG / "experiment_groups.csv").open(encoding="utf-8-sig") as f:
        groups = list(csv.DictReader(f))

    selected = []
    requested_groups = set(args.group or [])
    for row in groups:
        if tier_rank[row["tier"]] <= tier_rank[args.tier]:
            if requested_groups and row["group_id"] not in requested_groups:
                continue
            if not args.smoke or row["group_id"] in SMOKE_GROUPS:
                selected.append(row)

    selected_ids = {row["group_id"] for row in selected}
    missing_groups = requested_groups - selected_ids
    if missing_groups:
        raise SystemExit(f"Requested groups are unavailable at tier {args.tier}: {sorted(missing_groups)}")

    BUILD.mkdir(exist_ok=True)
    run_rows = []
    all_rtl = [str(p.resolve()) for p in sorted(RTL_DIR.glob("*.sv"))]
    rtl_digest = hashlib.sha256()
    for rtl_path in all_rtl:
        path = Path(rtl_path)
        rtl_digest.update(path.name.encode("utf-8"))
        rtl_digest.update(b"\0")
        rtl_digest.update(path.read_bytes())
        rtl_digest.update(b"\0")
    rtl_bundle_sha256 = rtl_digest.hexdigest()

    for row in selected:
        for period in periods:
            period_tag = str(period).replace(".", "p")
            run_id = f'{row["group_id"]}__T{period_tag}ns'
            run_dir = BUILD / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            wrapper = run_dir / "char_top.sv"
            wrapper.write_text(emit_wrapper(row).strip() + "\n", encoding="utf-8")
            rtl_list = run_dir / "rtl_files.list"
            design_rtl = RTL_DIR / TEMPLATE_RTL[row["template"]]
            rtl_list.write_text(
                "\n".join([str(design_rtl.resolve()), str(wrapper.resolve())]) + "\n",
                encoding="utf-8",
            )
            meta = dict(row)
            meta.update({
                "run_id": run_id,
                "clock_period_ns": period,
                "clock_mhz": 1000.0 / period,
                "run_dir": str(run_dir.resolve()),
                "rtl_bundle_sha256": rtl_bundle_sha256,
            })
            (run_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
            run_rows.append(meta)

    fields = list(run_rows[0].keys()) if run_rows else []
    with (BUILD / "runs.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(run_rows)

    print(f"Generated {len(selected)} groups and {len(run_rows)} DC runs.")
    print(f"Manifest: {BUILD / 'runs.csv'}")

if __name__ == "__main__":
    main()

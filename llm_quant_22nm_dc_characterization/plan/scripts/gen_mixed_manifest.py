#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

PLAN_ROOT = Path(__file__).resolve().parents[1]
PARENT_ROOT = PLAN_ROOT.parent
BUILD = PLAN_ROOT / "build_mixed"


def digest_sources(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(PARENT_ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def as_int(row: dict[str, str], key: str, default: int = 0) -> int:
    value = row.get(key, "")
    return default if value in ("", None) else int(value)


def emit_reference_int(row: dict[str, str]) -> str:
    w = as_int(row, "int_w_bits")
    a = as_int(row, "int_a_bits")
    return f"""
module char_top(
  input logic clk, rst_n, valid_i, clear_i,
  input logic signed [{4*w-1}:0] w_vec_i,
  input logic signed [{4*a-1}:0] a_vec_i,
  output logic valid_o,
  output logic signed [39:0] signature_o
);
  packed_dot_pe #(.W_W({w}), .A_W({a}), .LANES(4), .ACC_W(40)) u_dut (
    .clk, .rst_n, .valid_i, .clear_i, .w_vec_i, .a_vec_i,
    .valid_o, .acc_o(signature_o)
  );
endmodule
"""


def emit_reference_fp(row: dict[str, str]) -> str:
    sig = as_int(row, "fp_sig_width")
    exp = as_int(row, "fp_exp_width")
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
  fp_mac_dw #(.SIG_WIDTH({sig}), .EXP_WIDTH({exp}), .IEEE_COMPLIANCE(0)) u_dut (
    .clk, .rst_n, .valid_i, .a_i, .b_i, .c_i, .rnd_i,
    .valid_o, .z_o(signature_o), .status_o
  );
endmodule
"""


def emit_separate(row: dict[str, str]) -> str:
    w = as_int(row, "int_w_bits")
    a = as_int(row, "int_a_bits")
    sig = as_int(row, "fp_sig_width")
    exp = as_int(row, "fp_exp_width")
    fpw = sig + exp + 1
    return f"""
module char_top(
  input logic clk, rst_n, int_valid_i, int_clear_i, fp_valid_i,
  input logic signed [{4*w-1}:0] int_w_i,
  input logic signed [{4*a-1}:0] int_a_i,
  input logic [{fpw-1}:0] fp_a_i, fp_b_i, fp_c_i,
  input logic [2:0] rnd_i,
  output logic int_valid_o, fp_valid_o,
  output logic signed [39:0] int_acc_o,
  output logic [{fpw-1}:0] fp_z_o,
  output logic [7:0] fp_status_o
);
  separate_int_fp_reference #(
    .INT_W_W({w}), .INT_A_W({a}), .INT_LANES(4), .INT_ACC_W(40),
    .FP_SIG_WIDTH({sig}), .FP_EXP_WIDTH({exp})
  ) u_dut (.*);
endmodule
"""


def emit_dual(row: dict[str, str]) -> str:
    w = as_int(row, "int_w_bits")
    a = as_int(row, "int_a_bits")
    sig = as_int(row, "fp_sig_width")
    exp = as_int(row, "fp_exp_width")
    fpw = sig + exp + 1
    return f"""
module char_top(
  input logic clk, rst_n, mode_fp_i, valid_i, clear_i,
  input logic signed [{4*w-1}:0] int_w_i,
  input logic signed [{4*a-1}:0] int_a_i,
  input logic [{fpw-1}:0] fp_a_i, fp_b_i, fp_c_i,
  input logic [2:0] rnd_i,
  output logic valid_o,
  output logic signed [39:0] int_result_o,
  output logic [{fpw-1}:0] fp_result_o
);
  dual_domain_int_fp_reference #(
    .INT_W_W({w}), .INT_A_W({a}), .INT_LANES(4), .INT_ACC_W(40),
    .FP_SIG_WIDTH({sig}), .FP_EXP_WIDTH({exp})
  ) u_dut (.*);
endmodule
"""


def emit_convert(row: dict[str, str]) -> str:
    sig = as_int(row, "fp_sig_width")
    exp = as_int(row, "fp_exp_width")
    intw = as_int(row, "int_w_bits")
    fpw = sig + exp + 1
    return f"""
module char_top(
  input logic clk, rst_n, valid_i,
  input logic [1:0] a_format_i, b_format_i,
  input logic [15:0] a_bits_i, b_bits_i,
  input logic [{fpw-1}:0] acc_i,
  input logic [2:0] rnd_i,
  output logic valid_o,
  output logic [{fpw-1}:0] signature_o,
  output logic [7:0] status_o
);
  hybrid_convert_fp_mac_dw #(
    .SIG_WIDTH({sig}), .EXP_WIDTH({exp}), .IEEE_COMPLIANCE(0), .INT_WIDTH({intw})
  ) u_dut (
    .clk, .rst_n, .valid_i, .a_format_i, .b_format_i, .a_bits_i, .b_bits_i,
    .acc_i, .rnd_i, .valid_o, .z_o(signature_o), .status_o
  );
endmodule
"""


def emit_shared(row: dict[str, str]) -> str:
    group = row["group_id"]
    fp8 = 0 if "BF16" in group and "ALL" not in group else 1
    bf16 = 0 if "FP8" in group and "ALL" not in group else 1
    return f"""
module char_top(
  input logic clk, rst_n, valid_i, clear_i,
  input logic [1:0] a_format_i, b_format_i,
  input logic [15:0] a_bits_i, b_bits_i,
  input logic [2:0] rnd_i,
  output logic valid_o,
  output logic signed [39:0] int_acc_o,
  output logic [31:0] fp_acc_o,
  output logic [7:0] fp_status_o
);
  hybrid_shared_mul_dual_acc #(
    .INT_ACC_W(40), .ENABLE_FP8({fp8}), .ENABLE_BF16({bf16})
  ) u_dut (.*);
endmodule
"""


def emit_array(row: dict[str, str]) -> str:
    is_separate = row["group_id"].startswith("ARRAY4_SEP")
    cells, w, a, sig, exp, fpw = 16, 4, 8, 3, 4, 8
    if is_separate:
        return f"""
module char_top(
  input logic clk, rst_n,
  input logic [{cells-1}:0] int_valid_i, int_clear_i, fp_valid_i,
  input logic signed [{cells*w-1}:0] int_w_i,
  input logic signed [{cells*a-1}:0] int_a_i,
  input logic [{cells*fpw-1}:0] fp_a_i, fp_b_i, fp_c_i,
  input logic [{cells*3-1}:0] rnd_i,
  output logic [{cells-1}:0] int_valid_o, fp_valid_o,
  output logic signed [{cells*40-1}:0] int_acc_o,
  output logic [{cells*fpw-1}:0] fp_z_o,
  output logic [{cells*8-1}:0] fp_status_o
);
  genvar i;
  generate for (i=0; i<{cells}; i=i+1) begin : G
    separate_int_fp_reference #(
      .INT_W_W({w}), .INT_A_W({a}), .INT_LANES(1), .INT_ACC_W(40),
      .FP_SIG_WIDTH({sig}), .FP_EXP_WIDTH({exp})
    ) u_cell (
      .clk, .rst_n, .int_valid_i(int_valid_i[i]), .int_clear_i(int_clear_i[i]),
      .fp_valid_i(fp_valid_i[i]), .int_w_i(int_w_i[i*4 +: 4]),
      .int_a_i(int_a_i[i*8 +: 8]), .fp_a_i(fp_a_i[i*8 +: 8]),
      .fp_b_i(fp_b_i[i*8 +: 8]), .fp_c_i(fp_c_i[i*8 +: 8]),
      .rnd_i(rnd_i[i*3 +: 3]),
      .int_valid_o(int_valid_o[i]), .fp_valid_o(fp_valid_o[i]),
      .int_acc_o(int_acc_o[i*40 +: 40]), .fp_z_o(fp_z_o[i*8 +: 8]),
      .fp_status_o(fp_status_o[i*8 +: 8])
    );
  end endgenerate
endmodule
"""
    return f"""
module char_top(
  input logic clk, rst_n,
  input logic [{cells-1}:0] mode_fp_i, valid_i, clear_i,
  input logic signed [{cells*w-1}:0] int_w_i,
  input logic signed [{cells*a-1}:0] int_a_i,
  input logic [{cells*fpw-1}:0] fp_a_i, fp_b_i, fp_c_i,
  input logic [{cells*3-1}:0] rnd_i,
  output logic [{cells-1}:0] valid_o,
  output logic signed [{cells*40-1}:0] int_result_o,
  output logic [{cells*fpw-1}:0] fp_result_o
);
  genvar i;
  generate for (i=0; i<{cells}; i=i+1) begin : G
    dual_domain_int_fp_reference #(
      .INT_W_W({w}), .INT_A_W({a}), .INT_LANES(1), .INT_ACC_W(40),
      .FP_SIG_WIDTH({sig}), .FP_EXP_WIDTH({exp})
    ) u_cell (
      .clk, .rst_n, .mode_fp_i(mode_fp_i[i]), .valid_i(valid_i[i]),
      .clear_i(clear_i[i]), .int_w_i(int_w_i[i*4 +: 4]),
      .int_a_i(int_a_i[i*8 +: 8]), .fp_a_i(fp_a_i[i*8 +: 8]),
      .fp_b_i(fp_b_i[i*8 +: 8]), .fp_c_i(fp_c_i[i*8 +: 8]),
      .rnd_i(rnd_i[i*3 +: 3]),
      .valid_o(valid_o[i]), .int_result_o(int_result_o[i*40 +: 40]),
      .fp_result_o(fp_result_o[i*8 +: 8])
    );
  end endgenerate
endmodule
"""


def wrapper_and_sources(row: dict[str, str]) -> tuple[str, list[Path]]:
    topology = row["rtl_topology"]
    parent_rtl = PARENT_ROOT / "rtl"
    plan_rtl = PLAN_ROOT / "rtl"
    if topology == "existing_packed_dot":
        return emit_reference_int(row), [parent_rtl / "packed_dot_pe.sv"]
    if topology == "existing_fp_mac":
        return emit_reference_fp(row), [parent_rtl / "fp_mac_dw.sv"]
    if topology == "separate_int_fp_reference":
        return emit_separate(row), [parent_rtl / "packed_dot_pe.sv", parent_rtl / "fp_mac_dw.sv", plan_rtl / "separate_int_fp_reference.sv"]
    if topology == "dual_domain_int_fp_reference":
        return emit_dual(row), [parent_rtl / "packed_dot_pe.sv", parent_rtl / "fp_mac_dw.sv", plan_rtl / "dual_domain_int_fp_reference.sv"]
    if topology == "hybrid_convert_fp_mac_dw":
        return emit_convert(row), [plan_rtl / "hybrid_convert_fp_mac_dw.sv"]
    if topology == "hybrid_shared_mul_dual_acc":
        return emit_shared(row), [plan_rtl / "hybrid_shared_mul_dual_acc.sv"]
    if topology in {"generated_4x4_separate", "generated_4x4_dual"}:
        module = "separate_int_fp_reference.sv" if topology.endswith("separate") else "dual_domain_int_fp_reference.sv"
        return emit_array(row), [parent_rtl / "packed_dot_pe.sv", parent_rtl / "fp_mac_dw.sv", plan_rtl / module]
    raise ValueError(f"Unsupported topology: {topology}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", action="append")
    parser.add_argument("--periods", nargs="*", type=float)
    args = parser.parse_args()
    cfg = json.loads((PLAN_ROOT / "config/mixed_characterization.json").read_text())
    with (PLAN_ROOT / "config/mixed_experiment_groups.csv").open(encoding="utf-8-sig") as f:
        groups = list(csv.DictReader(f))
    requested = set(args.group or [])
    if requested:
        groups = [row for row in groups if row["group_id"] in requested]
        missing = requested - {row["group_id"] for row in groups}
        if missing:
            raise SystemExit(f"Unknown groups: {sorted(missing)}")
    periods = args.periods or cfg["clock_periods_ns"]
    bundle_sources = sorted((PLAN_ROOT / "rtl").glob("*.sv")) + sorted((PARENT_ROOT / "rtl").glob("*.sv"))
    bundle_sha = digest_sources(bundle_sources)
    BUILD.mkdir(exist_ok=True)
    rows: list[dict[str, object]] = []
    for group in groups:
        wrapper_text, sources = wrapper_and_sources(group)
        for period in periods:
            run_id = f'{group["group_id"]}__T{str(period).replace(".", "p")}ns'
            run_dir = (BUILD / run_id).resolve()
            run_dir.mkdir(parents=True, exist_ok=True)
            wrapper = run_dir / "char_top.sv"
            wrapper.write_text(wrapper_text.strip() + "\n", encoding="utf-8")
            rtl_list = run_dir / "rtl_files.list"
            rtl_list.write_text("\n".join(str(path.resolve()) for path in sources + [wrapper]) + "\n", encoding="utf-8")
            meta: dict[str, object] = {**group, "run_id": run_id, "clock_period_ns": period, "clock_mhz": 1000.0 / period, "run_dir": str(run_dir), "rtl_list": str(rtl_list.resolve()), "rtl_bundle_sha256": bundle_sha}
            (run_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
            rows.append(meta)
    fields = list(rows[0])
    for output in (BUILD / "runs.csv", PLAN_ROOT / "results/mixed_expected_runs.csv"):
        with output.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    print(f"Generated {len(groups)} groups and {len(rows)} DC runs")
    print(f"RTL bundle SHA-256: {bundle_sha}")


if __name__ == "__main__":
    main()

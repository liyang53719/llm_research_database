#!/usr/bin/env python3
from __future__ import annotations

import csv
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_dw_sim_env = os.environ.get("DW_SIM")
_synopsys_env = os.environ.get("SYNOPSYS")
DW_SIM = (
    Path(_dw_sim_env)
    if _dw_sim_env
    else Path(_synopsys_env) / "dw/sim_ver"
    if _synopsys_env
    else Path()
)
sys.path.insert(0, str(ROOT / "model"))
from numeric_formats import OperandFormat, conversion_coverage, encode_operand, sign_extend  # noqa: E402

CASES = (
    ("dw_i4_to_fp8", 4, 3, 4, OperandFormat.INT4, OperandFormat.FP8_E4M3FN),
    ("dw_i8_to_fp8", 8, 3, 4, OperandFormat.INT8, OperandFormat.FP8_E4M3FN),
    ("dw_i4_to_bf16", 4, 7, 8, OperandFormat.INT4, OperandFormat.BF16),
    ("dw_i8_to_bf16", 8, 7, 8, OperandFormat.INT8, OperandFormat.BF16),
)


def tb_text(int_width: int, sig: int, exp: int, count: int, fmt: int) -> str:
    fpw = sig + exp + 1
    return f"""
module tb;
  logic clk=0,rst_n=1,valid_i=0;
  logic [1:0] a_format_i={fmt},b_format_i={fmt};
  logic [15:0] a_bits_i=16'hffff,b_bits_i=16'hffff;
  logic [{fpw-1}:0] acc_i=0;
  logic [2:0] rnd_i=0;
  logic valid_o; logic [{fpw-1}:0] z_o; logic [7:0] status_o;
  integer i;
  hybrid_convert_fp_mac_dw #(
    .SIG_WIDTH({sig}),.EXP_WIDTH({exp}),.IEEE_COMPLIANCE(0),.INT_WIDTH({int_width})
  ) dut(.*);
  initial begin
    #1;
    for(i=0;i<{count};i=i+1) begin
      a_bits_i=i; b_bits_i=i; #10;
      $display("CODE=%0d RAW=%0h STATUS=%0h",i,dut.a_int_fp,dut.a_status);
    end
    $finish;
  end
endmodule
"""


def main() -> None:
    if not _dw_sim_env and not _synopsys_env:
        raise SystemExit("Set DW_SIM or SYNOPSYS to the local DesignWare installation")
    if not DW_SIM.is_dir():
        raise SystemExit(f"Missing DesignWare simulation directory: {DW_SIM}")
    output_rows = []
    details = []
    with tempfile.TemporaryDirectory(prefix="dw_converter_crosscheck_") as temp:
        temp_root = Path(temp)
        for name, int_width, sig, exp, source_fmt, target_fmt in CASES:
            count = 1 << int_width
            tb = temp_root / f"{name}.sv"
            tb.write_text(tb_text(int_width, sig, exp, count, int(source_fmt)), encoding="utf-8")
            binary = temp_root / f"{name}.vvp"
            compile_process = subprocess.run(
                [
                    "iverilog", "-g2012", "-s", "tb", "-y", str(DW_SIM),
                    "-o", str(binary), str(ROOT / "rtl/hybrid_convert_fp_mac_dw.sv"), str(tb),
                ],
                text=True,
                capture_output=True,
            )
            if compile_process.returncode:
                raise SystemExit(compile_process.stdout + compile_process.stderr)
            run_process = subprocess.run(["vvp", str(binary)], text=True, capture_output=True)
            if run_process.returncode:
                raise SystemExit(run_process.stdout + run_process.stderr)
            observed = {}
            for line in run_process.stdout.splitlines():
                if line.startswith("CODE="):
                    fields = dict(item.split("=", 1) for item in line.split())
                    raw_text = fields["RAW"].lower()
                    observed[int(fields["CODE"])] = (
                        None if "x" in raw_text or "z" in raw_text else int(raw_text, 16)
                    )
            failures = 0
            for raw in range(count):
                signed = sign_extend(raw, int_width)
                expected = encode_operand(float(signed), target_fmt)
                actual = observed.get(raw)
                if actual != expected:
                    failures += 1
                    if len(details) < 100:
                        details.append(
                            {"case": name, "source_raw": raw, "source_value": signed, "expected_raw": expected, "actual_raw": actual}
                        )
            coverage = conversion_coverage(source_fmt, target_fmt)
            output_rows.append(
                {
                    "category": name,
                    "checks": count,
                    "failures": failures,
                    "source_exact_fraction": coverage.exact_fraction,
                    "source_max_abs_error": coverage.max_abs_error,
                }
            )

    combined = ROOT / "results/numeric_rtl_crosscheck.csv"
    existing = []
    if combined.exists():
        with combined.open(encoding="utf-8-sig") as handle:
            existing = list(csv.DictReader(handle))
    fields = ["category", "checks", "failures", "source_exact_fraction", "source_max_abs_error"]
    with combined.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(existing + output_rows)
    detail_path = ROOT / "results/dw_converter_failures.csv"
    if details:
        with detail_path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(details[0]))
            writer.writeheader()
            writer.writerows(details)
        raise SystemExit(f"DW converter crosscheck failed; see {detail_path}")
    if detail_path.exists():
        detail_path.unlink()
    print(f"DesignWare converter crosscheck passed: {output_rows}")


if __name__ == "__main__":
    main()

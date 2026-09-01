#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "model"))
from numeric_formats import OperandFormat, decode_operand, float32_to_u32  # noqa: E402


def expected_product(a_fmt: int, b_fmt: int, a_bits: int, b_bits: int) -> int:
    a = decode_operand(a_bits, OperandFormat(a_fmt))
    b = decode_operand(b_bits, OperandFormat(b_fmt))
    with np.errstate(invalid="ignore", over="ignore", under="ignore"):
        product = np.float32(a * b)
    if math.isnan(float(product)):
        return 0x7FC00000
    return float32_to_u32(float(product))


def make_vectors() -> list[tuple[int, int, int, int, int]]:
    fp8 = [0x00, 0x80, 0x01, 0x07, 0x08, 0x38, 0xB8, 0x7E, 0xFE, 0x7F]
    bf16 = [
        0x0000, 0x8000, 0x0001, 0x007F, 0x0080, 0x3F80,
        0xBF80, 0x7F80, 0xFF80, 0x7FC1, 0x7F7F,
    ]
    vectors: list[tuple[int, int, int, int, int]] = []

    def add(a_fmt: int, b_fmt: int, lhs: list[int], rhs: list[int]) -> None:
        for a_bits in lhs:
            for b_bits in rhs:
                vectors.append(
                    (a_fmt, b_fmt, a_bits, b_bits, expected_product(a_fmt, b_fmt, a_bits, b_bits))
                )

    add(0, 2, list(range(16)), fp8)
    add(1, 2, list(range(256)), fp8)
    add(0, 3, list(range(16)), bf16)
    add(1, 3, list(range(256)), bf16)
    add(2, 2, fp8, fp8)
    add(3, 3, bf16, bf16)
    add(2, 3, fp8, bf16)
    add(3, 2, bf16, fp8)
    return vectors


def testbench(vector_path: Path) -> str:
    escaped = str(vector_path).replace("\\", "\\\\")
    return f"""
module tb;
  logic clk=0,rst_n=1,valid_i=0,clear_i=0;
  logic [1:0] a_format_i,b_format_i;
  logic [15:0] a_bits_i,b_bits_i;
  logic [2:0] rnd_i=0;
  logic valid_o; logic signed [39:0] int_acc_o;
  logic [31:0] fp_acc_o; logic [7:0] fp_status_o;
  integer ai,bi,fa,fb,checks_i,checks_f,failures,fd,rc;
  reg [31:0] expected;
  integer expected_signed;

  hybrid_shared_mul_dual_acc dut(.*);

  function integer sx4(input integer raw);
    sx4 = (raw & 8) ? raw-16 : raw;
  endfunction
  function integer sx8(input integer raw);
    sx8 = (raw & 128) ? raw-256 : raw;
  endfunction

  task check_int(input integer af,input integer bf,input integer av,input integer bv,input integer ev);
    begin
      a_format_i=af; b_format_i=bf; a_bits_i=av; b_bits_i=bv; #1;
      checks_i=checks_i+1;
      if($signed(dut.signed_product)!==ev) begin
        failures=failures+1;
        if(failures<10) $display("INT_FAIL af=%0d bf=%0d a=%0h b=%0h got=%0d exp=%0d",af,bf,av,bv,$signed(dut.signed_product),ev);
      end
    end
  endtask

  initial begin
    checks_i=0; checks_f=0; failures=0;
    for(ai=0;ai<16;ai=ai+1) for(bi=0;bi<16;bi=bi+1)
      check_int(0,0,ai,bi,sx4(ai)*sx4(bi));
    for(ai=0;ai<256;ai=ai+1) for(bi=0;bi<256;bi=bi+1)
      check_int(1,1,ai,bi,sx8(ai)*sx8(bi));
    for(ai=0;ai<16;ai=ai+1) for(bi=0;bi<256;bi=bi+1)
      check_int(0,1,ai,bi,sx4(ai)*sx8(bi));
    for(ai=0;ai<256;ai=ai+1) for(bi=0;bi<16;bi=bi+1)
      check_int(1,0,ai,bi,sx8(ai)*sx4(bi));

    fd=$fopen("{escaped}","r");
    if(fd==0) $fatal(1,"vector file open failed");
    while(!$feof(fd)) begin
      rc=$fscanf(fd,"%d %d %h %h %h\\n",fa,fb,a_bits_i,b_bits_i,expected);
      if(rc==5) begin
        a_format_i=fa; b_format_i=fb; #1; checks_f=checks_f+1;
        if(dut.product_fp32!==expected) begin
          failures=failures+1;
          if(failures<10) $display("FP_FAIL af=%0d bf=%0d a=%0h b=%0h got=%08h exp=%08h",fa,fb,a_bits_i,b_bits_i,dut.product_fp32,expected);
        end
      end
    end
    $fclose(fd);
    $display("INTEGER_CHECKS=%0d",checks_i);
    $display("FLOAT_CHECKS=%0d",checks_f);
    $display("FAILURES=%0d",failures);
    if(failures) $fatal(1,"numeric crosscheck failed");
    $finish;
  end
endmodule
"""


def main() -> None:
    vectors = make_vectors()
    results = ROOT / "results/numeric_rtl_crosscheck.csv"
    failures_file = ROOT / "results/numeric_rtl_failures.txt"
    with tempfile.TemporaryDirectory(prefix="mixed_numeric_crosscheck_") as temp:
        temp_root = Path(temp)
        vector_path = temp_root / "vectors.txt"
        with vector_path.open("w", encoding="ascii") as handle:
            for row in vectors:
                handle.write(f"{row[0]} {row[1]} {row[2]:04x} {row[3]:04x} {row[4]:08x}\n")
        tb_path = temp_root / "tb.sv"
        tb_path.write_text(testbench(vector_path), encoding="utf-8")
        output = temp_root / "crosscheck.vvp"
        compile_process = subprocess.run(
            [
                "iverilog", "-g2012", "-s", "tb", "-o", str(output),
                str(ROOT / "tests/dw_sim_stubs.sv"),
                str(ROOT / "rtl/hybrid_shared_mul_dual_acc.sv"), str(tb_path),
            ],
            text=True,
            capture_output=True,
        )
        if compile_process.returncode:
            failures_file.write_text(compile_process.stdout + compile_process.stderr, encoding="utf-8")
            raise SystemExit("Icarus compile failed; see numeric_rtl_failures.txt")
        run_process = subprocess.run(["vvp", str(output)], text=True, capture_output=True)
        output_text = run_process.stdout + run_process.stderr
        parsed = {}
        for line in output_text.splitlines():
            if "=" in line and line.split("=", 1)[0] in {"INTEGER_CHECKS", "FLOAT_CHECKS", "FAILURES"}:
                key, value = line.split("=", 1)
                parsed[key] = int(value)
        rows = [
            {"category": "integer_exhaustive", "checks": parsed.get("INTEGER_CHECKS", 0), "failures": parsed.get("FAILURES", -1) if not run_process.returncode else -1},
            {"category": "float_directed_stratified", "checks": parsed.get("FLOAT_CHECKS", 0), "failures": parsed.get("FAILURES", -1) if not run_process.returncode else -1},
        ]
        with results.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        if run_process.returncode:
            failures_file.write_text(output_text, encoding="utf-8")
            raise SystemExit("Numeric RTL crosscheck failed; see numeric_rtl_failures.txt")
        if failures_file.exists():
            failures_file.unlink()
    print(f"Numeric RTL crosscheck passed: {rows}")


if __name__ == "__main__":
    main()

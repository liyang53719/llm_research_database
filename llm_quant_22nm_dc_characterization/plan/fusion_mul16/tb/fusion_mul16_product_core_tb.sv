module fusion_mul16_product_core_tb;
  logic [3:0] mode_i;
  logic [15:0] lhs_i [0:15];
  logic [15:0] rhs_i [0:15];
  logic signed [32:0] int_product_o [0:15];
  logic [31:0] fp_product_o [0:15];
  logic [15:0] product_valid_o;
  logic [4:0] product_count_o;

  logic [32:0] expected [0:15];
  logic [15:0] expected_valid;
  integer expected_count;
  integer mode_value;
  integer fd;
  integer rc;
  integer i;
  integer vectors;
  integer checks;
  integer fails;
  reg [2047:0] vector_file;

  fusion_mul16_product_core dut (.*);

  initial begin
    vectors = 0;
    checks = 0;
    fails = 0;
    if (!$value$plusargs("vectors=%s", vector_file)) begin
      $display("ERROR missing +vectors=<file>");
      $fatal(1, "missing vector file");
    end
    fd = $fopen(vector_file, "r");
    if (fd == 0) begin
      $display("ERROR cannot open vectors");
      $fatal(1, "cannot open vector file");
    end
    while (!$feof(fd)) begin
      rc = $fscanf(fd, "%d %h %d", mode_value, expected_valid, expected_count);
      if (rc == 3) begin
        for (i = 0; i < 16; i = i + 1) rc = rc + $fscanf(fd, " %h", lhs_i[i]);
        for (i = 0; i < 16; i = i + 1) rc = rc + $fscanf(fd, " %h", rhs_i[i]);
        for (i = 0; i < 16; i = i + 1) rc = rc + $fscanf(fd, " %h", expected[i]);
        mode_i = mode_value[3:0];
        #1;
        vectors = vectors + 1;
        checks = checks + 2;
        if (product_valid_o !== expected_valid) fails = fails + 1;
        if (product_count_o !== expected_count[4:0]) fails = fails + 1;
        for (i = 0; i < expected_count; i = i + 1) begin
          checks = checks + 1;
          if (mode_value <= 3) begin
            if (int_product_o[i] !== expected[i]) begin
              if (fails < 8) $display("MISMATCH vector=%0d lane=%0d got=%h expected=%h", vectors, i, int_product_o[i], expected[i]);
              fails = fails + 1;
            end
          end else begin
            if (fp_product_o[i] !== expected[i][31:0]) begin
              if (fails < 8) $display("MISMATCH vector=%0d lane=%0d got=%h expected=%h", vectors, i, fp_product_o[i], expected[i][31:0]);
              fails = fails + 1;
            end
          end
        end
      end
    end
    $fclose(fd);
    $display("RESULT vectors=%0d checks=%0d fails=%0d", vectors, checks, fails);
    if (fails != 0) $fatal(1, "RTL mismatches detected");
    $finish;
  end
endmodule

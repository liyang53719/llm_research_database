proc require_env {name} {
  if {![info exists ::env($name)] || $::env($name) eq ""} {
    error "Required environment variable $name is not set"
  }
  return $::env($name)
}

set RUN_ID      [require_env RUN_ID]
set RUN_DIR     [require_env RUN_DIR]
set RTL_LIST    [require_env RTL_LIST]
set LIB_SETUP   [require_env LIB_SETUP]
set CLK_PERIOD  [expr {double([require_env CLK_PERIOD_NS])}]
set RTL_INPUT_SHA256 [require_env RTL_INPUT_SHA256]
set DC_MAX_CORES [expr {int([require_env DC_MAX_CORES])}]
set LIBRARY_SETUP_SHA256 [require_env LIBRARY_SETUP_SHA256]
if {$DC_MAX_CORES < 1 || $DC_MAX_CORES > 2} { error "DC_MAX_CORES must be 1 or 2" }
set_host_options -max_cores $DC_MAX_CORES
set TOP         "char_top"
set EXTRA_CONSTRAINT_TCL ""
if {[info exists ::env(EXTRA_CONSTRAINT_TCL)]} {
  set EXTRA_CONSTRAINT_TCL $::env(EXTRA_CONSTRAINT_TCL)
}

file mkdir $RUN_DIR/reports
file mkdir $RUN_DIR/netlist
source $LIB_SETUP

set_app_var search_path [concat $search_path $SEARCH_PATHS]
set_app_var target_library $TARGET_LIBRARIES
set_app_var synthetic_library [list dw_foundation.sldb]
set_app_var link_library [concat "*" $TARGET_LIBRARIES $ADDITIONAL_LINK_LIBS $synthetic_library]

set fp [open $RTL_LIST r]
set rtl_files [list]
foreach f [split [read $fp] "\n"] {
  if {[string trim $f] ne ""} { lappend rtl_files [string trim $f] }
}
close $fp

redirect -file $RUN_DIR/reports/analyze.log {
  analyze -format sverilog -define FUSION_USE_DW $rtl_files
  elaborate $TOP
  current_design $TOP
  link
  uniquify
  check_design
}

set_fix_multiple_port_nets -all -buffer_constants [get_designs *]
create_clock -name clk -period $CLK_PERIOD [get_ports clk]
set_clock_uncertainty [expr {$CLOCK_UNCERTAINTY_RATIO * $CLK_PERIOD}] [get_clocks clk]
set data_inputs [remove_from_collection [all_inputs] [get_ports -quiet {clk rst_n}]]
if {[sizeof_collection $data_inputs] > 0} {
  set_input_transition $INPUT_TRANSITION $data_inputs
  set_input_delay [expr {$INPUT_DELAY_RATIO * $CLK_PERIOD}] -clock clk $data_inputs
}
if {[sizeof_collection [all_outputs]] > 0} {
  set_load $OUTPUT_LOAD [all_outputs]
  set_output_delay [expr {$OUTPUT_DELAY_RATIO * $CLK_PERIOD}] -clock clk [all_outputs]
}
set_max_transition $MAX_TRANSITION [current_design]
set_max_area 0

set brick_count_pre [sizeof_collection [get_cells -hierarchical -quiet -filter "ref_name =~ mul4x4_brick*"]]
set dw_mult_count_pre [sizeof_collection [get_cells -hierarchical -quiet *u_dw_mult*]]
redirect -file $RUN_DIR/reports/report_resources_pre.rpt { report_resources -hierarchy }
redirect -file $RUN_DIR/reports/report_reference_pre.rpt { report_reference -hierarchy }
set brick_cells [get_cells -hierarchical -quiet -filter "ref_name =~ mul4x4_brick*"]
if {[sizeof_collection $brick_cells] > 0} {
  set_dont_touch $brick_cells
  set_ungroup $brick_cells false
}

set multicycle_applied 0
if {$EXTRA_CONSTRAINT_TCL ne ""} {
  if {![file exists $EXTRA_CONSTRAINT_TCL]} {
    error "Extra constraint file does not exist: $EXTRA_CONSTRAINT_TCL"
  }
  source $EXTRA_CONSTRAINT_TCL
  set multicycle_applied 1
}

if {$COMPILE_MODE eq "ultra"} {
  compile_ultra
} else {
  compile -map_effort high
}

redirect -file $RUN_DIR/reports/report_qor.rpt { report_qor }
redirect -file $RUN_DIR/reports/report_area.rpt { report_area -hierarchy }
redirect -file $RUN_DIR/reports/report_timing.rpt {
  report_timing -delay_type max -max_paths 30 -nworst 10 -nets -transition_time -capacitance
}
redirect -file $RUN_DIR/reports/report_constraints.rpt { report_constraint -all_violators }
redirect -file $RUN_DIR/reports/report_resources.rpt { report_resources -hierarchy }
redirect -file $RUN_DIR/reports/report_reference.rpt { report_reference -hierarchy }
# X-2025.06-SP3 does not provide report_exceptions.  Keep the required public
# report name while using the supported constraint/timing reports to expose
# all active exceptions and the checkpoint endpoint paths.
set ex_fp [open $RUN_DIR/reports/report_exceptions.rpt w]
puts $ex_fp "FusionMul16 v3 timing-exception evidence"
puts $ex_fp "dc_command=report_exceptions (unsupported in this DC release)"
puts $ex_fp "supported_constraint_report_begin"
set ex_constraints_file "$RUN_DIR/reports/report_exceptions_supported.rpt"
redirect -file $ex_constraints_file { report_constraint -verbose }
set ex_cf [open $ex_constraints_file r]
puts $ex_fp [read $ex_cf]
close $ex_cf
puts $ex_fp "supported_constraint_report_end"
puts $ex_fp "checkpoint_path_report_begin"
set ex_from [get_cells -hierarchical -quiet *checkpoint_base_q_reg*]
set ex_term [get_cells -hierarchical -quiet *checkpoint_term_q_reg*]
set ex_from [add_to_collection $ex_from $ex_term]
set ex_to [get_cells -hierarchical -quiet *checkpoint_fp32_o_reg*]
if {[sizeof_collection $ex_from] > 0 && [sizeof_collection $ex_to] > 0} {
  set ex_from_pins [get_pins -of_objects $ex_from -filter "full_name =~ */Q"]
  set ex_to_pins [get_pins -of_objects $ex_to -filter "full_name =~ */next_state"]
  set ex_paths_file "$RUN_DIR/reports/report_exceptions_paths.rpt"
  redirect -file $ex_paths_file { report_timing -from $ex_from_pins -to $ex_to_pins -delay_type max -max_paths 30 -nworst 10 -path_type full_clock_expanded }
  set ex_pf [open $ex_paths_file r]
  puts $ex_fp [read $ex_pf]
  close $ex_pf
} else {
  puts $ex_fp "checkpoint_endpoint_cells_missing=1"
}
puts $ex_fp "checkpoint_path_report_end"
close $ex_fp
redirect -file $RUN_DIR/reports/check_design_post.rpt { check_design; check_timing }

write -format ddc -hierarchy -output $RUN_DIR/netlist/$TOP.ddc
write_file -format verilog -hierarchy -output $RUN_DIR/netlist/$TOP.v
write_sdc $RUN_DIR/netlist/$TOP.sdc

set design_area [get_attribute [current_design] area]
if {$design_area eq "" || double($design_area) <= 0.0} {
  set design_area 0.0
  foreach_in_collection leaf [get_cells -hierarchical -filter "is_hierarchical == false"] {
    set leaf_area [get_attribute $leaf area]
    if {$leaf_area ne ""} { set design_area [expr {$design_area + double($leaf_area)}] }
  }
}
set leaf_count [sizeof_collection [get_cells -hierarchical -filter "is_hierarchical == false"]]
set blackbox_count [sizeof_collection [get_designs -hierarchical -filter "is_black_box == true"]]
set path_col [get_timing_paths -delay_type max -max_paths 1 -nworst 1]
set wns "NA"
set critical_delay "NA"
set achieved_fmax "NA"
set timing_met "NA"
if {[sizeof_collection $path_col] > 0} {
  set wns [get_attribute $path_col slack]
  set critical_delay [expr {$CLK_PERIOD - $wns}]
  if {$critical_delay > 0.0} { set achieved_fmax [expr {1000.0 / $critical_delay}] }
  set timing_met [expr {$wns >= 0.0 ? 1 : 0}]
}

set sf [open $RUN_DIR/summary.kv w]
puts $sf "run_id=$RUN_ID"
puts $sf "top=$TOP"
puts $sf "library_set_id=$LIBRARY_SET_ID"
puts $sf "target_libraries=$TARGET_LIBRARIES"
puts $sf "compile_mode=$COMPILE_MODE"
puts $sf "clock_period_ns=$CLK_PERIOD"
puts $sf "clock_mhz=[expr {1000.0/$CLK_PERIOD}]"
puts $sf "mapped_cell_area_um2=$design_area"
puts $sf "leaf_cell_count=$leaf_count"
puts $sf "blackbox_count=$blackbox_count"
puts $sf "wns_ns=$wns"
puts $sf "critical_delay_ns=$critical_delay"
puts $sf "achieved_fmax_mhz=$achieved_fmax"
puts $sf "timing_met=$timing_met"
puts $sf "multicycle_applied=$multicycle_applied"
puts $sf "extra_constraint_tcl=$EXTRA_CONSTRAINT_TCL"
puts $sf "tool_version=[get_app_var sh_product_version]"
puts $sf "rtl_input_sha256=$RTL_INPUT_SHA256"
puts $sf "dc_max_cores=$DC_MAX_CORES"
puts $sf "library_setup_sha256=$LIBRARY_SETUP_SHA256"
puts $sf "brick_instance_count_precompile=$brick_count_pre"
puts $sf "dw_mult_instance_count_precompile=$dw_mult_count_pre"
close $sf
quit

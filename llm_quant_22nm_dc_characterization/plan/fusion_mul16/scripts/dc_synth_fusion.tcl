proc require_env {name} {
  if {![info exists ::env($name)] || $::env($name) eq ""} {
    error "Required environment variable $name is not set"
  }
  return $::env($name)
}

set RUN_ID       [require_env RUN_ID]
set RUN_DIR      [require_env RUN_DIR]
set RTL_LIST     [require_env RTL_LIST]
set LIB_SETUP    [require_env LIB_SETUP]
set TOP          [require_env TOP]
set CLK_PERIOD   [expr {double([require_env CLK_PERIOD_NS])}]
set KEEP_BRICKS  [expr {int([require_env KEEP_BRICKS])}]
set RTL_BUNDLE_SHA256 [require_env RTL_BUNDLE_SHA256]
set DC_MAX_CORES [expr {int([require_env DC_MAX_CORES])}]
set LIBRARY_SETUP_SHA256 [require_env LIBRARY_SETUP_SHA256]

if {$DC_MAX_CORES < 1 || $DC_MAX_CORES > 2} {
  error "DC_MAX_CORES must be 1 or 2"
}
set_host_options -max_cores $DC_MAX_CORES

file mkdir $RUN_DIR/reports
file mkdir $RUN_DIR/netlist
source $LIB_SETUP

set_app_var search_path [concat $search_path $SEARCH_PATHS]
set_app_var target_library $TARGET_LIBRARIES
set_app_var synthetic_library [list dw_foundation.sldb]
set_app_var link_library [concat "*" $TARGET_LIBRARIES $ADDITIONAL_LINK_LIBS $synthetic_library]

set fp [open $RTL_LIST r]
set raw_files [split [read $fp] "\n"]
close $fp
set rtl_files [list]
foreach file $raw_files {
  if {[string trim $file] ne ""} {
    lappend rtl_files [string trim $file]
  }
}

redirect -file $RUN_DIR/reports/analyze.log {
  analyze -format sverilog -define FUSION_USE_DW $rtl_files
  elaborate $TOP
  current_design $TOP
  link
  uniquify
  check_design
}

set brick_count_pre [sizeof_collection [get_cells -hierarchical -quiet -filter "ref_name =~ mul4x4_brick*"]]
set dw_mult_count_pre [sizeof_collection [get_cells -hierarchical -quiet *u_dw_mult*]]

redirect -file $RUN_DIR/reports/report_resources_pre.rpt {
  report_resources -hierarchy
}
redirect -file $RUN_DIR/reports/report_reference_pre.rpt {
  report_reference -hierarchy
}

if {$KEEP_BRICKS} {
  set brick_cells [get_cells -hierarchical -quiet -filter "ref_name =~ mul4x4_brick*"]
  if {[sizeof_collection $brick_cells] > 0} {
    set_dont_touch $brick_cells
    set_ungroup $brick_cells false
  }
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

compile_ultra

redirect -file $RUN_DIR/reports/report_qor.rpt { report_qor }
redirect -file $RUN_DIR/reports/report_area.rpt { report_area -hierarchy }
redirect -file $RUN_DIR/reports/report_timing.rpt {
  report_timing -delay_type max -max_paths 20 -nworst 5 -nets -transition_time -capacitance
}
redirect -file $RUN_DIR/reports/report_resources_post.rpt { report_resources -hierarchy }
redirect -file $RUN_DIR/reports/report_reference_post.rpt { report_reference -hierarchy }
redirect -file $RUN_DIR/reports/report_constraints.rpt { report_constraint -all_violators }
redirect -file $RUN_DIR/reports/check_design_post.rpt { check_design; check_timing }

write -format ddc -hierarchy -output $RUN_DIR/netlist/$TOP.ddc
write_file -format verilog -hierarchy -output $RUN_DIR/netlist/$TOP.v
write_sdc $RUN_DIR/netlist/$TOP.sdc

set design_area 0.0
foreach_in_collection leaf [get_cells -hierarchical -filter "is_hierarchical == false"] {
  set leaf_area [get_attribute $leaf area]
  if {$leaf_area ne ""} {
    set design_area [expr {$design_area + double($leaf_area)}]
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
puts $sf "clock_period_ns=$CLK_PERIOD"
puts $sf "clock_mhz=[expr {1000.0/$CLK_PERIOD}]"
puts $sf "mapped_cell_area_um2=$design_area"
puts $sf "leaf_cell_count=$leaf_count"
puts $sf "blackbox_count=$blackbox_count"
puts $sf "brick_instance_count_precompile=$brick_count_pre"
puts $sf "dw_mult_instance_count_precompile=$dw_mult_count_pre"
puts $sf "wns_ns=$wns"
puts $sf "critical_delay_ns=$critical_delay"
puts $sf "achieved_fmax_mhz=$achieved_fmax"
puts $sf "timing_met=$timing_met"
puts $sf "tool_version=[get_app_var sh_product_version]"
puts $sf "rtl_bundle_sha256=$RTL_BUNDLE_SHA256"
puts $sf "dc_max_cores=$DC_MAX_CORES"
puts $sf "library_setup_sha256=$LIBRARY_SETUP_SHA256"
puts $sf "compile_mode=compile_ultra"
puts $sf "input_transition=$INPUT_TRANSITION"
puts $sf "output_load=$OUTPUT_LOAD"
puts $sf "max_transition=$MAX_TRANSITION"
puts $sf "clock_uncertainty_ratio=$CLOCK_UNCERTAINTY_RATIO"
puts $sf "input_delay_ratio=$INPUT_DELAY_RATIO"
puts $sf "output_delay_ratio=$OUTPUT_DELAY_RATIO"
close $sf
quit

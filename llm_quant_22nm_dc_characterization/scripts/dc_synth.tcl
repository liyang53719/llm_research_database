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
set TOP         "char_top"

file mkdir $RUN_DIR/reports
file mkdir $RUN_DIR/netlist
file mkdir $RUN_DIR/work
define_design_lib WORK -path $RUN_DIR/work

source $LIB_SETUP

if {![info exists MAX_CORES]} {
  set MAX_CORES 1
}
if {[info exists ::env(DC_MAX_CORES)] && $::env(DC_MAX_CORES) ne ""} {
  set MAX_CORES [expr {int($::env(DC_MAX_CORES))}]
}
if {$MAX_CORES < 1 || $MAX_CORES > 2} {
  error "MAX_CORES must be in the range 1..2"
}
set_host_options -max_cores $MAX_CORES

set_app_var search_path [concat $search_path $SEARCH_PATHS]
set_app_var target_library $TARGET_LIBRARIES
set SYNTHETIC_LIBRARIES [list dw_foundation.sldb]
set_app_var synthetic_library $SYNTHETIC_LIBRARIES
set_app_var link_library [concat "*" $TARGET_LIBRARIES $ADDITIONAL_LINK_LIBS $SYNTHETIC_LIBRARIES]

set fp [open $RTL_LIST r]
set raw_files [split [read $fp] "\n"]
close $fp
set rtl_files [list]
foreach f $raw_files {
  if {[string trim $f] ne ""} {
    lappend rtl_files [string trim $f]
  }
}

redirect -file $RUN_DIR/reports/analyze.log {
  analyze -format sverilog $rtl_files
  elaborate $TOP
  current_design $TOP
  link
  uniquify
  if {$OPERATING_CONDITION ne ""} {
    set_operating_conditions $OPERATING_CONDITION
  }
  check_design
}

set_fix_multiple_port_nets -all -buffer_constants [get_designs *]

if {[sizeof_collection [get_ports -quiet clk]] > 0} {
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
}
set_max_transition $MAX_TRANSITION [current_design]
set_max_area 0

if {$KEEP_HIERARCHY} {
  set_ungroup [get_cells -hierarchical -filter "is_hierarchical == true"] false
}

if {$COMPILE_MODE eq "ultra"} {
  if {$KEEP_HIERARCHY} {
    compile_ultra -no_autoungroup
  } else {
    compile_ultra
  }
} else {
  compile -map_effort high
}

if {[llength [info commands analyze_datapath_extraction]] > 0} {
  redirect -file $RUN_DIR/reports/datapath_extraction.rpt {
    analyze_datapath_extraction
  }
}

redirect -file $RUN_DIR/reports/report_qor.rpt {
  report_qor
}
redirect -file $RUN_DIR/reports/report_area.rpt {
  report_area -hierarchy
}
redirect -file $RUN_DIR/reports/report_timing.rpt {
  report_timing -delay_type max -max_paths 20 -nworst 5 -nets -transition_time -capacitance
}
redirect -file $RUN_DIR/reports/report_constraints.rpt {
  report_constraint -all_violators
}
redirect -file $RUN_DIR/reports/report_resources.rpt {
  report_resources -hierarchy
}
redirect -file $RUN_DIR/reports/report_reference.rpt {
  report_reference -hierarchy
}
redirect -file $RUN_DIR/reports/check_design_post.rpt {
  check_design
  check_timing
}

if {$ENABLE_POWER_REPORT} {
  redirect -file $RUN_DIR/reports/report_power.rpt {
    report_power -hierarchy
  }
}

write -format ddc -hierarchy -output $RUN_DIR/netlist/$TOP.ddc
write_file -format verilog -hierarchy -output $RUN_DIR/netlist/$TOP.v
write_sdc $RUN_DIR/netlist/$TOP.sdc

set design_area [get_attribute [current_design] area]
set leaf_count [sizeof_collection [get_cells -hierarchical -filter "is_hierarchical == false"]]
set blackbox_count [sizeof_collection [get_designs * -filter "is_black_box == true"]]
set path_col [get_timing_paths -delay_type max -max_paths 1 -nworst 1]
set wns "NA"
set critical_delay "NA"
set achieved_fmax "NA"
set timing_met "NA"
if {[sizeof_collection $path_col] > 0} {
  set wns [get_attribute $path_col slack]
  set critical_delay [expr {$CLK_PERIOD - $wns}]
  if {$critical_delay > 0.0} {
    set achieved_fmax [expr {1000.0 / $critical_delay}]
  }
  set timing_met [expr {$wns >= 0.0 ? 1 : 0}]
}

set sf [open $RUN_DIR/summary.kv w]
puts $sf "run_id=$RUN_ID"
puts $sf "top=$TOP"
puts $sf "rtl_bundle_sha256=$::env(RTL_BUNDLE_SHA256)"
puts $sf "library_setup_sha256=$::env(LIB_SETUP_SHA256)"
puts $sf "library_set_id=$LIBRARY_SET_ID"
puts $sf "target_libraries=$TARGET_LIBRARIES"
puts $sf "compile_mode=$COMPILE_MODE"
puts $sf "keep_hierarchy=$KEEP_HIERARCHY"
puts $sf "operating_condition_requested=$OPERATING_CONDITION"
puts $sf "max_cores=$MAX_CORES"
puts $sf "clock_period_ns=$CLK_PERIOD"
puts $sf "clock_mhz=[expr {1000.0/$CLK_PERIOD}]"
puts $sf "mapped_cell_area_um2=$design_area"
puts $sf "leaf_cell_count=$leaf_count"
puts $sf "blackbox_count=$blackbox_count"
puts $sf "wns_ns=$wns"
puts $sf "critical_delay_ns=$critical_delay"
puts $sf "achieved_fmax_mhz=$achieved_fmax"
puts $sf "timing_met=$timing_met"
puts $sf "tool_version=[get_app_var sh_product_version]"
close $sf

quit

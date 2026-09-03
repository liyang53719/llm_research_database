proc require_env {name} {
  if {![info exists ::env($name)] || $::env($name) eq ""} { error "Required env $name missing" }
  return $::env($name)
}
set RUN_ID [require_env RUN_ID]
set RUN_DIR [require_env RUN_DIR]
set RTL_LIST [require_env RTL_LIST]
set LIB_SETUP [require_env LIB_SETUP]
set CLK_PERIOD [expr {double([require_env CLK_PERIOD_NS])}]
set RTL_INPUT_SHA256 [require_env RTL_INPUT_SHA256]
set DC_MAX_CORES [expr {int([require_env DC_MAX_CORES])}]
set LIBRARY_SETUP_SHA256 [require_env LIBRARY_SETUP_SHA256]
if {$DC_MAX_CORES < 1 || $DC_MAX_CORES > 2} { error "DC_MAX_CORES must be 1 or 2" }
set TOP char_top
file mkdir $RUN_DIR/reports
file mkdir $RUN_DIR/netlist
source $LIB_SETUP
set_host_options -max_cores $DC_MAX_CORES
set_app_var search_path [concat $search_path $SEARCH_PATHS]
set_app_var target_library $TARGET_LIBRARIES
set_app_var synthetic_library [list dw_foundation.sldb]
set_app_var link_library [concat "*" $TARGET_LIBRARIES $ADDITIONAL_LINK_LIBS $synthetic_library]
set fp [open $RTL_LIST r]
set rtl_files [list]
foreach f [split [read $fp] "\n"] { if {[string trim $f] ne ""} { lappend rtl_files [string trim $f] } }
close $fp
redirect -file $RUN_DIR/reports/analyze.log {
  analyze -format sverilog -define {FUSION_USE_DW} $rtl_files
  elaborate $TOP
  current_design $TOP
  link
  uniquify
  check_design
}
set brick_count_pre [sizeof_collection [get_cells -hierarchical -quiet *u_brick*]]
set dw_mult_count_pre [sizeof_collection [get_cells -hierarchical -quiet *u_dw_mult*]]
redirect -file $RUN_DIR/reports/report_resources_pre.rpt { report_resources -hierarchy }
redirect -file $RUN_DIR/reports/report_reference_pre.rpt { report_reference -hierarchy }
set_fix_multiple_port_nets -all -buffer_constants [get_designs *]
if {[sizeof_collection [get_ports -quiet clk]] > 0} {
  create_clock -name clk -period $CLK_PERIOD [get_ports clk]
  set_clock_uncertainty [expr {$CLOCK_UNCERTAINTY_RATIO*$CLK_PERIOD}] [get_clocks clk]
  set data_inputs [remove_from_collection [all_inputs] [get_ports -quiet {clk rst_n}]]
  if {[sizeof_collection $data_inputs] > 0} {
    set_input_transition $INPUT_TRANSITION $data_inputs
    set_input_delay [expr {$INPUT_DELAY_RATIO*$CLK_PERIOD}] -clock clk $data_inputs
  }
  if {[sizeof_collection [all_outputs]] > 0} {
    set_load $OUTPUT_LOAD [all_outputs]
    set_output_delay [expr {$OUTPUT_DELAY_RATIO*$CLK_PERIOD}] -clock clk [all_outputs]
  }
}
set_max_transition $MAX_TRANSITION [current_design]
set_max_area 0
if {$COMPILE_MODE eq "ultra"} { compile_ultra } else { compile -map_effort high }
redirect -file $RUN_DIR/reports/report_qor.rpt { report_qor }
redirect -file $RUN_DIR/reports/report_area.rpt { report_area -hierarchy }
redirect -file $RUN_DIR/reports/report_timing.rpt { report_timing -delay_type max -max_paths 30 -nworst 10 -nets -transition_time -capacitance }
redirect -file $RUN_DIR/reports/report_hold.rpt { report_timing -delay_type min -max_paths 30 -nworst 10 -nets }
redirect -file $RUN_DIR/reports/report_constraints.rpt { report_constraint -all_violators }
redirect -file $RUN_DIR/reports/report_resources.rpt { report_resources -hierarchy }
redirect -file $RUN_DIR/reports/report_reference.rpt { report_reference -hierarchy }
redirect -file $RUN_DIR/reports/check_design_post.rpt { check_design; check_timing }
write -format ddc -hierarchy -output $RUN_DIR/netlist/$TOP.ddc
write_file -format verilog -hierarchy -output $RUN_DIR/netlist/$TOP.v
write_sdc $RUN_DIR/netlist/$TOP.sdc
set area [get_attribute [current_design] area]
if {$area eq "" || double($area) <= 0.0} {
  set area 0.0
  foreach_in_collection leaf_cell [get_cells -hierarchical -filter "is_hierarchical == false"] {
    set leaf_area [get_attribute $leaf_cell area]
    if {$leaf_area ne ""} { set area [expr {$area + double($leaf_area)}] }
  }
}
set leaf [sizeof_collection [get_cells -hierarchical -filter "is_hierarchical == false"]]
set bb [sizeof_collection [get_designs -hierarchical -filter "is_black_box == true"]]
set p [get_timing_paths -delay_type max -max_paths 1 -nworst 1]
set wns NA; set crit NA; set fmax NA; set met NA
if {[sizeof_collection $p] > 0} {
  set wns [get_attribute $p slack]
  set crit [expr {$CLK_PERIOD-$wns}]
  if {$crit>0} { set fmax [expr {1000.0/$crit}] }
  set met [expr {$wns>=0?1:0}]
}
set sf [open $RUN_DIR/summary.kv w]
puts $sf "run_id=$RUN_ID"
puts $sf "library_set_id=$LIBRARY_SET_ID"
puts $sf "target_libraries=$TARGET_LIBRARIES"
puts $sf "compile_mode=$COMPILE_MODE"
puts $sf "clock_period_ns=$CLK_PERIOD"
puts $sf "mapped_cell_area_um2=$area"
puts $sf "leaf_cell_count=$leaf"
puts $sf "blackbox_count=$bb"
puts $sf "brick_instance_count_precompile=$brick_count_pre"
puts $sf "dw_mult_instance_count_precompile=$dw_mult_count_pre"
puts $sf "wns_ns=$wns"
puts $sf "critical_delay_ns=$crit"
puts $sf "achieved_fmax_mhz=$fmax"
puts $sf "timing_met=$met"
puts $sf "tool_version=[get_app_var sh_product_version]"
puts $sf "rtl_input_sha256=$RTL_INPUT_SHA256"
puts $sf "library_setup_sha256=$LIBRARY_SETUP_SHA256"
puts $sf "dc_max_cores=$DC_MAX_CORES"
close $sf
quit

# Copy to config/library_setup.local.tcl before running.
# Point CLN22UL_DB at a locally licensed CLN22UL 0.80 V TT .db file.
if {![info exists ::env(CLN22UL_DB)] || $::env(CLN22UL_DB) eq ""} {
  error "Set CLN22UL_DB to the local licensed .db path"
}

set LIBRARY_SET_ID        "cln22ul_svt_tt_0p80v_25c"
set TARGET_LIBRARIES      [list $::env(CLN22UL_DB)]
set ADDITIONAL_LINK_LIBS  [list]
set SEARCH_PATHS          [list [file dirname $::env(CLN22UL_DB)]]
set OPERATING_CONDITION   ""
set INPUT_TRANSITION      0.05
set OUTPUT_LOAD           0.005
set MAX_TRANSITION        0.20
set CLOCK_UNCERTAINTY_RATIO 0.05
set INPUT_DELAY_RATIO       0.10
set OUTPUT_DELAY_RATIO      0.10
set COMPILE_MODE          "ultra"
set KEEP_HIERARCHY        0
set ENABLE_POWER_REPORT   0
set MAX_CORES             1

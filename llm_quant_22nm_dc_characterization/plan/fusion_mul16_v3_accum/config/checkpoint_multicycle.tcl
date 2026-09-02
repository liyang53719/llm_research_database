# FusionMul16 v3 Kblock=64 checkpoint engine.
# checkpoint_base_q/checkpoint_term_q are captured at a block boundary and kept
# stable for two cycles. checkpoint_fp32_o is enabled only on the second edge.
set ckpt_from [get_cells -hierarchical -quiet *checkpoint_base_q_reg*]
set ckpt_term [get_cells -hierarchical -quiet *checkpoint_term_q_reg*]
set ckpt_to   [get_cells -hierarchical -quiet *checkpoint_fp32_o_reg*]
set ckpt_sources [add_to_collection $ckpt_from $ckpt_term]
if {[sizeof_collection $ckpt_sources] == 0 || [sizeof_collection $ckpt_to] == 0} {
  error "FusionMul16 v3 checkpoint multicycle register pattern matched zero cells"
}
# Preserve the named checkpoint state elements through compile_ultra.  Without
# this guard DC may absorb checkpoint_term_q into the output-register D cone;
# that would leave the requested exception with stale source objects and make
# the 2-cycle checkpoint contract unverifiable in the mapped design.
set_dont_touch $ckpt_sources
set_dont_touch $ckpt_to
set_multicycle_path 2 -setup -from $ckpt_sources -to $ckpt_to
set_multicycle_path 1 -hold  -from $ckpt_sources -to $ckpt_to

update_compile_order -fileset sources_1
reset_run synth_1
launch_runs impl_1 -to_step write_bitstream
wait_on_run impl_1

if {[get_property STATUS [get_runs synth_1]] == {synth_design Complete!}} {
    puts "Design synthesized!"
} else {
    puts "ERROR! Synthesis error occurred! See synth_1/runme.log"
    exit 1
}
exit




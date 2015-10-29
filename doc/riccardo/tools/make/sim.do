#
# Call vsim to invoke simulator
#
set NumericStdNoWarnings 1
set StdArithNoWarnings 1

vsim -voptargs="+acc" -t 1ps -L unisims_ver -L unimacro_ver -L secureip -L common_lib -L fft_lib -L common_OA_lib -L common_ox -L polyfilt_lib -L jesd204_if -L common_mem -L axi4lite -L gtwizard_ultrascale_v1_3 -L xil_defaultlib -L jesd_buffer -L f2f -L tpm_test -L jesd204_v5_2 -L c2c -L axi4s -lib xil_defaultlib $1 tpm_test.glbl

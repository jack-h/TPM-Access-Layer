import re

__author__ = 'lessju'

from pyfabil import TPM

# Connect and initliase
tpm = TPM()
tpm.connect(ip = "10.0.10.2", port= 10000)

print tpm

# Start streaming
# tpm["board.regfile.c2c_stream_enable"] = 0x1

tpm.tpm_fpga.fpga_stop()
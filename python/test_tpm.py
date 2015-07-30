import re

__author__ = 'lessju'

from pyfabil import TPM

# Connect and initliase
tpm = TPM(ip = "10.0.10.2", port= 10000)

# Start streaming
tpm["board.regfile.c2c_stream_enable"] = 0x1

print tpm
tpm.tpm_fpga.fpga_stop()
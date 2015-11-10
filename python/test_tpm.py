import re

__author__ = 'lessju'

from pyfabil import TPM, Device

# Connect and initliase
tpm = TPM(ip = "10.0.10.2", port = 10000)

###### ------ Kcu Dev Board ----- ######
#kcu = tpm.load_plugin("KcuTestFirmware", device = Device.FPGA_1)
#kcu.start_streaming()
########################################

# Load tpm test firmware for both FPGAs
tpm.load_plugin("TpmTestFirmware", device = Device.FPGA_1)
tpm.load_plugin("TpmTestFirmware", device = Device.FPGA_2)

# Start streaming
# tpm["board.regfile.c2c_stream_enable"] = 0x1

# To send data
tpm.tpm_test_firmware.send_raw_data()

#print tpm

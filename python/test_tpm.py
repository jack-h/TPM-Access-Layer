import re

__author__ = 'lessju'

from pyfabil import TPM, Device

# Connect and initliase
# tpm = TPM(ip = "10.0.10.2", port= 10000)
#
# # Load plugin
# kcu = tpm.load_plugin("KcuTestFirmware", device = Device.FPGA_1)
#
# # Start streaming
# kcu.start_streaming()

tpm = TPM(ip='localhost', port=10000, simulator=True)

tpm.load_firmware(Device.Board, filepath='/home/lessju/map.xml')

print tpm
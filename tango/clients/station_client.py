import PyTango
import pickle
from pyfabil import Device

# INIT device
station = PyTango.DeviceProxy("test/station/1")

# Add TPM board to station
device = {}
device['name'] = 'test/tpm_board/1'
device['ip'] = '127.0.0.1'
device['port'] = 10000
args = pickle.dumps(device)
station.command_inout("add_tpm", args)

# Connect devices in station
tpm_name = 'test/tpm_board/1'
station.command_inout("connect_tpm", tpm_name)

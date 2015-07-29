import PyTango
import pickle
from pyfabil import BoardMake, Device

# INIT device
station = PyTango.DeviceProxy("test/station/1")

# Add TPM board to station
device = {}
device['name'] = "test/tpm_board/1"
device['ip'] = '127.0.0.1'
device['port'] = 10000
device['type'] = BoardMake.TpmBoard
args = pickle.dumps(device)
station.command_inout("add_tpm", args)

# Connect devices in station
tpm_name = 'test/tpm_board/1'
station.command_inout("connect_tpm", tpm_name)

# Add TPM board to station
device = {}
device['name'] = "test/tpm_board/2"
device['ip'] = '127.0.0.1'
device['port'] = 10000
device['type'] = BoardMake.TpmBoard
args = pickle.dumps(device)
station.command_inout("add_tpm", args)

# Connect devices in station
tpm_name = 'test/tpm_board/2'
station.command_inout("connect_tpm", tpm_name)


# Get station state
states = station.command_inout("get_station_state")

# Load firmware on station
arguments = {}
arguments['fnName'] = 'load_firmware_blocking'

input_arguments = {}
input_arguments['device'] = Device.FPGA_1.value
input_arguments['path'] = '/home/andrea/Documents/AAVS/xml/map.xml'
input_stream = [input_arguments]
#input_stream.append(input_arguments)
#input_stream.append(input_arguments)


arguments['fnInput'] = input_stream
args = pickle.dumps(arguments)
station.command_inout("run_station_command", args)

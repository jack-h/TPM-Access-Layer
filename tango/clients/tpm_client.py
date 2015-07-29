import PyTango
import pickle
from pyfabil import Device

# class BoardState(Enum):
#     """ Board State enumeration """
#     UNKNOWN = 0         # Tango
#     INIT = 1            # Tango (was Initialising)
#     ON = 2              # Tango (was Ready)
#     RUNNING = 3         # Tango (was In_use)
#     FAULT = 4           # Tango (was Faulty)
#     OFF = 5             # Tango
#     STANDBY = 6         # Tango
#     SHUTTING_DOWN = 7   # Tango Close?
#     MAINTENANCE = 8     # ???
#     LOW_POWER = 9       # ???
#     SAFE_STATE = 10     # ???
#
#
# print BoardState.INIT.value
# print BoardState(1)

# INIT device
tpm_instance = PyTango.DeviceProxy("test/tpm_board/1")
tpm_instance.ip_address = "127.0.0.1"
tpm_instance.port = 10000

# Connect to device
tpm_instance.command_inout("connect")

# Load firmware
arguments = {}
arguments['device'] = Device.FPGA_1.value
arguments['path'] = '/home/andrea/Documents/AAVS/xml/map.xml'
args = pickle.dumps(arguments)
tpm_instance.command_inout("load_firmware", args)

# Load plugin
arguments = {}
arguments['plugin_name_load'] = 'TpmAdc'
keywords = {}
#keywords = {'keyword1': 'foo', 'keyword2': 'bar'}
arguments['kw_args'] = keywords
args = pickle.dumps(arguments)

tpm_instance.command_inout("load_plugin", args)
tpm_instance.command_inout("load_plugin", args)
tpm_instance.command_inout("load_plugin", args)
tpm_instance.command_inout("load_plugin", args)

# Get device list
tpm_instance.command_inout("get_device_list")

# Run plugin command
arguments = {}
arguments['fnName'] = 'tpm_adc[0].adc_single_start'
arguments['fnInput'] = pickle.dumps({})
args = pickle.dumps(arguments)
argout = tpm_instance.command_inout("run_plugin_command", args)
argout

# Try change attribute alarms
arguments = {}
arguments['name'] = 'port'
arguments['min_value'] = '1'
arguments['max_value'] = '50000'
arguments['min_alarm'] = '10'
arguments['max_alarm'] = '30000'
args = pickle.dumps(arguments)
tpm_instance.command_inout("set_attribute_levels", args)

# Start polling port
tpm_instance.poll_attribute('port', 3000)
#tpm_instance.poll_attribute('port', 0) #to stop polling

# Print register list
print tpm_instance.command_inout("get_register_list")

# Read from register
arguments={}
arguments['device'] = Device.FPGA_1.value
arguments['register'] = 'fpga1.regfile.block2048b'
arguments['words'] = 512
arguments['offset'] = 0
args = pickle.dumps(arguments)
print tpm_instance.command_inout("read_register", args)
#print tpm_instance.read_register(args)

# Write to vector register
arguments = {}
arguments['device'] = Device.FPGA_1.value
arguments['register'] = 'fpga1.regfile.block2048b'
arguments['values'] = [100,1,2,3]
arguments['offset'] = 512-4
args = pickle.dumps(arguments)
print tpm_instance.command_inout("write_register", args)
#tpm_instance.write_register(args)

# Read from register
arguments={}
arguments['device'] = Device.FPGA_1.value
arguments['register'] = 'fpga1.regfile.block2048b'
arguments['words'] = 4
arguments['offset'] = 512-4
args = pickle.dumps(arguments)
print tpm_instance.command_inout("read_register", args)
#print tpm_instance.read_register(args)
print '============================================'
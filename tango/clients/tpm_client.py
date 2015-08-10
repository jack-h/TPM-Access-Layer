import PyTango
import pickle
from pyfabil import Device, BoardState


# INIT device
tpm_instance = PyTango.DeviceProxy("test/tpm_board/1")
#tpm_instance.ip_address = "192.168.56.1"
tpm_instance.ip_address = "127.0.0.1"
tpm_instance.port = 10000
print tpm_instance
print tpm_instance.is_connected

# Connect to device
tpm_instance.command_inout("connect")
print tpm_instance.is_connected

# INIT device
tpm_instance = PyTango.DeviceProxy("test/tpm_board/2")
#tpm_instance.ip_address = "192.168.56.1"
tpm_instance.ip_address = "127.0.0.1"
tpm_instance.port = 10000

# Connect to device
tpm_instance.command_inout("connect")

# Load Firmware
arguments = {}
arguments['device'] = Device.Board.value
#arguments['path'] = None
arguments['path'] = '/home/andrea/Documents/AAVS/xml/map_old.xml'
arguments['load_values'] = False
args = pickle.dumps(arguments)
print "Load firmware: " + str(tpm_instance.command_inout("load_firmware", args))

# Load attributes based on firmware
print "Generate attributes in Tango: " + str(tpm_instance.command_inout("generate_attributes"))

# Flush attributes
print "Flush attributes in Tango: " + str(tpm_instance.command_inout("flush_attributes"))

# And re-load them again
print "Regenerate attributes in Tango: " + str(tpm_instance.command_inout("generate_attributes"))

# Get device list
print "Get device list: " + str(pickle.loads(tpm_instance.command_inout("get_device_list")))

# # Get firmware list (1)
# arguments = {}
# arguments['device'] = Device.FPGA_1.value
# args = pickle.dumps(arguments)
# print "Get firmware list: " + str(pickle.loads(tpm_instance.command_inout("get_firmware_list", args)))
#
# # Get firmware list (2)
# arguments = {}
# arguments['device'] = None
# args = pickle.dumps(arguments)
# print "Get firmware list None device: " + str(pickle.loads(tpm_instance.command_inout("get_firmware_list", args)))

# Get register info (1)
print "Get register info: " + str(pickle.loads(tpm_instance.command_inout("get_register_info", 'board.regfile.c2c_stream_enable')))
#print pickle.loads(tpm_instance.command_inout("get_register_info", 'board.address'))

# Get register info (2)
print "Get register info, wrong register: " + str(pickle.loads(tpm_instance.command_inout("get_register_info", 'blasens')))

# Get register list
arguments = {}
arguments['reset'] = False
arguments['load_values'] = False
args = pickle.dumps(arguments)
print "Get register list: " + str(tpm_instance.command_inout("get_register_list", args))

# Read Address (1)
arguments = {}
arguments['address'] = '0x00000000'
arguments['words'] = 2
args = pickle.dumps(arguments)
print "Read address vector: " + str(tpm_instance.command_inout("read_address", args))

# Read Address (2)
arguments = {}
arguments['address'] = '0x00000000'
arguments['words'] = 1
args = pickle.dumps(arguments)
print "Read address scalar: " + str(tpm_instance.command_inout("read_address", args))

# Read Address (3)
arguments = {}
arguments['address'] = '0x00--'
arguments['words'] = 1
args = pickle.dumps(arguments)
print "Read address wrong address: " + str(tpm_instance.command_inout("read_address", args))

# Read Device (1)
arguments = {}
arguments['device'] = 'pll'
arguments['address'] = '0x00000000'
args = pickle.dumps(arguments)
print "Read device: " + str(tpm_instance.command_inout("read_device", args))

# Read Device (2)
arguments = {}
arguments['device'] = 'pll--'
arguments['address'] = '0x00000000'
args = pickle.dumps(arguments)
print "Read device wrong device: " + str(tpm_instance.command_inout("read_device", args))

# Read Register (1)
arguments = {}
arguments['device'] = Device.FPGA_1.value
arguments['register'] = 'board.regfile.c2c_stream_enable'
#arguments['register'] = 'board.sclk'
arguments['words'] = 1
arguments['offset'] = 0
args = pickle.dumps(arguments)
print "Read register scalar: " + str(tpm_instance.command_inout("read_register", args))

# Read Register (2)
arguments = {}
arguments['device'] = Device.FPGA_1.value
arguments['register'] = 'board.regfile.c2c_stream_enable'
#arguments['register'] = 'board.sclk'
arguments['words'] = 2
arguments['offset'] = 0
args = pickle.dumps(arguments)
print "Read register vector no offset: " + str(tpm_instance.command_inout("read_register", args))

# Read Register (3)
arguments = {}
arguments['device'] = Device.FPGA_1.value
arguments['register'] = 'blasens'
arguments['words'] = 2
arguments['offset'] = 0
args = pickle.dumps(arguments)
print "Read register wrong register: " + str(tpm_instance.command_inout("read_register", args))

# Read Register (4) VECTOR
arguments = {}
arguments['device'] = Device.FPGA_1.value
#arguments['device'] = Device.Board.value
arguments['register'] = 'fpga1.regfile.block2048b'
arguments['words'] = 4
arguments['offset'] = 512-4
args = pickle.dumps(arguments)
print "Read register vector offset: " + str(tpm_instance.command_inout("read_register", args))

# Set Attribute levels (1)
arguments = {}
arguments['name'] = 'port'
arguments['min_value'] = '1'
arguments['max_value'] = '50000'
arguments['min_alarm'] = '1000'
arguments['max_alarm'] = '6000'
args = pickle.dumps(arguments)
print "Set attribute levels: " + str(tpm_instance.command_inout("set_attribute_levels", args))

# Set Attribute levels (2)
arguments = {}
arguments['name'] = 'port'
arguments['min_value'] = 1
arguments['max_value'] = 50000
arguments['min_alarm'] = 1000
arguments['max_alarm'] = 6000
args = pickle.dumps(arguments)
print "Set attribute levels (wrong): " + str(tpm_instance.command_inout("set_attribute_levels", args))

# Set Board State
state = BoardState.On.value
print "Set board state: " + str(tpm_instance.command_inout("set_board_state", state))

# Write Address (1)
arguments = {}
arguments['address'] = '0x00000000'
arguments['values'] = [0]
args = pickle.dumps(arguments)
print "Write address: " + str(tpm_instance.command_inout("write_address", args))

# Write Address (2)
arguments = {}
arguments['address'] = '0x0000000-'
arguments['values'] = [0]
args = pickle.dumps(arguments)
print "Write address wrong address: " + str(tpm_instance.command_inout("write_address", args))

# Write device (1)
arguments = {}
arguments['device'] = 'pll'
arguments['address'] = '0x00000000'
arguments['value'] = 0
args = pickle.dumps(arguments)
print "Write device: " + str(tpm_instance.command_inout("write_device", args))
#
# Write device (2)
arguments = {}
arguments['device'] = 'pll'
arguments['address'] = '0x0000000-'
arguments['value'] = 0
args = pickle.dumps(arguments)
print "Write device wrong address: " + str(tpm_instance.command_inout("write_device", args))

# Write register (1)
arguments = {}
arguments['device'] = Device.FPGA_1.value
arguments['register'] = 'board.regfile.c2c_stream_enable'
arguments['values'] = [1]
arguments['offset'] = 0
args = pickle.dumps(arguments)
print "Write register scalar: " + str(tpm_instance.command_inout("write_register", args))

# Write register (2)
arguments = {}
arguments['device'] = None
arguments['register'] = 'board.regfile.c2c_stream_enable'
arguments['values'] = [1]
arguments['offset'] = 0
args = pickle.dumps(arguments)
print "Write None device register: " + str(tpm_instance.command_inout("write_register", args))

# Write register (3)
arguments = {}
arguments['device'] = Device.FPGA_1.value
arguments['register'] = 'blasens'
arguments['values'] = [1]
arguments['offset'] = 0
args = pickle.dumps(arguments)
print "Write nonexistent register scalar: " + str(tpm_instance.command_inout("write_register", args))

# Write to register (4) VECTOR
arguments = {}
arguments['device'] = Device.FPGA_1.value
arguments['register'] = 'fpga1.regfile.block2048b'
arguments['values'] = [100,1,2,3]
arguments['offset'] = 512-4
args = pickle.dumps(arguments)
print "Write register vector: " + str(tpm_instance.command_inout("write_register", args))

# Sink Alarm States
print "Sink alarm states: " + str(tpm_instance.command_inout("sink_alarm_state"))

# Reset Board (1)
arguments = {}
arguments['device'] = Device.FPGA_1.value
args = pickle.dumps(arguments)
print "Reset board: " + str(tpm_instance.command_inout("reset_board", args))

# Reset Board (2)
arguments = {}
arguments['device'] = None
args = pickle.dumps(arguments)
print "Reset board with None device: " + str(tpm_instance.command_inout("reset_board", args))

# Start/stop polling (1)
print "Start polling: " + str(tpm_instance.poll_attribute('port', 3000))
print "Stop polling: " + str(tpm_instance.poll_attribute('port', 0))

# Load Plugin
arguments = {}
arguments['plugin_name_load'] = 'tpm_adc'
keywords = {}
keywords = {'adc_id': 'adc1'}
arguments['kw_args'] = keywords
args = pickle.dumps(arguments)
print "Load plugin: " + str(tpm_instance.command_inout("load_plugin", args))

# Load More Plugin Instances
# tpm_instance.command_inout("load_plugin", args)
# tpm_instance.command_inout("load_plugin", args)
# tpm_instance.command_inout("load_plugin", args)
# tpm_instance.command_inout("load_plugin", args)


# Run plugin command
arguments = {}
arguments['fnName'] = 'tpm_adc[0].adc_single_start'
arguments['fnInput'] = pickle.dumps({})
args = pickle.dumps(arguments)
print "Run plugin command: " + str(tpm_instance.command_inout("run_plugin_command", args))

# # Remove Command
print "Remove command: " + str(tpm_instance.command_inout("remove_command", 'tpm_adc[0].adc_single_start'))

# Run plugin command (after deletion)
arguments = {}
arguments['fnName'] = 'tpm_adc[0].adc_single_start'
arguments['fnInput'] = pickle.dumps({})
args = pickle.dumps(arguments)
print "Run plugin command after deletion: " + str(tpm_instance.command_inout("run_plugin_command", args))

# Unload Plugin
arguments = {}
arguments['plugin'] = 'tpm_adc'
arguments['instance'] = 0
args = pickle.dumps(arguments)
print "Unload plugin: " + str(tpm_instance.command_inout("unload_plugin", args))

# Unload all plugins
print "Unload all plugins: " + str(tpm_instance.command_inout("unload_all_plugins"))




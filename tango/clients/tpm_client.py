import PyTango
import pickle
from pyfabil import Device, BoardMake


# INIT device
tpm_instance = PyTango.DeviceProxy("test/tpm_board/1")
#tpm_instance.ip_address = "192.168.56.1"
tpm_instance.ip_address = "127.0.0.1"
tpm_instance.port = 10000

# Connect to device
tpm_instance.command_inout("connect")

# Load Firmware
arguments = {}
arguments['device'] = Device.FPGA_1.value
#arguments['path'] = None
#arguments['path'] = '/home/andrea/Documents/AAVS/xml/map.xml'
arguments['path'] = '/home/andrea/Documents/AAVS/xml/cpld.xml'
arguments['load_values'] = False
args = pickle.dumps(arguments)
tpm_instance.command_inout("load_firmware", args)

# # Load attributes based on firmware
# tpm_instance.command_inout("generate_attributes")
#
# # Flush attributes
# tpm_instance.command_inout("flush_attributes")
#
# # And re-load them again
# tpm_instance.command_inout("generate_attributes")
#
# # Get device list
# print pickle.loads(tpm_instance.command_inout("get_device_list"))
#
# # Get firmware list (1)
# arguments = {}
# arguments['device'] = 1
# args = pickle.dumps(arguments)
# print pickle.loads(tpm_instance.command_inout("get_firmware_list", args))
#
# # Get firmware list (2)
# arguments = {}
# arguments['device'] = None
# args = pickle.dumps(arguments)
# print pickle.loads(tpm_instance.command_inout("get_firmware_list", args))
#
# # Get register info (1)
# print pickle.loads(tpm_instance.command_inout("get_register_info", 'board.regfile.c2c_stream_enable'))
#
# # Get register info (2)
# print pickle.loads(tpm_instance.command_inout("get_register_info", 'blasens'))
#
# # Get register list
# arguments = {}
# arguments['reset'] = False
# arguments['load_values'] = False
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("get_register_list", args)
#
# # Read Address (1)
# arguments = {}
# arguments['address'] = '0x00000000'
# arguments['words'] = 2
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("read_address", args)
#
# # Read Address (2)
# arguments = {}
# arguments['address'] = '0x00000000'
# arguments['words'] = 1
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("read_address", args)
#
# # Read Address (3)
# arguments = {}
# arguments['address'] = '0x00--'
# arguments['words'] = 1
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("read_address", args)
#
# # Read Device (1)
# arguments = {}
# arguments['device'] = 'pll'
# arguments['address'] = '0x00000000'
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("read_device", args)
#
# # Read Device (2)
# arguments = {}
# arguments['device'] = 'pll--'
# arguments['address'] = '0x00000000'
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("read_device", args)
#
# # Read Register (1)
# arguments = {}
# arguments['device'] = Device.Board.value
# arguments['register'] = 'board.regfile.c2c_stream_enable'
# arguments['words'] = 1
# arguments['offset'] = 0
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("read_register", args)
#
# # Read Register (2)
# arguments = {}
# arguments['device'] = Device.Board.value
# arguments['register'] = 'board.regfile.c2c_stream_enable'
# arguments['words'] = 2
# arguments['offset'] = 0
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("read_register", args)
#
# # Read Register (3)
# arguments = {}
# arguments['device'] = Device.Board.value
# arguments['register'] = 'blasens'
# arguments['words'] = 2
# arguments['offset'] = 0
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("read_register", args)
#
# # Read Register (4) VECTOR
# arguments = {}
# arguments['device'] = Device.FPGA_1.value
# arguments['register'] = 'fpga1.regfile.block2048b'
# arguments['words'] = 4
# arguments['offset'] = 512-4
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("read_register", args)
#
# # Set Attribute levels (1)
# arguments = {}
# arguments['name'] = 'port'
# arguments['min_value'] = '1'
# arguments['max_value'] = '50000'
# arguments['min_alarm'] = '1000'
# arguments['max_alarm'] = '6000'
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("set_attribute_levels", args)
#
# # Set Attribute levels (2)
# arguments = {}
# arguments['name'] = 'port'
# arguments['min_value'] = 1
# arguments['max_value'] = 50000
# arguments['min_alarm'] = 1000
# arguments['max_alarm'] = 6000
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("set_attribute_levels", args)
#
# # Set Board State
# state = BoardState.On.value
# print tpm_instance.command_inout("set_board_state", state)
#
#
# # Write Address (1)
# arguments = {}
# arguments['address'] = '0x00000000'
# arguments['values'] = [0]
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("write_address", args)
#
# # Write Address (2)
# arguments = {}
# arguments['address'] = '0x0000000-'
# arguments['values'] = [0]
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("write_address", args)
#
# # Write device (1)
# arguments = {}
# arguments['device'] = 'pll'
# arguments['address'] = '0x00000000'
# arguments['value'] = 0
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("write_device", args)
#
# # Write device (2)
# arguments = {}
# arguments['device'] = 'pll'
# arguments['address'] = '0x0000000-'
# arguments['value'] = 0
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("write_device", args)
#
# # Write register (1)
# arguments = {}
# arguments['device'] = Device.Board.value
# #arguments['device'] = None
# arguments['register'] = 'board.regfile.c2c_stream_enable'
# arguments['values'] = [1]
# arguments['offset'] = 0
# print arguments
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("write_register", args)
#
# # Write register (2)
# arguments = {}
# arguments['device'] = None
# arguments['register'] = 'board.regfile.c2c_stream_enable'
# arguments['values'] = [1]
# arguments['offset'] = 0
# print arguments
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("write_register", args)
#
# # Write register (3)
# arguments = {}
# arguments['device'] = Device.Board.value
# arguments['register'] = 'blasens'
# arguments['values'] = [1]
# arguments['offset'] = 0
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("write_register", args)
#
# # Write to register (4) VECTOR
# arguments = {}
# arguments['device'] = Device.FPGA_1.value
# arguments['register'] = 'fpga1.regfile.block2048b'
# arguments['values'] = [100,1,2,3]
# arguments['offset'] = 512-4
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("write_register", args)
#
# # Sink Alarm States
# tpm_instance.command_inout("sink_alarm_state")
#
# # Reset Board (1)
# arguments = {}
# arguments['device'] = Device.Board.value
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("reset_board", args)
#
# # Reset Board (2)
# arguments = {}
# arguments['device'] = None
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("reset_board", args)
#
# # Start/stop polling (1)
# tpm_instance.poll_attribute('port', 3000)
# tpm_instance.poll_attribute('port', 0) #to stop polling
#
# # Load Firmware
# arguments = {}
# arguments['device'] = Device.FPGA_1.value
# arguments['path'] = None
# arguments['load_values'] = False
# #arguments['path'] = '/home/andrea/Documents/AAVS/xml/map.xml'
# args = pickle.dumps(arguments)
# tpm_instance.command_inout("load_firmware", args)

# # Load Plugin
# arguments = {}
# arguments['plugin_name_load'] = 'TpmAdc'
# keywords = {}
# keywords = {'adc_id': 'adc1'}
# arguments['kw_args'] = keywords
# args = pickle.dumps(arguments)
# print tpm_instance.command_inout("load_plugin", args)

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
print tpm_instance.command_inout("run_plugin_command", args)

# # Remove Command
print tpm_instance.command_inout("remove_command", 'tpm_adc[0].adc_single_start')

# Run plugin command (after deletion)
arguments = {}
arguments['fnName'] = 'tpm_adc[0].adc_single_start'
arguments['fnInput'] = pickle.dumps({})
args = pickle.dumps(arguments)
print tpm_instance.command_inout("run_plugin_command", args)

# Unload Plugin
arguments = {}
arguments['plugin'] = 'tpm_adc'
arguments['instance'] = 1
args = pickle.dumps(arguments)
print tpm_instance.command_inout("unload_plugin", args)

# Unload all plugins
print tpm_instance.command_inout("unload_all_plugins")




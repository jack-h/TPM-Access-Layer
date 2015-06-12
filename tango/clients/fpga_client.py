import PyTango
import pickle

# INIT FPGA device
fpga_instance = PyTango.DeviceProxy("test/fpga_board/1")
fpga_instance.ip_address = "127.0.0.1"
fpga_instance.port = 10000

# Connect to device
fpga_instance.command_inout("connect")

# Load firmware
arguments = {}
arguments['device'] = 2
arguments['path'] = '/home/andrea/Documents/AAVS/xml/map.xml'
args = pickle.dumps(arguments)
fpga_instance.command_inout("load_firmware_blocking", args)

# Load plugin
fpga_instance.command_inout("load_plugin", 'FirmwareTest')

# Get device list
fpga_instance.command_inout("get_device_list")

# Run plugin command
arguments = {}
arguments['fnName'] = 'firmware_test.read_date_code'
arguments['fnInput'] = pickle.dumps({})
args = pickle.dumps(arguments)
fpga_instance.command_inout("run_plugin_command", args)

# Try change attribute alarms
arguments = {}
arguments['name'] = 'port'
arguments['min_value'] = '1'
arguments['max_value'] = '50000'
arguments['min_alarm'] = '10'
arguments['max_alarm'] = '30000'
args = pickle.dumps(arguments)
fpga_instance.command_inout("set_attribute_levels", args)

# Start polling port
fpga_instance.poll_attribute('port', 3000)
#tpm_instance.poll_attribute('port', 0) #to stop polling

# Read from register
arguments={}
arguments['device'] = 2
arguments['register'] = 'fpga1.regfile.block2048b'
arguments['words'] = 512
arguments['offset'] = 0
args = pickle.dumps(arguments)
print fpga_instance.read_register(args)

# Write to vector register
arguments = {}
arguments['device'] = 2
arguments['register'] = 'fpga1.regfile.block2048b'
arguments['values'] = [100,1,2,3]
arguments['offset'] = 512-4
args = pickle.dumps(arguments)
fpga_instance.write_register(args)

# Read from register
arguments={}
arguments['device'] = 2
arguments['register'] = 'fpga1.regfile.block2048b'
arguments['words'] = 4
arguments['offset'] = 512-4
args = pickle.dumps(arguments)
print fpga_instance.read_register(args)
print '============================================'

# tpm_instance.command_inout("getDeviceList")
# tpm_instance.command_inout("getRegisterList")
# args = 'fpga1.regfile.jesd_ctrl.ext_trig_en'
# tpm_instance.command_inout("getRegisterInfo", args)
# print '============================================'


# arguments = {}
# arguments['device'] = 2
# args = str(arguments)
# tpm_instance.command_inout("getFirmwareList", args)
# tpm_instance.command_inout("flushAttributes")
# #tpm_instance.command_inout("Disconnect")




# # INIT device
# tpm_instance = PyTango.DeviceProxy("test/tpm_board/2")
# tpm_instance.ip_address = "127.0.0.1"
# tpm_instance.port = 10000
#
# # Connect to device
# tpm_instance.command_inout("connect")
#
# # Load firmware
# arguments = {}
# arguments['device'] = 2
# arguments['path'] = '/home/andrea/Documents/AAVS/xml/map.xml'
# args = pickle.dumps(arguments)
# tpm_instance.command_inout("load_firmware_blocking", args)
#
# # Load plugin
# tpm_instance.command_inout("load_plugin", 'FirmwareTest')
#
# # Get device list
# tpm_instance.command_inout("get_device_list")
#
# # Run plugin command
# arguments = {}
# arguments['fnName'] = 'firmware_test.read_date_code'
# arguments['fnInput'] = pickle.dumps({})
# args = pickle.dumps(arguments)
# tpm_instance.command_inout("run_plugin_command", args)
#
# # Try change attribute alarms
# arguments = {}
# arguments['name'] = 'port'
# arguments['min_value'] = '1'
# arguments['max_value'] = '50000'
# arguments['min_alarm'] = '10'
# arguments['max_alarm'] = '30000'
# args = pickle.dumps(arguments)
# tpm_instance.command_inout("set_attribute_levels", args)
#
# # Start polling port
# tpm_instance.poll_attribute('port', 3000)
# #tpm_instance.poll_attribute('port', 0) #to stop polling
#
# # Read from register
# arguments={}
# arguments['device'] = 2
# arguments['register'] = 'fpga1.regfile.block2048b'
# arguments['words'] = 512
# arguments['offset'] = 0
# args = pickle.dumps(arguments)
# print tpm_instance.read_register(args)
#
# # Write to vector register
# arguments = {}
# arguments['device'] = 2
# arguments['register'] = 'fpga1.regfile.block2048b'
# arguments['values'] = [100,1,2,3]
# arguments['offset'] = 512-4
# args = pickle.dumps(arguments)
# tpm_instance.write_register(args)
#
# # Read from register
# arguments={}
# arguments['device'] = 2
# arguments['register'] = 'fpga1.regfile.block2048b'
# arguments['words'] = 4
# arguments['offset'] = 512-4
# args = pickle.dumps(arguments)
# print tpm_instance.read_register(args)
# print '============================================'
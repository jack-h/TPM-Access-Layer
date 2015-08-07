import PyTango
import pickle
from pyfabil import Device, BoardState


# INIT device
roach = PyTango.DeviceProxy("test/roach_board/1")
roach.ip_address = "192.168.100.2"
roach.port = 7147

# Connect to device
roach.command_inout("connect")

# Load firmware
roach.set_timeout_millis(20000)
arguments = {}
arguments['device'] = Device.FPGA_1.value
arguments['path'] = 'tut4.bof'
arguments['load_values'] = False
args = pickle.dumps(arguments)
print "Load firmware: " + str(roach.command_inout("load_firmware", args))
roach.set_timeout_millis(3000)

# Load attributes based on firmware
print "Generate attributes in Tango: " + str(roach.command_inout("generate_attributes"))

# Flush attributes
print "Flush attributes in Tango: " + str(roach.command_inout("flush_attributes"))

# And re-load them again
print "Regenerate attributes in Tango: " + str(roach.command_inout("generate_attributes"))

# Get device list
print "Get device list: " + str(pickle.loads(roach.command_inout("get_device_list")))

# Get register list
arguments = {}
arguments['reset'] = False
arguments['load_values'] = False
args = pickle.dumps(arguments)
print "Get register list: " + str(roach.command_inout("get_register_list", args))

# Get register info (1)
print "Get register info: " + str(pickle.loads(roach.command_inout("get_register_info", 'acc_len')))

# Get register info (2)
print "Get register info: " + str(pickle.loads(roach.command_inout("get_register_info", 'acc_lennnnn')))

# Get firmware list (1)
arguments = {}
arguments['device'] = Device.FPGA_1.value
args = pickle.dumps(arguments)
print "Get firmware list: " + str(pickle.loads(roach.command_inout("get_firmware_list", args)))

# Read Register (1)
arguments = {}
arguments['device'] = Device.FPGA_1.value
arguments['register'] = 'acc_len'
arguments['words'] = 1
arguments['offset'] = 0
args = pickle.dumps(arguments)
print "Read register scalar: " + str(roach.command_inout("read_register", args))

# Read Register (2)
arguments = {}
arguments['device'] = Device.FPGA_1.value
arguments['register'] = 'acc_len'
arguments['words'] = 2
arguments['offset'] = 0
args = pickle.dumps(arguments)
print "Read register scalar: " + str(roach.command_inout("read_register", args))

# Set Attribute levels (1)
arguments = {}
arguments['name'] = 'port'
arguments['min_value'] = '1'
arguments['max_value'] = '50000'
arguments['min_alarm'] = '1000'
arguments['max_alarm'] = '6000'
args = pickle.dumps(arguments)
print "Set attribute levels: " + str(roach.command_inout("set_attribute_levels", args))

# Set Board State
state = BoardState.On.value
print "Set board state: " + str(roach.command_inout("set_board_state", state))

# Write Address (1)
arguments = {}
arguments['address'] = '0x00000000'
arguments['values'] = [0]
args = pickle.dumps(arguments)
print "Write address: " + str(roach.command_inout("write_address", args))

# Write device (1)
arguments = {}
arguments['device'] = 'pll'
arguments['address'] = '0x00000000'
arguments['value'] = 0
args = pickle.dumps(arguments)
print "Write device: " + str(roach.command_inout("write_device", args))

# Write register (1)
arguments = {}
arguments['device'] = Device.FPGA_1.value
arguments['register'] = 'acc_len'
arguments['values'] = [1]
arguments['offset'] = 0
args = pickle.dumps(arguments)
print "Write register scalar: " + str(roach.command_inout("write_register", args))

# Read Register (1)
arguments = {}
arguments['device'] = Device.FPGA_1.value
arguments['register'] = 'acc_len'
arguments['words'] = 1
arguments['offset'] = 0
args = pickle.dumps(arguments)
print "Read register scalar: " + str(roach.command_inout("read_register", args))

# Sink Alarm States
print "Sink alarm states: " + str(roach.command_inout("sink_alarm_state"))

# Reset Board (1)
arguments = {}
arguments['device'] = Device.FPGA_1.value
args = pickle.dumps(arguments)
print "Reset board: " + str(roach.command_inout("reset_board", args))

# Start/stop polling (1)
print "Start polling: " + str(roach.poll_attribute('port', 3000))
print "Stop polling: " + str(roach.poll_attribute('port', 0))








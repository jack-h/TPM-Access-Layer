import PyTango
import pickle

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
arguments['device'] = 2
arguments['path'] = '/home/andrea/Documents/AAVS/xml/map.xml'
args = pickle.dumps(arguments)
tpm_instance.command_inout("load_firmware_blocking", args)

# Load plugin
tpm_instance.command_inout("load_plugin", 'FirmwareTest')

# Run plugin command
arguments = {}
arguments['fnName'] = 'read_date_code'
arguments['fnInput'] = pickle.dumps({})
args = pickle.dumps(arguments)
tpm_instance.command_inout("run_plugin_command", args)

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
tpm_instance.poll_attribute('port', 2000)
tpm_instance.poll_attribute('port', 0) #to stop polling

# Read from register
arguments={}
arguments['device'] = 2
arguments['register'] = 'fpga1.regfile.block2048b'
arguments['words'] = 512
arguments['offset'] = 0
args = pickle.dumps(arguments)
print tpm_instance.read_register(args)

# Write to vector register
arguments = {}
arguments['device'] = 2
arguments['register'] = 'fpga1.regfile.block2048b'
arguments['values'] = [100,1,2,3]
arguments['offset'] = 512-4
args = pickle.dumps(arguments)
tpm_instance.write_register(args)

# Read from register
arguments={}
arguments['device'] = 2
arguments['register'] = 'fpga1.regfile.block2048b'
arguments['words'] = 4
arguments['offset'] = 512-4
args = pickle.dumps(arguments)
print tpm_instance.read_register(args)
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
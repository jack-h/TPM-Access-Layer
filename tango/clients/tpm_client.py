import PyTango
from mercurial.store import fncache
import pickle
from enum import Enum

class BoardState(Enum):
    """ Board State enumeration """
    UNKNOWN = 0         # Tango
    INIT = 1            # Tango (was Initialising)
    ON = 2              # Tango (was Ready)
    RUNNING = 3         # Tango (was In_use)
    FAULT = 4           # Tango (was Faulty)
    OFF = 5             # Tango
    STANDBY = 6         # Tango
    SHUTTING_DOWN = 7   # Tango Close?
    MAINTENANCE = 8     # ???
    LOW_POWER = 9       # ???
    SAFE_STATE = 10     # ???


print BoardState.INIT.value
print BoardState(1)

tpm_instance = PyTango.DeviceProxy("test/tpm_board/1")

arguments = {}
arguments['device'] = 2
arguments['path'] = '/home/andrea/Documents/AAVS/xml/map.xml'
args = pickle.dumps(arguments)
#args = str(arguments)

tpm_instance.command_inout("loadfirmwareblocking", args)
tpm_instance.command_inout("getDeviceList")
tpm_instance.command_inout("getRegisterList")
args = 'fpga1.regfile.jesd_ctrl.ext_trig_en'
tpm_instance.command_inout("getRegisterInfo", args)
print '============================================'

arguments = {}
arguments['device'] = 2
args = str(arguments)
tpm_instance.command_inout("getFirmwareList", args)
tpm_instance.command_inout("flushAttributes")
#tpm_instance.command_inout("Disconnect")
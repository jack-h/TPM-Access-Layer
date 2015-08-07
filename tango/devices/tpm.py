import PyTango
from pyfabil import Device
import pickle
import sys

class Tpm(object):

    # Class constructor
    def __init__(self, device_name = None, ip_address = "127.0.0.1", port = 1000):
        if device_name is not None:
            self._board_instance = PyTango.DeviceProxy(device_name)
            self._board_instance.ip_address = ip_address
            self._board_instance.port = port

    def connect(self):
        try:
            self._board_instance.command_inout("connect")
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def disconnect(self):
        try:
            self._board_instance.command_inout("disconnect")
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def reset(self, device):
        try:
            arguments = {}
            arguments['device'] = device.value
            args = pickle.dumps(arguments)
            self._board_instance.command_inout("reset_board", args)
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def sink_alarm_state(self):
        try:
            self._board_instance.command_inout("sink_alarm_state")
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def get_device_list(self):
        try:
            return self._board_instance.command_inout("get_device_list")
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def get_firmware_list(self, device = Device.Board):
        try:
            arguments = {}
            arguments['device'] = device.value
            args = pickle.dumps(arguments)
            return self._board_instance.command_inout("get_firmware_list", args)
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def get_register_info(self, reset = False, load_values = False):
        try:
            arguments = {}
            arguments['reset'] = reset
            arguments['load_values'] = load_values
            args = pickle.dumps(arguments)
            return self._board_instance.command_inout("get_register_info", args)
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def get_register_list(self, reset = False, load_values = False):
        try:
            arguments = {}
            arguments['reset'] = reset
            arguments['load_values'] = load_values
            args = pickle.dumps(arguments)
            return self._board_instance.command_inout("get_register_list", args)
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def load_firmware(self, device, filepath = None, load_values = False):
        try:
            arguments = {}
            arguments['device'] = device.value
            arguments['path'] = filepath
            arguments['load_values'] = load_values
            args = pickle.dumps(arguments)
            return self._board_instance.command_inout("load_firmware", args)
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def load_plugin(self, plugin, **kwargs):
        try:
            arguments = {}
            arguments['plugin_name_load'] = plugin
            arguments['kw_args'] = kwargs
            args = pickle.dumps(arguments)
            return self._board_instance.command_inout("load_plugin", args)
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def unload_all_plugins(self):
        try:
            return self._board_instance.command_inout("unload_all_plugins")
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def unload_plugin(self, plugin, instance = None):
        try:
            arguments = {}
            arguments['plugin'] = plugin
            arguments['instance'] = instance
            args = pickle.dumps(arguments)
            return self._board_instance.command_inout("unload_plugin", args)
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def run_plugin_command(self, name, input):
        try:
            arguments = {}
            arguments['fnName'] = name
            arguments['fnInput'] = input
            args = pickle.dumps(arguments)
            return self._board_instance.command_inout("run_plugin_command", args)
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def read_address(self, address, n=1):
        try:
            arguments = {}
            arguments['address'] = address
            arguments['words'] = n
            args = pickle.dumps(arguments)
            return self._board_instance.command_inout("read_address", args)
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def write_address(self, address, values):
        try:
            arguments = {}
            arguments['address'] = address
            arguments['values'] = values
            args = pickle.dumps(arguments)
            return self._board_instance.command_inout("write_address", args)
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def read_device(self, address, device):
        try:
            arguments = {}
            arguments['address'] = address
            arguments['device'] = device.value
            args = pickle.dumps(arguments)
            return self._board_instance.command_inout("read_device", args)
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def write_device(self, device, address, values):
        try:
            arguments = {}
            arguments['address'] = address
            arguments['device'] = device.value
            arguments['value'] = values
            args = pickle.dumps(arguments)
            return self._board_instance.command_inout("write_device", args)
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def read_register(self, register, n = 1, offset = 0, device = None):
        try:
            arguments = {}
            arguments['register'] = register
            arguments['device'] = device.value
            arguments['words'] = n
            arguments['offset'] = offset
            args = pickle.dumps(arguments)
            return self._board_instance.command_inout("read_register", args)
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def write_register(self, register, values, offset = 0, device = None):
        try:
            arguments = {}
            arguments['register'] = register
            arguments['device'] = device.value
            arguments['values'] = values
            arguments['offset'] = offset
            args = pickle.dumps(arguments)
            return self._board_instance.command_inout("write_register", args)
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def set_attribute_levels(self, name, min_value, max_value, min_alarm, max_alarm):
        try:
            arguments = {}
            arguments['name'] = name
            arguments['min_value'] = min_value
            arguments['max_value'] = max_value
            arguments['min_alarm'] = min_alarm
            arguments['max_alarm'] = max_alarm
            args = pickle.dumps(arguments)
            return self._board_instance.command_inout("set_attribute_levels", args)
        except:
            print "Error:", sys.exc_info()[0]
            raise

if __name__ == "__main__":
    tpm = Tpm(device_name = "test/tpm_board/1", ip_address="127.0.0.1", port=10000)
    print tpm.connect()
    print tpm.load_firmware(Device.Board, '/home/andrea/Documents/AAVS/xml/map_old.xml')

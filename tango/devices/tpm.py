import PyTango
from pyfabil import Device
import fpga
import pickle
import sys


class Tpm(fpga.Fpga):

    # Class constructor
    def __init__(self, device_name = None, ip_address = "127.0.0.1", port = 1000):
        if device_name is not None:
            super(Tpm, self).__init__(device_name, ip_address, port)

    def connect(self):
        try:
            self._board_instance.command_inout("connect")
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

if __name__ == "__main__":
    pass
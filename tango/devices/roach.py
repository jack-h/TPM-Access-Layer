import PyTango
from pyfabil import Device
import fpga
import pickle
import sys


class Roach(fpga.Fpga):

    # Class constructor
    def __init__(self, device_name = None, ip_address = "127.0.0.1", port = 1000):
        if device_name is not None:
            super(Roach, self).__init__(device_name, ip_address, port)

    def connect(self):
        try:
            self._board_instance.command_inout("connect")
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

    def get_firmware_list(self, device = Device.FPGA_1):
        return super(Roach, self).get_firmware_list(device)

    def read_register(self, register, n = 1, offset = 0, device = Device.FPGA_1):
        return super(Roach, self).read_register(register, n, offset, device = Device.FPGA_1)

    def write_register(self, register, values, offset = 0, device = Device.FPGA_1):
        return super(Roach, self).write_register(register, values, offset, device = Device.FPGA_1)

    def load_firmware(self, boffile = None, load_values = False):
        """ Roach helper for loadFirmwareBlocking """
        return super(Roach, self).load_firmware(Device.FPGA_1, filepath = boffile, load_values = False)

    def read_address(self, address, n=1, device = None):
        return super(Roach, self).read_address(address, n)

    def write_address(self, address, values, device = None):
        return super(Roach, self).write_address(address, values)

    def read_device(self, device, address):
        return super(Roach, self).read_device(address = address, device = device)

    def write_device(self, device, address, value):
        return super(Roach, self).write_device(address = address, values = value)

if __name__ == '__main__':
    roach = Roach(ip="192.168.100.2", port=7147)
    roach.load_firmware('tut4.bof')
    print roach
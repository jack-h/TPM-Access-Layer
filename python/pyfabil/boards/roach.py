from pyfabil.base.definitions import *
from pyfabil.boards.fpgaboard import FPGABoard

class Roach(FPGABoard):
    """ FPGABoard subclass for communicating with a ROACH board """

    def __init__(self, *args, **kwargs):
        """ Class constructor """
        kwargs['fpgaBoard'] = BoardMake.RoachBoard
        super(Roach, self).__init__(**kwargs)

    def connect(self, ip, port):
        """ Add functionality to connect in order to check whether the
            roach is already programmed
        :param ip: ROACH IP
        :param port: port
        """

        # Connect to board
        super(Roach, self).connect(ip, port)

        # Check if ROACH is programmed (has any registers loaded)
        self._programmed = True
        if len(self.get_register_list()) == 0:
            self._programmed = False

    def get_register_list(self, load_values = False):
        """ Add functionality to getRegisterList in order to map register names 
            as python attributes """

        # Populate register list
        super(Roach, self).get_register_list(load_values)

        # Check if any register are present
        if self.register_list is None:
            return None

        # The super class will prepend the device type to the register name.
        # Since everyting on the roach is controlled by a single entity,
        # we don't need this. Remove prepended device type
        newRegList = { }
        for k in self.register_list.keys():
            newKey = k.replace("fpga1.", "")
            newRegList[newKey] = self.register_list[k]
            newRegList[newKey]['name'] = newKey
        self.register_list = newRegList

        return self.register_list

    def get_firmware_list(self):
        """ Roach helper for getFirmwareList """
        return super(Roach, self).get_firmware_list(Device.FPGA_1)

    def read_register(self, register, n = 1, offset = 0):
        """ Roach helper for readRegister """
        return super(Roach, self).read_register(register, n, offset, device = Device.FPGA_1)

    def write_register(self, register, values, offset = 0):
        """ Roach helper for writeRegister"""
        return super(Roach, self).write_register(register, values, offset, device = Device.FPGA_1)

    def load_firmware_blocking(self, boffile):
        """ Roach helper for loadFirmwareBlocking """
        return super(Roach, self).load_firmware_blocking(Device.FPGA_1, boffile)

    def load_firmware(self, boffile):
       """ Roach helpder for loadFirmware """
       return super(Roach, self).loadFirmware(Device.FPGA_1, boffile)

    def read_address(self, address, n = 1):
        """ Roach helper for readAddress """
        raise NotImplemented("Read memory address not supported for ROACH")

    def write_address(self, address, values):
        """ Roach helper for writeAddress """
        raise NotImplemented("Write memory address not supported for ROACH")

    def write_device(self, device, address, value):
        """ Roach helper for writeDevice """
        raise NotImplemented("Write device is not supported for ROACH")

    def read_device(self, device, address):
        """ Roach helper for readDevice """
        raise NotImplemented("Read device is not supported for ROACH")

    def __getitem__(self, key):
        """ Override __getitem__, return value from board """

        # Run checks
        if not self._checks():
            return

        # Check if register is valid
        if type(key) is str:
            if self.register_list.has_key(key):
                return self.read_register(key, self.register_list[key]['size'])
        else:
            raise LibraryError("Unrecognised key type, must be register name or memory address")

        # Register not found
        raise LibraryError("Register '%s' not found" % key)

    def __setitem__(self, key, value):
        """ Override __setitem__, set value on board"""

        # Run checks
        if not self._checks():
            return

        if type(key) is str:      
            # Check if register is valid
            if self.register_list.has_key(key):
                return self.write_register(key, value)
        else:
            raise LibraryError("Unrecognised key type, must be register name or memory address")

        # Register not found
        raise LibraryError("Register '%s' not found" % key)

    def __getattr__(self, name):
        """ Override __getattr__, get value from board """
        if name in self.__dict__:
            return self.__dict__[name]
        elif self.register_list is not None and name in self.register_list:
            return self.read_register(name)
        else:
            raise AttributeError("Register %s not found" % name)

    def __setattr__(self, name, value):
        """ Override __setattr__, set value on board"""
        if name in self.__dict__:
            self.__dict__[name] = value
        # Allow attributes to be defined normally during initialisation
        elif not self.__dict__.has_key('_FPGABoard__initialised'):
            return  dict.__setattr__(self, name, value)
        elif self.register_list is not None and name in self.register_list:
            self.write_register(name, value)
        else:
            raise AttributeError("Register %s not found % name")

    def __str__(self):
        """ Override __str__ to print register information in a human readable format """
        super(Roach, self).list_register_names()
        return ""

# if __name__ == '__main__':
#     roach = Roach(ip="192.168.100.2", port=7147)
#     roach.load_firmware_blocking('tut1_2015_Apr_11_1544.bof')
#     print roach.a
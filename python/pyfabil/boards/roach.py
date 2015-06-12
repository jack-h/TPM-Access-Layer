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

    def get_register_list(self):
        """ Add functionality to getRegisterList in order to map register names 
            as python attributes """

        # Populate register list
        super(Roach, self).get_register_list()

        # Check if any register are present
        if self._registerList is None:
            return None

        # The super class will prepend the device type to the register name.
        # Since everyting on the roach is controlled by a single entity,
        # we don't need this. Remove prepended device type
        newRegList = { }
        for k in self._registerList.keys():
            newKey = k.replace("fpga1.", "")
            newRegList[newKey] = self._registerList[k]
            newRegList[newKey]['name'] = newKey
        self._registerList = newRegList

        return self._registerList

    def get_firmware_list(self):
        """ Roach helper for getFirmwareList """
        return super(Roach, self).get_firmware_list(Device.FPGA_1)

    def read_register(self, register, n = 1, offset = 0):
        """ Roach helper for readRegister """
        return super(Roach, self).read_register(Device.FPGA_1, register, n, offset)

    def write_register(self, register, values, offset = 0):
        """ Roach helper for writeRegister"""
        return super(Roach, self).write_register(Device.FPGA_1, register, values, offset)

    def load_firmware_blocking(self, boffile):
        """ Roach helper for loadFirmwareBlocking """
        return super(Roach, self).load_firmware_blocking(Device.FPGA_1, boffile)

    def loadFirmware(self, boffile):
       """ Roach helpder for loadFirmware """
       return super(Roach, self).loadFirmware(Device.FPGA_1, boffile)

    def read_address(self, address, n = 1):
        """ Roach helper for readAddress """
        print "Read memory address not supported for ROACH"

    def write_address(self, address, values):
        """ Roach helper for writeAddress """
        print "Write memory address not supported for ROACH"

    def write_device(self, device, address, value):
        """ Roach helper for writeDevice """
        print "Write device is not supported for ROACH"

    def read_device(self, device, address):
        """ Roach helper for readDevice """
        print "Read device is not supported for ROACH"

    def __getitem__(self, key):
        """ Override __getitem__, return value from board """

        # Run checks
        if not self._checks():
            return

        # Check if register is valid
        if type(key) is str:
            if self._registerList.has_key(key):
                return self.read_register(key, self._registerList[key]['size'])
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
            if self._registerList.has_key(key):
                return self.write_register(key, value)
        else:
            raise LibraryError("Unrecognised key type, must be register name or memory address")

        # Register not found
        raise LibraryError("Register '%s' not found" % key)

    def __getattr__(self, name):
        """ Override __getattr__, get value from board """
        if name in self.__dict__:
            return self.__dict__[name]
        elif self._registerList is not None and name in self._registerList:
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
        elif self._registerList is not None and name in self._registerList:
            self.write_register(name, value)
        else:
            raise AttributeError("Register %s not found % name")

    def __str__(self):
        """ Override __str__ to print register information in a human readable format """
        super(Roach, self).list_register_names()
        return ""

from pyfabil.boards.fpgaboard import FPGABoard, DeviceNames
from pyfabil.base.definitions import *

class TPM(FPGABoard):
    """ FPGABoard subclass for communicating with a TPM board """

    def __init__(self, **kwargs):
        """ Class constructor """
        kwargs['fpgaBoard'] = BoardMake.TpmBoard
        super(TPM, self).__init__(**kwargs)

    def __getitem__(self, key):
        """ Override __getitem__, return value from board """

        # Run checks
        if not self._checks():
            return

        # Check if the specified key is a memory address or register name
        if type(key) is int:
            return self.read_address(key)

        # Checkl if the specified key is a tuple, in which case we are reading from a device
        if type(key) is tuple:
            if len(key) == 2:
                return self.read_device(key[0], key[1])
            else:
                raise LibraryError("A device name and address need to be specified for writing to SPI devices")

        elif type(key) is str:
            # Check if a device is specified in the register name
            if self._registerList.has_key(key):
                reg = self._registerList[key]
                return self.read_register(key, reg['size'])
        else:
            raise LibraryError("Unrecognised key type, must be register name or memory address")

        # Register not found
        raise LibraryError("Register %s not found" % key)

    def __setitem__(self, key, value):
        """ Override __setitem__, set value on board"""

        # Run checks
        if not self._checks():
            return

        # Check is the specified key is a memory address or register name
        if type(key) is int:
            return self.write_address(key, value)

        # Check if the specified key is a tuple, in which case we are writing to a device
        if type(key) is tuple:
            if len(key) == 2:
                return self.write_device(key[0], key[1], value)
            else:
                raise LibraryError("A device name and address need to be specified for writing to SPI devices")

        elif type(key) is str:      
            # Check if device is specified in the register name
            if self._registerList.has_key(key):
                return self.write_register(key, value)
        else:
            raise LibraryError("Unrecognised key type, must be register name or memory address")

        # Register not found
        raise LibraryError("Register %s not found" % key)

    def __str__(self):
        """ Override __str__ to print register information in a human readable format """

        if not self._programmed:
            return ""

        # Run checks
        if not self._checks():
            return

        # Split register list into devices
        registers = { }
        for k, v in self._registerList.iteritems():
            if v['device'] not in registers.keys():
                registers[v['device']] = []
            registers[v['device']].append(v)

        # Loop over all devices
        string  = "Device%sRegister%sAddress%sBitmask\n" % (' ' * 2, ' ' * 37, ' ' * 8)
        string += "------%s--------%s-------%s-------\n" % (' ' * 2, ' ' * 37, ' ' * 8)
    
        for k, v in registers.iteritems():
            for reg in sorted(v, key = lambda arg : arg['name']):
                regspace = ' ' * (45 - len(reg['name']))
                adspace  = ' ' * (15 - len(hex(reg['address'])))
                string += '%s\t%s%s%s%s0x%08X\n' % (DeviceNames[k], reg['name'], regspace, hex(reg['address']), adspace, reg['bitmask'])

        # Add SPI devices
        if len(self._deviceList) > 0:
            string += "\nSPI Devices\n"
            string += "-----------\n"

        for v in sorted(self._deviceList.itervalues(), key = lambda arg : arg['name']):
            string += 'Name: %s\tspi_sclk: %d\tspi_en: %d\n' % (v['name'], v['spi_sclk'], v['spi_en'])

        # Return string representation
        return string
from interface import *
from math import ceil
import numpy as np
import ctypes
import os
import re

# --------------- Helpers ------------------------------
DeviceNames = { Device.Board : "Board", Device.FPGA_1 : "FPGA 1", Device.FPGA_2 : "FPGA 2" }

# ------------------------------------------------------

# Wrap functionality for a TPM board
class FPGABoard(object):
    """ Class which wraps LMC functionality for generic FPGA boards """

    # Class constructor
    def __init__(self, **kwargs):
        """ Class constructor for FPGABoard"""

        # Set defaults
        self._registerList = None
        self._firmwareList = None
        self._fpgaBoard    = 0
        self._deviceList   = None
        self.id            = None
        self.status        = Status.NotConnected
        self._programmed   = False

        # Override to make this compatible with IPython
        self.__methods__        = None
        self.trait_names        = None
        self._getAttributeNames = None
        self.__members__        = None

        # Used by __setattr__ to know how to handle new attributes
        self.__initialised = True  

        # Check if FPGA board type is specified
        self._fpgaBoard = kwargs.get('fpgaBoard', None)
        if self._fpgaBoard is None:
            print "fpgaBoard type must be specified"
            return

        # Check if filepath is included in arguments
        filepath = kwargs.get('library', None)

        # Initialise library
        initialiseLibrary(filepath)

        # Check if ip and port are defined in arguments
        ip   = kwargs.get('ip', None)
        port = kwargs.get('port', None)

        # If so, the connect immediately
        if not (ip is None and port is None):
            self.connect(ip, port)

    def connect(self, ip, port):
        """ Connect to board
        :param ip: Board IP
        :param port: Port to connect to
        :return: Success of Failure
        """

        board_id = callConnectBoard(self._fpgaBoard.value, ip, port)
        if board_id == 0:
            print "Could not connect to board"
            self.status = Status.NetworkError
        else:
            self.id = board_id
            self.status = Status.OK

    def disconnect(self):
        """ Disconnect from board
        :return: Success or Failure
        """

        # Check if board is connected
        if self.id is None:
            print "Board not connected"
            return Error.Failure

        ret = callDisconnectBoard(self.id)
        if ret == Error.Success:
            self.id = None
            self._registerList = None
        return ret

    def getFirmwareList(self, device):
        """ Get list of firmware on board
        :param device: Device on board to get list of firmware
        :return: List of firmware
        """

        # Check if board is connected
        if self.id is None:
            print "Board not connected"
            return Error.Failure

        # Call getFirmware on board
        self._firmwareList = callGetFirmwareList(self.id, device)

        return self._firmwareList
        
    def loadFirmwareBlocking(self, device, filepath):
        """ Blocking call to load firmware
         :param device: Device on board to load firmware to
         :param filepath: Path to firmware
         :return: Success of Failure
         """
        
        # Check if device argument is of type Device
        if not type(device) is Device:
            print "device argument should be of type Device"
            return

        # All OK, call function
        err = callLoadFirmwareBlocking(self.id, device, filepath)

        # If call succeeded, get register and device list
        if err == Error.Success:
            self._programmed = True
            self.getRegisterList()
            self.getDeviceList()
        else:
            self._programmed = False
            print "Failed to program Roach"

    def getRegisterList(self):
        """ Get list of registers """

        # Check if register list has already been acquired, and if so return it
        if self._registerList is not None:
            return self._registerList

        # Check if device is programmed
        if not self._programmed:
            print "Device must be programmed before register list can be loaded"
            return

        # Call function
        self._registerList = callGetRegisterList(self.id)

        # All done, return
        return self._registerList


    def getDeviceList(self):
        """ Get list of SPI devices """

        # Check if register list has already been acquired, and if so return it
        if self._deviceList is not None:
            return self._deviceList

        # Call function
        self._deviceList = callGetDeviceList(self.id)

        # All done, return
        return self._deviceList

    def readRegister(self, device, register, n = 1, offset = 0):
        """" Get register value
         :param device: Device on board to read register from
         :param register: Register name
         :param n: Number of words to read
         :param offset: Memory address offset to read from
         :return: Values
         """

        # Perform basic checks
        if not self._checks():    
            return

        # Check if device argument is of type Device
        if not type(device) is Device:
            print "device argument should be of type Device"
            return

        # Call function
        values = callReadRegister(self.id, device, register, n, offset)

        # Check if value succeeded, otherwise return
        if values.error == Error.Failure.value:
            return Error.Failure

        # Read succeeded, wrap data and return
        valPtr = ctypes.cast(values.values, ctypes.POINTER(ctypes.c_uint32))

        if n == 1:
            return valPtr[0]
        else:
            return [valPtr[i] for i in range(n)]

    def writeRegister(self, device, register, values, offset = 0):
        """ Set register value
         :param device: Device on board to write register to
         :param register: Register name
         :param values: Values to write
         :param offset: Memory address offset to write to
         :return: Success or Failure
         """

        # Perform basic checks
        if not self._checks():    
            return

        # Check if device argument is of type Device
        if not type(device) is Device:
            print "device argument should be of type Device"
            return

        # Call function and return
        return callWriteRegister(self.id, device, register, values, offset)

    def readAddress(self, address, n = 1):
        """" Get register value
         :param address: Memory address to read from
         :param n: Number of words to read
         :return: Values
         """

        # Call function and return
        return  callReadAddress(self.id, address, n)

    def writeAddress(self, address, values):
        """ Set register value
         :param address: Memory address to write to
         :param values: Values to write
         :return: Success of Failure
         """

        # Call function and return
        return callWriteAddress(self.id, address, values)


    def readDevice(self, device, address):
        """" Get device value
         :param device: SPI Device to read from
         :param address: Address on device to read from
         :return: Value
         """
    
        # Check if device is in device list
        if device not in self._deviceList:
            print "Device not found in device list"
            return

        # Call function and return
        return callReadDevice(self.id, device, address)

    def writeDevice(self, device, address, value):
        """ Set device value
        :param device: SPI device to write to
        :param address: Address on device to write to
        :param value: Value to write
        :return: Success or Failure
        """

        # Check if device is in device list
        if device not in self._deviceList:
            print "Device not found in device list"
            return

        # Call function and return
        return callWriteDevice(self.id, device, address, value)

    def listRegisterNames(self):
        """ Print list of register names """
        
        # Run checks
        if not self._checks():
            return

        # Split register list into devices
        registers = { }
        for k, v in self._registerList.iteritems():
            if v['device'] not in registers.keys():
                registers[v['device']] = []
            registers[v['device']].append(k)

        # Loop over all devices
        for k, v in registers.iteritems():
            print DeviceNames[k]
            print '-' * len(DeviceNames[k])
            for regname in sorted(v):
                print '\t' + str(regname)

    def listDeviceNames(self):
        """ Print list of SPI device names """
        
        # Run check
        if not self._checks():
            return

        # Loop over all SPI devices
        print "List of SPI Devices"
        print "-------------------"
        for k in self._deviceList:
            print k

    def findRegister(self, string, display = False):
        """ Return register information for provided search string
         :param string: Regular expression to search against
         :param display: True to output result to console
         :return: List of found registers
         """
        
        # Run checks
        if not self._checks():
            return

        # Go through all registers and store the name of registers
        # which generate a match
        matches = []
        for k, v in self._registerList.iteritems():
            if re.search(string, k) is not None:
                matches.append(v)

        # Display to screen if required
        if display:
            string = "\n"
            for v in sorted(matches, key = lambda l : l['name']):
                string += '%s:\n%s\n'            % (v['name'], '-' * len(v['name']))
                string += 'Address:\t%s\n'       % (hex(v['address']))
                string += 'Type:\t\t%s\n'        % str(v['type'])
                string += 'Device:\t\t%s\n'      % str(v['device'])
                string += 'Permission:\t%s\n'    % str(v['permission'])
                string += 'Bitmask:\t0x%X\n'     % v['bitmask']
                string += 'Bits:\t\t%d\n'        % v['bits']
                string += 'Size:\t\t%d\n'        % v['size']
                string += 'Description:\t%s\n\n' % v['description']

            print string

        # Return matches
        return matches

    def findDevice(self, string, display = False):
        """ Return SPI device information for provided search string
         :param string: Regular expression to search against
         :param display: True to output result to console
         :return: List of found devices
         """

        # Run check
        if not self._check():
            return

        # Loop over all devices
        matches = []
        for k, v in self._deviceList:
            if re.match(string, k) is not None:
                matches.append(v)

        # Display to screen if required
        if display:
            string = "\n"
            for v in sorted(matches, key = lambda l : l['name']):
                string += 'Name: %s, spi_sclk: %d, spi_en: %d\n' % (v['name'], v['spi_sclk'], v['spi_en'])
            print string

        # Return matches
        return matches

    def __len__(self):
        """ Override __len__, return number of registers """
        if self._registerList is not None:
            return len(self._registerList.keys())

    def _checks(self):
        """ Check prior to function calls """

        # Check if board is connected
        if self.id is None:
            print "Board not connected"
            return False

        # Check if device is programmed
        if not self._programmed:
            print "Device not programmed"
            return False

        # Check if register list has been populated
        if self._registerList is None:
            self.getRegisterList()

        return True

    @staticmethod
    def _getDevice(name):
        """ Extract device name from provided register name, if present """

        try:
            device = name.split('.')[0].upper()
            if device == "BOARD":
                return Device.Board
            elif device == "FPGA1":
                return Device.FPGA_1
            elif device == "FPGA2":
                return Device.FPGA_2
            else:
                return None
        except:
            return None

# ================================== TPM Board ======================================
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
            return self.readAddress(key)

        # Checkl if the specified key is a tuple, in which case we are reading from a device
        if type(key) is tuple:
            if len(key) == 2:
                return self.readDevice(key[0], key[1])
            else:
                print "A device name and address need to be specified for reading SPI devices"

        elif type(key) is str:
            # Check if a device is specified in the register name
            device = self._getDevice(key)
            if self._registerList.has_key(key):
                reg = self._registerList[key]
                key = '.'.join(key.split('.')[1:])
                return self.readRegister(device, key, reg['size'])
        else:
            print "Unrecognised key type. Use register name or memory address"
            return

        # Register not found
        print "Register '%s' not found" % key

    def __setitem__(self, key, value):
        """ Override __setitem__, set value on board"""

        # Run checks
        if not self._checks():
            return

        # Check is the specified key is a memory address or register name
        if type(key) is int:
            return self.writeAddress(key, value)

        # Check if the specified key is a tuple, in which case we are writing to a device
        if type(key) is tuple:
            if len(key) == 2:
                return self.writeDevice(key[0], key[1], value)
            else:
                print "A device name and address need to be specified for writing to SPI devices"

        elif type(key) is str:      
            # Check if device is specified in the register name
            device = self._getDevice(key)
            if self._registerList.has_key(key):
                key = '.'.join(key.split('.')[1:])
                return self.writeRegister(device, key, value)
        else:
            print "Unrecognised key type. Use register name or memory address"
            return

        # Register not found
        print "Register '%s' not found" % key   

    def __str__(self):
        """ Override __str__ to print register information in a human readable format """
        
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
        string  = "Device%sRegister%sAddress%sBitmask\n" % (' ' * 2, ' ' * 27, ' ' * 8)
        string += "------%s--------%s-------%s-------\n" % (' ' * 2, ' ' * 27, ' ' * 8)
    
        for k, v in registers.iteritems():
            for reg in sorted(v, key = lambda k : k['name']):
                regspace = ' ' * (35 - len(reg['name']))
                adspace  = ' ' * (15 - len(hex(reg['address'])))
                string += '%s\t%s%s%s%s0x%08X\n' % (DeviceNames[k], reg['name'], regspace, hex(reg['address']), adspace, reg['bitmask'])

        # Add SPI devices
        if len(self._deviceList) > 0:
            string += "\nSPI Devices\n"
            string += "-----------\n"

        for v in sorted(self._deviceList.itervalues(), key = lambda k : k['name']):
            string += 'Name: %s\tspi_sclk: %d\tspi_en: %d\n' % (v['name'], v['spi_sclk'], v['spi_en'])

        # Return string representation
        return string

# ================================= ROACH Board ====================================
class Roach(FPGABoard):
    """ FPGABoard subclass for communicating with a ROACH board """

    def __init__(self, *args, **kwargs):
        """ Class constructor """
        kwargs['fpgaBoard'] = BoardMake.RoachBoard
        super(Roach, self).__init__(**kwargs)

    def getRegisterList(self):
        """ Add functionality to getRegisterList in order to map register names 
            as python attributes """

        # Populate register list
        super(Roach, self).getRegisterList()

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

    def getFirmwareList(self):
        """ Roach helper for getFirmwareList """
        return super(Roach, self).getFirmwareList(Device.FPGA_1)

    def readRegister(self, register, n = 1, offset = 0):
        """ Roach helper for readRegister """
        return super(Roach, self).readRegister(Device.FPGA_1, register, n, offset)

    def writeRegister(self, register, values, offset = 0):
        """ Roach helper for writeRegister"""
        return super(Roach, self).writeRegister(Device.FPGA_1, register, values, offset)

    def loadFirmwareBlocking(self, boffile):
        """ Roach helper for loadFirmwareBlocking """
        return super(Roach, self).loadFirmwareBlocking(Device.FPGA_1, boffile)

    def loadFirmware(self, boffile):
       """ Roach helpder for loadFirmware """
       return super(Roach, self).loadFirmware(Device.FPGA_1, boffile)

    def readAddress(self, address, n = 1):
        """ Roach helper for readAddress """
        print "Read memory address not supported for ROACH"

    def writeAddress(self, address, values):
        """ Roach helper for writeAddress """
        print "Write memory address not supported for ROACH"

    def writeDevice(self, device, address, value):
        """ Roach helper for writeDevice """
        print "Write device is not supported for ROACH"

    def readDevice(self, device, address):
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
                return self.readRegister(key, self._registerList[key]['size'])
        else:
            print "Unrecognised key type. Use register name or memory address"
            return

        # Register not found
        print "Register '%s' not found" % key

    def __setitem__(self, key, value):
        """ Override __setitem__, set value on board"""

        # Run checks
        if not self._checks():
            return

        if type(key) is str:      
            # Check if register is valid
            if self._registerList.has_key(key):
                return self.writeRegister(key, value)
        else:
            print "Unrecognised key type. Use register name or memory address"
            return

        # Register not found
        print "Register '%s' not found" % key       

    def __getattr__(self, name):
        """ Override __getattr__, get value from board """
        if name in self.__dict__:
            return self.__dict__[name]
        elif self._registerList is not None and name in self._registerList:
            return self.readRegister(name)
        else:
            print "Register %s not found" % name
            raise AttributeError

    def __setattr__(self, name, value):
        """ Override __setattr__, set value on board"""
        if name in self.__dict__:
            self.__dict__[name] = value
        # Allow attributes to be defined normally during initialisation
        elif not self.__dict__.has_key('_FPGABoard__initialised'):
            return  dict.__setattr__(self, name, value)
        elif self._registerList is not None and name in self._registerList:
            self.writeRegister(name, value)
        else:
            print "Register %s not found" % name
            raise AttributeError  

    def __str__(self):
        """ Override __str__ to print register information in a human readable format """
        super(Roach, self).listRegisterNames()
        return ""

if __name__ == "__main__":
    # Simple TPM test
    tpm = TPM(ip="127.0.0.1", port=10000)
    tpm.loadFirmwareBlocking(Device.FPGA_1, "/home/lessju/map.xml")
    tpm['fpga1.regfile.block2048b'] = [1] * 512
    print tpm['fpga1.regfile.block2048b']
    tpm.disconnect()

    # Simple ROACH test
    roach = Roach(ip="192.168.100.2", port=7147)
    roach.getFirmwareList()
    roach.loadFirmwareBlocking("fenggbe.bof")
    roach.amp_EQ0_coeff_bram = range(4096)
    print roach.readRegister('amp_EQ0_coeff_bram', 4096)
    roach.disconnect()
from sys import platform
from math import ceil
from enum import Enum
import numpy as np
import ctypes, os
import re

# --------------- Enumerations --------------------------

# Error
class Error(Enum):
    Success = 0
    Failure = -1
    NotImplemented = -2

# Device
class Device(Enum):
    Board = 1
    FPGA_1 = 2
    FPGA_2 = 4

# BoardMake
class BoardMake(Enum):
    TpmBoard      = 1
    RoachBoard    = 2
    Roach2Board   = 3
    UniboardBoard = 4

# Status
class Status(Enum):
    OK = 0
    LoadingFirmware = -1
    ConfigError = -2
    BoardError = -3
    NotConnected = -4
    NetworkError = -5

# RegisterType
class RegisterType(Enum):
    Sensor = 1
    BoardRegister = 2
    FirmwareRegister = 3
    SPIDevice = 4
    Component = 5

# Permission
class Permission(Enum):
    Read      = 1
    Write     = 2
    ReadWrite = 3

# --------------- Structures --------------------------
class Values:
    def __init__(self, values, error):
        self.values = values
        self.error = error

class RegisterInfo:
    def __init__(self, name, address, reg_type, device, permission, bitmask, bits, size, desc):
        self.name = name    
        self.address = address
        self.type = reg_type
        self.device = device
        self.permission = permission
        self.bitmask = bitmask
        self.bits = bits
        self.size = size
        self.desc = desc

class SPIDeviceInfo:
    def __init__(self, name, spi_sclk, spi_en):
        self.name     = name
        self.spi_sclk = spi_sclk
        self.spi_en   = spi_en

# --------------- Helpers ------------------------------
DeviceNames = { Device.Board : "Board", Device.FPGA_1 : "FPGA 1", Device.FPGA_2 : "FPGA 2" }

# ------------------------------------------------------

# Wrap functionality for a TPM board
class FPGABoard(object):

    # Define ctype wrapper to library structures
    class ValuesStruct(ctypes.Structure):
        _fields_ = [
            ('values', ctypes.POINTER(ctypes.c_uint32)),
            ('error', ctypes.c_int)
        ]

    class RegisterInfoStruct(ctypes.Structure):
        _fields_ = [    
            ('name',        ctypes.c_char_p),
            ('address',     ctypes.c_uint32),
            ('type',        ctypes.c_int),
            ('device',      ctypes.c_int),
            ('permission',  ctypes.c_int),
            ('bitmask',     ctypes.c_uint32),
            ('bits',        ctypes.c_uint32),
            ('size',        ctypes.c_uint32),
            ('description', ctypes.c_char_p)
        ]
    
    class SPIDeviceInfoStruct(ctypes.Structure):
        _fields_ = [
            ('name',     ctypes.c_char_p),
            ('spi_sclk', ctypes.c_uint32),
            ('spi_en',   ctypes.c_uint32)
        ]

    # Class constructor
    def __init__(self, *args, **kwargs):
        """ Class constructor """

        # Set defaults
        self._registerList = None
        self._fpgaBoard    = 0
        self._deviceList   = None
        self.id            = None
        self.status        = Status.NotConnected
        self._programmed   = False
        self._library       = None
        self._board        = None

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
        self._initialiseLibrary(filepath)

        # Check if ip and port are defined in arguments
        ip   = kwargs.get('ip', None)
        port = kwargs.get('port', None)

        # If so, the connect immediately
        if not (ip is None and port is None):
            self.connect(ip, port)

    def connect(self, ip, port):
        """ Connect to board """
        boardId = self._board.connectBoard(self._fpgaBoard.value, ip, port)
        if boardId == 0:
            print "Could not connect to board"
            self.status = Status.NetworkError
            return Error.Failure
        else:
            self.id = boardId
            self.status = Status.OK
            return Error.Success

    def disconnect(self):
        """ Disconnect from board """

        # Check if board is connected
        if self.id is None:
            print "Board not connected"
            return Error.Failure

        ret = Error(self._board.disconnectBoard(self.id))
        if (ret == Error.Success):
            self.id = None
            self._registerList = None
        return ret

    def getFirmwareList(self, device):
        """ Get list of firmware on board"""

        # Check if board is connected
        if self.id is None:
            print "Board not connected"
            return Error.Failure

        # Create an integer and extract it's address
        INTP = ctypes.POINTER(ctypes.c_int)
        num  = ctypes.c_int(0)
        addr = ctypes.addressof(num)
        ptr  = ctypes.cast(addr, INTP)

        # Call library function
        firmware = self._board.getFirmware(self.id, device.value, ptr)

        # Process all firmware
        firmwareList = [firmware[i] for i in range(num.value)]

        # Free firmware pointer
        self._board.freeMemory(firmware)

        # Store as class member and return
        self._firmwareList = firmwareList
        return firmwareList
        
    def loadFirmwareBlocking(self, device, filepath):
        """ Blocking call to load firmware """
        
        # Check if device argument is of type Device
        if not type(device) is Device:
            print "device argument should be of type Device"
            return

        # Check if filepath is valid
        # if not os.path.isfile(filepath):
        #    print "Invalid file path %s" % filepath
        #    return

        # All OK, call function
        err = Error(self._board.loadFirmwareBlocking(self.id, device.value, filepath))

        # If call succeeded, get register and device list
        if err == Error.Success:
            self._programmed = True
            self.getRegisterList()
            self.getDeviceList()
        else:
            self._programmed = False

        # Return 
        return err

    def getRegisterList(self):
        """ Get list of registers """

        # Check if register list has already been acquired, and if so return it
        if self._registerList is not None:
            return self._registerList

        # Check if device is programmed
        if not self._programmed:
            print "Device must be programmed before register list can be loaded"
            return

        # Create an integer and extract it's address
        INTP = ctypes.POINTER(ctypes.c_int)
        num  = ctypes.c_int(0)
        addr = ctypes.addressof(num)
        ptr  = ctypes.cast(addr, INTP)

        # Call function
        registers = self._board.getRegisterList(self.id, ptr)

        # Create device map for register names
        names = { Device.Board : "board", Device.FPGA_1 : "fpga1", Device.FPGA_2 : "fpga2" }

        # Wrap register formats and return
        registerList = { }
        for i in range(num.value):
            reg = { }
            reg['name']        = registers[i].name
            reg['address']     = registers[i].address
            reg['type']        = RegisterType(registers[i].type)
            reg['device']      = Device(registers[i].device)
            reg['permission']  = Permission(registers[i].permission)
            reg['size']        = registers[i].size
            reg['bitmask']     = registers[i].bitmask
            reg['bits']        = registers[i].bits
            #TODO: Check below
#            reg['description'] = registers[i].description
            registerList["%s.%s" % (names[reg['device']], reg['name'])] = reg

        # Store register list locally for get and set items
        self._registerList = registerList

        # Free registers pointer
        # TODO: Does not work for Roach
#        self._board.freeMemory(regist   ers)

        return registerList

    def getDeviceList(self):
        """ Get list of SPI devices """

        # Check if register list has already been acquired, and if so return it
        if self._deviceList is not None:
            return self._deviceList

        # Create an integer and extract it's address
        INTP = ctypes.POINTER(ctypes.c_uint32)
        num  = ctypes.c_uint32(0)
        addr = ctypes.addressof(num)
        ptr  = ctypes.cast(addr, INTP)

        # Call function
        devices = self._board.getDeviceList(self.id, ptr)

        # Wrap register formats and return
        deviceList = { }
        for i in range(num.value):
            reg = { }
            reg['name']      = devices[i].name
            reg['spi_en']    = devices[i].spi_en
            reg['spi_sclk']  = devices[i].spi_sclk
            deviceList[reg['name']] = reg

        # Store register list locally for get and set items
        self._deviceList = deviceList

        # Free registers pointer
        self._board.freeMemory(devices)

        return deviceList

    def readRegister(self, device, register, n = 1, offset = 0):
        """" Get register value """

        # Perform basic checks
        if not self._checks():    
            return

        # Check if device argument is of type Device
        if not type(device) is Device:
            print "device argument should be of type Device"
            return

        # Call function
        values = self._board.readRegister(self.id, device.value, register, n, offset)

        # Check if value succeeded, otherwise reture
        if values.error == Error.Failure.value:
            return Error.Failure

        # Read succeeded, wrap data and return
        valPtr = ctypes.cast(values.values, ctypes.POINTER(ctypes.c_uint32))

        if n == 1:
            return valPtr[0]
        else:
            return [valPtr[i] for i in range(n)]

    def writeRegister(self, device, register, values, offset = 0):
        """ Set register value """

        # Perform basic checks
        if not self._checks():    
            return

        # Check if device argument is of type Device
        if not type(device) is Device:
            print "device argument should be of type Device"
            return

        # Check if we have a single value or list of values
        if type(values) is not list:

            # Create an integer and extract it's address
            INTP = ctypes.POINTER(ctypes.c_uint32)
            num  = ctypes.c_uint32(values)
            addr = ctypes.addressof(num)
            ptr  = ctypes.cast(addr, INTP)

            print "Calling write register"
            err = self._board.writeRegister(self.id, device.value,
                                            register, ptr, 1, offset)
            return err

        elif type(values) is list:
            n = len(values)
            vals = (ctypes.c_uint32 * n) (*values)
            return Error(self._board.writeRegister(self.id, device.value,
                                                 register, vals, n, offset))
        else:
            print "Something not quite right in writeRegister"

    def readAddress(self, address, n = 1):
        """" Get register value """

        # Call function
        values = self._board.readAddress(self.id, address, n)

        # Check if value succeeded, otherwise reture
        if values.error == Error.Failure.value:
            return Error.Failure

        # Read succeeded, wrap data and return
        valPtr = ctypes.cast(values.values, ctypes.POINTER(ctypes.c_uint32))

        if n == 1:
            return valPtr[0]
        else:
            return [valPtr[i] for i in range(n)]

    def writeAddress(self, address, values):
        """ Set register value """

        # Check if we have a single value or list of values
        if type(values) is not list:

            # Create an integer and extract it's address
            INTP = ctypes.POINTER(ctypes.c_uint32)
            num  = ctypes.c_uint32(values)
            addr = ctypes.addressof(num)
            ptr  = ctypes.cast(addr, INTP)

            return Error(self._board.writeAddress(self.id, address, ptr))

        elif type(values) is list:
            n = len(values)
            vals = (ctypes.c_uint32 * n) (*values)
            return Error(self._board.writeAddress(self.id, address, vals, n))
        else:
            print "Something not quite right in writeAddress"


    def readDevice(self, device, address):
        """" Get device value """
    
        # Check if device is in device list
        if device not in self._deviceList:
            print "Device not found in device list"
            return

        # Call function
        values = self._board.readDevice(self.id, device, address)

        # Check if value succeeded, otherwise reture
        if values.error == Error.Failure.value:
            return Error.Failure

        # Read succeeded, wrap data and return
        valPtr = ctypes.cast(values.values, ctypes.POINTER(ctypes.c_uint32))

        if n == 1:
            return valPtr[0]
        else:
            return [valPtr[i] for i in range(n)]

    def writeDevice(self, device, address, value):
        """ Set device value """

        # Check if device is in device list
        if device not in self._deviceList:
            print "Device not found in device list"
            return

        # Call function
        return Error(self._board.writeDevice(self.id, device, address, value))

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
        """ Return register information for provided search string """
        
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
            for v in sorted(matches, key = lambda k : k['name']):
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
        """ Return SPI device information for provided search string """

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
            for v in sorted(matches, key = lambda k : k['name']):
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

    def _getDevice(self, name):
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

    def _initialiseLibrary(self, filepath = None):
        """ Initialise library """
       
        # Load access layer shared library
        if filepath is None:
            self._library = "libboard"
        else:
            self._library = filepath

        # Library found, load it (OS-specific)
        if platform.find('linux') >= 0:
            self._board = ctypes.CDLL(self._library + ".so")
        elif platform in ['win32', 'cygwin']:
            self._board = ctypes.WinDLL(self._library)
        else:
            print "Unsupported operating system"
            return            

        # Define connect function
        self._board.connectBoard.argtypes = [ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint16]
        self._board.connectBoard.restype  = ctypes.c_uint32

        # Define disconnect function
        self._board.disconnectBoard.argtypes = [ctypes.c_uint32]
        self._board.disconnectBoard.restype  = ctypes.c_int

        # Define getFirmware function
        self._board.getFirmware.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        self._board.getFirmware.restype = ctypes.POINTER(ctypes.c_char_p)

        # Define loadFirmwareBlocking function
        self._board.loadFirmwareBlocking.argtypes =  [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p]
        self._board.loadFirmwareBlocking.restype = ctypes.c_int

        # Define getRegisterList function
        self._board.getRegisterList.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_int)]
        self._board.getRegisterList.restype = ctypes.POINTER(self.RegisterInfoStruct)

        # Define readRegister function
        self._board.readRegister.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
        self._board.readRegister.restype = self.ValuesStruct

        # Define writeRegister function
        self._board.writeRegister.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32, ctypes.c_uint32]
        self._board.writeRegister.restype = ctypes.c_int

        # Define readRegister function
        self._board.readAddress.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
        self._board.readAddress.restype = self.ValuesStruct

        # Define writeRegister function
        self._board.writeAddress.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
        self._board.writeAddress.restype = ctypes.c_int

        # Define getDeviceList function
        self._board.getDeviceList.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
        self._board.getDeviceList.restype = ctypes.POINTER(self.SPIDeviceInfoStruct)

        # Define readDevice function
        self._board.readDevice.argtypes = [ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32]
        self._board.readDevice.restype = self.ValuesStruct

        # Define writeDevice function
        self._board.writeDevice.argtypes = [ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_uint32]
        self._board.writeDevice.restype = ctypes.c_int

        # Define freeMemory function
        self._board.freeMemory.argtypes = [ctypes.c_void_p]

# ================================== TPM Board ======================================
class TPM(FPGABoard):
    """ FPGABoard subclass for communicating with a TPM board """

    def __init__(self, *args, **kwargs):
        """ Class constructor """
        kwargs['fpgaBoard'] = BoardMake.TpmBoard
        super(TPM, self).__init__(*args, **kwargs)

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
                reg = self._registerList[key]
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
        return super(Roach, self).__init__(*args, **kwargs)

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
            return dict.__setattr__(self, name, value)
        elif self._registerList is not None and name in self._registerList:
            self.writeRegister(name, value)
        else:
            print name, dir(self)
            print "Register %s not found" % name
            raise AttributeError  

    def __str__(self):
        """ Override __str__ to print register information in a human readable format """
        super(Roach, self).listRegisterNames()
        return ""

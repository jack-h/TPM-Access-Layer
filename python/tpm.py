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

# --------------- Helpers ------------------------------
DeviceNames = { Device.Board : "Board", Device.FPGA_1 : "FPGA 1", Device.FPGA_2 : "FPGA 2" }

# ------------------------------------------------------

# Wrap functionality for a TPM board
class TPM:

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

    # Class constructor
    def __init__(self, *args, **kwargs):
        """ Class constructor """

        # Check if filepath is included in arguments
        filepath = kwargs.get('library', None)

        # Initialise library
        self._initialiseLibrary(filepath)

        # Check if ip and port are defined in arguments
        ip   = kwargs.get('ip', None)
        port = kwargs.get('port', None)

        # Set registerList to None
        self._registerList = None

        # Set ID to None
        self.id = None

        # Set board status  
        self.status = None

        # If so, the connect immediately
        if not (ip is None and port is None):
            self.connect(ip, port)

    def connect(self, ip, port):
        """ Connect to board """
        boardId = self._tpm.connectBoard(ip, port)
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

        ret = Error(self._tpm.disconnectBoard(self.id))
        if (ret == Error.Success):
            self.id = None
            self._registerList = None
        return ret

    def loadFirmwareBlocking(self, device, filepath):
        """ Blocking call to load firmware """
        
        # Check if device argument is of type Device
        if not type(device) is Device:
            print "device argument should be of type Device"
            return

        # Check if filepath is valid
        if not os.path.isfile(filepath):
            print "Invalid file path %s" % filepath
            return

        # All OK, call function
        err = Error(self._tpm.loadFirmwareBlocking(self.id, device.value, filepath))

        # If call succeeded, get register list
        if err == Error.Success:
            self.getRegisterList()

        # Return 
        return err

    def getRegisterList(self):
        """ Get list of registers """

        # Check if register list has already been acquired, and if so return it
        if self._registerList is not None:
            return self._registerList

        # Create an integer and extract it's address
        INTP = ctypes.POINTER(ctypes.c_int)
        num  = ctypes.c_int(0)
        addr = ctypes.addressof(num)
        ptr  = ctypes.cast(addr, INTP)

        # Call function
        registers = self._tpm.getRegisterList(self.id, ptr)

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
            reg['description'] = registers[i].description
            registerList[reg['name']] = reg

        # Store register list locally for get and set items
        self._registerList = registerList

        # Free registers pointer
        self._tpm.freeMemory(registers)

        return registerList

    def readRegister(self, device, register, n = 1, offset = 0):
        """" Get register value """
    
        # Check if device argument is of type Device
        if not type(device) is Device:
            print "device argument should be of type Device"
            return

        # Call function
        values = self._tpm.readRegister(self.id, device.value, register, n, offset)

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

            return Error(self._tpm.writeRegister(self.id, device.value,
                                                 register, 1, ptr, offset))

        elif type(values) is list:
            n = len(values)
            vals = (ctypes.c_uint32 * n) (*values)
            return Error(self._tpm.writeRegister(self.id, device.value,
                                                 register, n, vals, offset))
        else:
            print "Something not quite right in writeRegister"

    def readAddress(self, address, n = 1):
        """" Get register value """

        # Call function
        values = self._tpm.readAddress(self.id, address, n)

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

            return Error(self._tpm.writeAddress(self.id, address, 1, ptr))

        elif type(values) is list:
            n = len(values)
            vals = (ctypes.c_uint32 * n) (*values)
            return Error(self._tpm.writeAddress(self.id, address, n, vals))
        else:
            print "Something not quite right in writeAddress"


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

    def findRegister(self, string, display = False):
        """ Return register information for provided register """
        
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

    def __getitem__(self, key):
        """ Override __getitem__, return value from board """

        # Run checks
        if not self._checks():
            return

        # Check if the specified key is a memory address or register name
        if type(key) is int:
            return self.readAddress(key)

        elif type(key) is str:
            # Check if a device is specified in the register name
            device = self._getDevice(key)
            if device:
                # Device found, extract register name
                key = '.'.join(key.split('.')[1:])
                # Check if register list contains this register
                if self._registerList.has_key(key):
                    # Get register value
                    reg = self._registerList[key]
                    return self.readRegister(device, key, reg['size'])
            # No device specified, get register value
            else:            
                if self._registerList.has_key(key):
                    reg = self._registerList[key]
                    return self.readRegister(reg['device'], key, reg['size'])
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

        elif type(key) is str:      
            # Check if device is specified in the register name
            device = self._getDevice(key)
            if device:
                # Device found, extract register name
                key = key = '.'.join(key.split('.')[1:])
                # Check if register list contains the register
                if self._registerList.has_key(key):
                    reg = self._registerList[key]
                    return self.writeRegister(device, key, value)
            # No device found, get register value
            else:
                if self._registerList.has_key(key): 
                    reg = self._registerList[key]
                    return self.writeRegister(reg['device'], key, value)
        else:
            print "Unrecognised key type. Use register name or memory address"
            return

        # Register not found
        print "Register '%s' not found" % key       

    def __len__(self):
        """ Override __len__, return number of registers """
        if self._registerList is not None:
            return len(self._registerList.keys())

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

        # Return string representation
        return string

    def _checks(self):
        """ Check prior to function calls """

        # Check if board is connected
        if self.id is None:
            print "Board not connected"
            return False

        # Check if register list has been populated
        if self._registerList is None:
            #TODO: Check if board has been programmed
            self.getRegisterList()

        return True

    def _getDevice(self, name):
        """ Extract device name from provided register name, if present """

        try:
            device = name.split('.')[0].upper()
            print device
            if device in ['BOARD', 'CPLD', 'TPM']:
                return Device.Board
            elif device in ['FPGA_1', 'FPGA1']:
                return Device.FPGA_1
            elif device in ['FPGA2', 'FPGA_2']:
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
            self._tpm = ctypes.CDLL(self._library + ".so")
        elif platform in ['win32', 'cygwin']:
            self._tpm = ctypes.WinDLL(self._library)
        else:
            print "Unsupported operating system"
            return            

        # Define connect function
        self._tpm.connectBoard.argtypes = [ctypes.c_char_p, ctypes.c_uint16]
        self._tpm.connectBoard.restype  = ctypes.c_uint32

        # Define disconnect function
        self._tpm.disconnectBoard.argtypes = [ctypes.c_uint32]
        self._tpm.disconnectBoard.restype  = ctypes.c_int

        # Define loadFirmwareBlocking function
        self._tpm.loadFirmwareBlocking.argtypes =  [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p]
        self._tpm.loadFirmwareBlocking.restype = ctypes.c_int

        # Define getRegisterList function
        self._tpm.getRegisterList.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_int)]
        self._tpm.getRegisterList.restype = ctypes.POINTER(self.RegisterInfoStruct)

        # Define readRegister function
        self._tpm.readRegister.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
        self._tpm.readRegister.restype = self.ValuesStruct

        # Define writeRegister function
        self._tpm.writeRegister.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
        self._tpm.writeRegister.restype = ctypes.c_int

        # Define readRegister function
        self._tpm.readAddress.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
        self._tpm.readAddress.restype = self.ValuesStruct

        # Define writeRegister function
        self._tpm.writeAddress.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
        self._tpm.writeAddress.restype = ctypes.c_int

        # Define freeMemory function
        self._tpm.freeMemory.argtypes = [ctypes.c_void_p]

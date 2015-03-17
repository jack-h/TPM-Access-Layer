from enum import Enum
import numpy as np
import ctypes, os

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
    def __init__(self, name, reg_type, device, permission, size, desc):
        self.name = name    
        self.type = reg_type
        self.device = device
        self.permission = permission
        self.size = size
        self.desc = desc

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
            ('type',        ctypes.c_int),
            ('device',      ctypes.c_int),
            ('permission',  ctypes.c_int),
            ('bitmask',     ctypes.c_uint32),
            ('size',        ctypes.c_uint32),
            ('description', ctypes.c_char_p)
        ]

    # Class constructor
    def __init__(self, *args, **kwargs):
        """ Class constructor """

        # Check if filepath is included in arguments
        filepath = kwargs.get('filepath', None)

        # Initialise library
        self._initialiseLibrary(filepath)

        # Check if ip and port are defined in arguments
        ip   = kwargs.get('ip', None)
        port = kwargs.get('port', None)

        # Set registerList to None
        self._registerList = None

        # Set ID to None
        self.id = None

        # If so, the connect immediately
        if not (ip is None and port is None):
            self.connect(ip, port)

    def connect(self, ip, port):
        """ Connect to board """
        boardId = self._tpm.connectBoard(ip, port)
        if boardId < 1:
            return Error.Failure
        else:
            self.id = boardId
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
        registerList = {  }
        for i in range(num.value):
            reg = { }
            reg['name']        = registers[i].name
            reg['type']        = RegisterType(registers[i].type)
            reg['device']      = Device(registers[i].device)
            reg['permission']  = Permission(registers[i].permission)
            reg['size']        = registers[i].size
            reg['bitmask']     = registers[i].bitmask
            reg['description'] = registers[i].description
            registerList[reg['name']] = reg

        # Store register list locally for get and set items
        self._registerList = registerList

        return registerList

    def readRegister(self, device, register, n):
        """" Get register value """
    
        # Check if device argument is of type Device
        if not type(device) is Device:
            print "device argument should be of type Device"
            return

        # Call function
        values = self._tpm.readRegister(self.id, device.value, register, n)

        # Check if value succeeded, otherwise reture
        if values.error == Error.Failure.value:
            return Error.Failure

        # Read succeeded, wrap data and return
        valPtr = ctypes.cast(values.values, ctypes.POINTER(ctypes.c_uint32))

        if n == 1:
            return hex(valPtr[0])
        else:
            return [hex(valPtr[i]) for i in range(n)]

    def writeRegister(self, device, register, n, values):
        """ Set register value """

        # Check if device argument is of type Device
        if not type(device) is Device:
            print "device argument should be of type Device"
            return

        # Check if number of values mathces n
        if n == 1 and type(values) is not list:

            # Create an integer and extract it's address
            INTP = ctypes.POINTER(ctypes.c_uint32)
            num  = ctypes.c_uint32(values)
            addr = ctypes.addressof(num)
            ptr  = ctypes.cast(addr, INTP)

            return Error(self._tpm.writeRegister(self.id, device.value,
                                                 register, n, ptr))

        elif n == len(values):
            vals = (ctypes.c_uint32 * n) (*values)
            return Error(self._tpm.writeRegister(self.id, device.value,
                                                 register, n, vals))
        else:
            print "Something not quite right in writeRegister"


    def listRegisterNames(self):
        """ Print list of register names """
        
        # Check if board is connected
        if self.id is None:
            print "Board not connected"
            return

        # Check if register list has been populated
        if self._registerList is None:
            self.getRegisterList()

        print '\n'.join([str(k) for k in self._registerList.keys()])

    def __getitem__(self, key):
        """ Override __getitem__, return value from board """
        if self._registerList is not None:
            if self._registerList.has_key(key):
                reg = self._registerList[key]
                return self.readRegister(reg['device'], key, reg['size'])
            else:
                print "Register '%s' not found" % key

    def __setitem__(self, key, value):
        """ Override __setitem__, set value on board"""
        if self._registerList is not None:
            if self._registerList.has_key(key):
                reg = self._registerList[key]
                if type(value) is list:
                    return self.writeRegister(reg['device'], key, len(value), value)
                else:
                    return self.writeRegister(reg['device'], key, 1, value)
        print "Register '%s' not found" % key       

    def __len__(self):
        """ Override __len__, return number of registers """
        if self._registerList is not None:
            return len(self._registerList.keys())

    def __str__(self):
        """ Override __str__ to print register information in a human readable format """
        
        # Check if board is connected:
        if self.id is None:
            print "Board not connected"
            return
    
        # Check if register list has been populated
        if self._registerList is None:
            self.getRegisterList()

        string = ""
        for k, v in self._registerList.iteritems():
            string += '%s:\n%s\n'            % (v['name'], '-' * len(v['name']))
            string += 'Type:\t\t%s\n'        % str(v['type'])
            string += 'Device:\t\t%s\n'      % str(v['device'])
            string += 'Permission:\t%s\n'    % str(v['permission'])
            string += 'Bitmask:\t0x%X\n'     % v['bitmask']
            string += 'Size:\t\t%d\n'        % v['size']
            string += 'Description:\t%s\n\n' % v['description']

        # Return string representation
        return string


    def _initialiseLibrary(self, filepath = None):
        """ Initialise library """
       
        # Load access layer shared library
        if filepath is None:
            self._library = "/home/lessju/Code/TPM-Access-Layer/src/library/libboard.so"
        else:
            self._library = filepath

        if not os.path.isfile(self._library):
            print "Library (%s) not found" % self._library
            return 

        # Library found, load it
        self._tpm = ctypes.CDLL(self._library)

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
        self._tpm.readRegister.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p]
        self._tpm.readRegister.restype = self.ValuesStruct

        # Define writeRegister function
        self._tpm.writeRegister.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
        self._tpm.writeRegister.restype = ctypes.c_int

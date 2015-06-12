import ctypes

from enum import Enum

# --------------- Enumerations --------------------------
class BoardState(Enum):
    """ Board State enumeration """
    Unknown = 0         # Tango
    Init = 1            # Tango (was Initialising)
    On = 2              # Tango (was Ready)
    Running = 3         # Tango (was In_use)
    Fault = 4           # Tango (was Faulty)
    Off = 5             # Tango
    Standby = 6         # Tango
    Shutting_Down = 7   # ???
    Maintenance = 8     # ???
    Low_Power = 9       # ???
    Safe_State = 10     # ???
    All        = 20


class Error(Enum):
    """ Error enumeration """
    Success = 0
    Failure = -1
    NotImplemented = -2

class Device(Enum):
    """ Device enumeration """
    FPGA_1 = 1
    FPGA_2 = 2
    FPGA_3 = 4
    FPGA_4 = 8
    FPGA_5 = 16
    FPGA_6 = 32
    FPGA_7 = 64
    FPGA_8 = 128
    Board  = 65536

class BoardMake(Enum):
    """ BoardMake enumeration """
    TpmBoard      = 1
    RoachBoard    = 2
    Roach2Board   = 3
    UniboardBoard = 4

class Status(Enum):
    """ Status enumeration """
    OK = 0
    LoadingFirmware = -1
    ConfigError = -2
    BoardError = -3
    NotConnected = -4
    NetworkError = -5
    FirmwareError = -6
    LoadingFirmwareError = -7

class RegisterType(Enum):
    """ RegisterType enumeration """
    Sensor = 1
    BoardRegister = 2
    FirmwareRegister = 3
    SPIDevice = 4
    Component = 5
    FifoRegister = 6

class Permission(Enum):
    """ Permission enumeration """
    Read      = 1
    Write     = 2
    ReadWrite = 3

# --------------- Structures --------------------------
class Values(object):
    """ Class representing VALUES struct """
    def __init__(self, values, error):
        self.values = values
        self.error = error

class RegisterInfo(object):
    """ Class representing REGSTER)INFO struct """
    def __init__(self, name, address, reg_type, device, permission, bitmask, bits, value, size, desc):
        self.name = name
        self.address = address
        self.type = reg_type
        self.device = device
        self.permission = permission
        self.bitmask = bitmask
        self.bits = bits
        self.value = value
        self.size = size
        self.desc = desc

class SPIDeviceInfo(object):
    """ Class representing SPI_DEVICE_INFO struct """
    def __init__(self, name, spi_sclk, spi_en):
        self.name     = name
        self.spi_sclk = spi_sclk
        self.spi_en   = spi_en

# ------ ctype wrapper to library structures ----------
class ValuesStruct(ctypes.Structure):
    """ Class representing VALUES struct """
    _fields_ = [
        ('values', ctypes.POINTER(ctypes.c_uint32)),
        ('error', ctypes.c_int)
    ]

class RegisterInfoStruct(ctypes.Structure):
    """ Class REGISTER_INFO struct """
    _fields_ = [
        ('name',        ctypes.c_char_p),
        ('address',     ctypes.c_uint32),
        ('type',        ctypes.c_int),
        ('device',      ctypes.c_int),
        ('permission',  ctypes.c_int),
        ('bitmask',     ctypes.c_uint32),
        ('bits',        ctypes.c_uint32),
        ('value',       ctypes.c_uint32),
        ('size',        ctypes.c_uint32),
        ('description', ctypes.c_char_p)
    ]

class SPIDeviceInfoStruct(ctypes.Structure):
    """ Class representing SPI_DEVICE_INFO struct """
    _fields_ = [
        ('name',     ctypes.c_char_p),
        ('spi_sclk', ctypes.c_uint32),
        ('spi_en',   ctypes.c_uint32)
    ]

# ------------------- Exceptions -----------------------
class BoardError(Exception):
    """ Define an exception which occurs when an operation occuring
        on an FPGA boards returns an error """
    pass

class LibraryError(Exception):
    """ Define an exception which occurs when an operation occuring
        within the library returns an error """
    pass

class InstrumentError(Exception):
    """ Define an exception which occurs when an operation occuring
        within the instrument returns an error """
    pass

class PluginError(Exception):
    """ Define an exception which occurs when an operation occuring
        within a plugin returns an error """
    pass

# -------------- Device State Decorator ----------------
def validstates(*args):
    """ Add valid states meta data to function
    :param args: Valid states
    :return: Decorated function
    """

    def decorator(func):
        # Check if any states were declared
        if len(args) > 0 and all([type(x) == BoardState for x in args]):
           # Add to function metadata
           func.__dict__['_valid_states'] = args

        # All done, return
        return func

    return decorator

# ----------- Board Compatibility Decorator --------------
def compatibleboards(*args):
    """ Add board compatability to funtion
    :param args: Compatible boards
    :return: Decorated class
    """

    def decorator(func):
        # Check if any boards were declared
        if len(args) > 0 and all(type(x) == BoardMake for x in args):
            # Add board make to class metadata
            func.__dict__['_compatible_boards'] = args

        # All done, return
        return func

    return decorator

# ------------- Friendly Name Decorator ----------------
def friendlyname(*args):
    """ Add board compatability to funtion
    :param args: Compatible boards
    :return: Decorated class
    """

    def decorator(func):
        # Add friendly name to class metadata
        arg = args
        if len(args) > 0:
            arg = args[0]
        if type(arg) is str:
            func.__dict__['_friendly_name'] = args[0]
        else:
            raise PluginError("Invalid friendly name in pluging friendlyname decorator")

        # All done, return
        return func

    return decorator



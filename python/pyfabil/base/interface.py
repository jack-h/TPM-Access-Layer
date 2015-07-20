from pyfabil.base.definitions import *

# ------------- Wrap library calls ---------------------------

# Global store for interface object
library = None

def initialise_library(filepath = None):
    """ Wrap access library shared library functionality in ctypes
    :param filepath: Path to library path
    :return: None
    """
    global library

    # This only need to be done once
    if library is not None:
        return

    # Load access layer shared library
    if filepath is None:
        _library = "libaccesslayer"
    else:
        _library = filepath

    # Load library
    library = ctypes.CDLL(_library + ".so")

    # Define connect function
    library.connectBoard.argtypes = [ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint16]
    library.connectBoard.restype  = ctypes.c_uint32

    # Define disconnect function
    library.disconnectBoard.argtypes = [ctypes.c_uint32]
    library.disconnectBoard.restype  = ctypes.c_int

    # Define reset function
    library.resetBoard.argtypes = [ctypes.c_uint32, ctypes.c_int]
    library.resetBoard.restype = ctypes.c_int

    # Define getFirmware function
    library.getFirmware.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
    library.getFirmware.restype = ctypes.POINTER(ctypes.c_char_p)

    # Define loadFirmwareBlocking function
    library.loadFirmwareBlocking.argtypes =  [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p]
    library.loadFirmwareBlocking.restype = ctypes.c_int

    # Define loadFirmwareBlocking function
    library.loadFirmware.argtypes =  [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p]
    library.loadFirmware.restype = ctypes.c_int

    # Define getRegisterList function
    library.getRegisterList.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_int), ctypes.c_bool]
    library.getRegisterList.restype = ctypes.POINTER(RegisterInfoStruct)

    # Define readRegister function
    library.readRegister.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
    library.readRegister.restype = ValuesStruct

    # Define writeRegister function
    library.writeRegister.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32, ctypes.c_uint32]
    library.writeRegister.restype = ctypes.c_int

    # Define readFifoRegister function
    library.readFifoRegister.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p]
    library.readFifoRegister.restype = ValuesStruct

    # Define writeFifoRegister function
    library.writeFifoRegister.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
    library.writeFifoRegister.restype = ctypes.c_int

    # Define readRegister function
    library.readAddress.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
    library.readAddress.restype = ValuesStruct

    # Define writeRegister function
    library.writeAddress.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
    library.writeAddress.restype = ctypes.c_int

    # Define getDeviceList function
    library.getDeviceList.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
    library.getDeviceList.restype = ctypes.POINTER(SPIDeviceInfoStruct)

    # Define readDevice function
    library.readDevice.argtypes = [ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32]
    library.readDevice.restype = ValuesStruct

    # Define writeDevice function
    library.writeDevice.argtypes = [ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_uint32]
    library.writeDevice.restype = ctypes.c_int

    # Define getStatus function
    library.getStatus.argtype = [ctypes.c_uint32]
    library.getStatus.restype = Status

    # Define freeMemory function
    library.freeMemory.argtypes = [ctypes.c_void_p]

# ------------- Function wrappers to library ---------------------------

def call_connect_board(board_type, ip, port):
    """ Call connect board
    :param board_type: Board type to connect to
    :param ip: IP address of board
    :param port: port number to connect to
    :return: Integer ID representation of board
    """
    global library
    return library.connectBoard(board_type, ip, port)

def call_disconnect_board(board_id):
    """
    :param board_id: ID of board to disconnect from
    :return: Success or Failure
    """
    global library
    return Error(library.disconnectBoard(board_id))

def call_reset_board(board_id, device):
    """ Call resetBoard on bord
    :param board_id: ID of board to communicate with
    :param device: Device on board to reset
    :return: Success or Failure
    """
    global library
    return Error(library.resetBoard(board_id, device.value))

def call_get_status(board_id):
    """ Call getStatus on board
    :param board_id: ID of board to query
    :return: Status
    """
    global library
    return Status(library.getStatus(board_id))

def call_get_firmware_list(board_id, device):
    """
    :param board_id: ID of board to query
    :param device: Device on board to query
    :return: List of firmware available on board
    """
    global library

    # Create an integer and extract it's address
    INTP = ctypes.POINTER(ctypes.c_int)
    num  = ctypes.c_int(0)
    addr = ctypes.addressof(num)
    ptr  = ctypes.cast(addr, INTP)

    # Call library function
    firmware = library.getFirmware(board_id, device.value, ptr)

    # Process all firmware
    firmwareList = [firmware[i] for i in range(num.value)]

    # Free firmware pointer
    library.freeMemory(firmware)

    return firmwareList

def call_load_firmware_blocking(board_id, device, filepath):
    """ Load firmware on board in blocking mode
    :param board_id: ID of board to communicate with
    :param device: Device on board to load firmware onto
    :param filepath: Filepath or name of firmware to load
    :return: Success or Failure
    """
    global library
    return Error(library.loadFirmwareBlocking(board_id, device.value, filepath))

def call_load_firmware(board_id, device, filepath):
    """ Load firmware on board in async mode
    :param board_id: ID of board to communicate with
    :param device: Device on board to load firmware onto
    :param filepath: Filepath or name of firmware to load
    :return: Success or Failure
    """
    global library
    return Error(library.loadFirmware(board_id, device.value, filepath))

def call_get_register_list(board_id, load_values = False):
    """ Get list of available registers on board
    :param board_id: ID of board to query
    :param load_values: Load current register values when getting list
    :return: List of registers
    """
    global library

    # Create an integer and extract it's address
    INTP = ctypes.POINTER(ctypes.c_int)
    num  = ctypes.c_int(0)
    addr = ctypes.addressof(num)
    ptr  = ctypes.cast(addr, INTP)

    # Call function
    registers = library.getRegisterList(board_id, ptr, load_values)

    # Create device map for register names
    names = { Device.Board : "board", Device.FPGA_1 : "fpga1", Device.FPGA_2 : "fpga2",
              Device.FPGA_3 : "fpga3", Device.FPGA_4 : "fpga4", Device.FPGA_5 : "fpga5",
              Device.FPGA_6 : "fpga6", Device.FPGA_7 : "fpga7", Device.FPGA_8 : "fpga8"}

    # Wrap register formats and return
    registerList = { }
    for i in range(num.value):
        dev = Device(registers[i].device)
        reg = {
            'name'        : '%s.%s' % (names[dev], registers[i].name),
            'address'     : registers[i].address,
            'type'        : RegisterType(registers[i].type),
            'device'      : dev,
            'permission'  : Permission(registers[i].permission),
            'size'        : registers[i].size,
            'bitmask'     : registers[i].bitmask,
            'bits'        : registers[i].bits,
            'value'       : registers[i].value,
            'description' : registers[i].description
        }
        registerList["%s.%s" % (names[dev], registers[i].name)] = reg

    # Free up memory on board
    library.freeMemory(registers)

    return registerList

def call_get_device_list(board_id):
    """
    :param board_id: ID of board to query
    :return: List of devices
    """
    global library

    # Create an integer and extract it's address
    INTP = ctypes.POINTER(ctypes.c_uint32)
    num  = ctypes.c_uint32(0)
    addr = ctypes.addressof(num)
    ptr  = ctypes.cast(addr, INTP)

    # Call function
    devices = library.getDeviceList(board_id, ptr)

    # Wrap register formats and return
    deviceList = { }
    for i in range(num.value):
        reg = {
            'name'      : devices[i].name,
            'spi_en'    : devices[i].spi_en,
            'spi_sclk'  : devices[i].spi_sclk
        }
        deviceList[reg['name']] = reg

    # Free up memory on board
    library.freeMemory(devices)

    return deviceList

def call_read_register(board_id, device, register, n = 1, offset = 0):
    """
    :param board_id: ID of board to operate upon
    :param device: Device on board to operate upon
    :param register: Register name
    :param n: Number of words to read
    :param offset: Address offset
    :return: Memory-mapped values
    """
    global library

    # Call function and return
    return library.readRegister(board_id, device.value, register, n, offset)


def call_write_register(board_id, device, register, values, offset = 0):
    """
    :param board_id: ID of board to operate upon
    :param device: Device on board to operate upon
    :param register: Register name
    :param values: Value to write to board
    :param offset: Address offset
    :return: Success or Failure
    """
    global library

    # Check if we have a single value or list of values
    if type(values) is not list:

        # Create an integer and extract it's address
        INTP = ctypes.POINTER(ctypes.c_uint32)
        num  = ctypes.c_uint32(values)
        addr = ctypes.addressof(num)
        ptr  = ctypes.cast(addr, INTP)

        err = library.writeRegister(board_id, device.value, register, ptr, 1, offset)
        return err

    elif type(values) is list:
        n = len(values)
        vals = (ctypes.c_uint32 * n) (*values)
        return Error(library.writeRegister(board_id, device.value, register, vals, n, offset))
    else:
        return Error.Failure


def call_read_fifo_register(board_id, device, register, n = 1):
    """
    :param board_id: ID of board to operate upon
    :param device: Device on board to operate upon
    :param register: Register name
    :param n: Number of words to read
    :return: Memory-mapped values
    """
    global library

    # Call function and return
    return library.readFifoRegister(board_id, device.value, register, n)


def call_write_fifo_register(board_id, device, register, values):
    """
    :param board_id: ID of board to operate upon
    :param device: Device on board to operate upon
    :param register: Register name
    :param values: Value to write to board
    :return: Success or Failure
    """
    global library

    # Check if we have a single value or list of values
    if type(values) is not list:

        # Create an integer and extract it's address
        INTP = ctypes.POINTER(ctypes.c_uint32)
        num  = ctypes.c_uint32(values)
        addr = ctypes.addressof(num)
        ptr  = ctypes.cast(addr, INTP)

        err = library.writeFifoRegister(board_id, device.value, register, ptr, 1)
        return err

    elif type(values) is list:
        n = len(values)
        vals = (ctypes.c_uint32 * n) (*values)
        return Error(library.writeFifoRegister(board_id, device.value, register, vals, n))
    else:
        return Error.Failure

def call_read_address(board_id, device, address, n = 1):
    """ Read form address on board
    :param board_id: ID of board to operate upon
    :param device: Device on board to operate upon
    :param address: Memory address to read from
    :param n: Number of words to read
    :return: Memory-mapped values
    """
    global library

    # Call function
    values = library.readAddress(board_id, device.value, address, n)

    # Check if value succeeded, othewise rerturn
    if values.error == Error.Failure.value:
        return Error.Failure

    # Read successful, wrap data and return
    valPtr = ctypes.cast(values.values, ctypes.POINTER(ctypes.c_uint32))

    if n == 1:
        return valPtr[0]
    else:
        return [valPtr[i] for i in range(n)]


def call_write_address(board_id, device, address, values):
    """ Write to address on board
    :param board_id: ID of board to operate upon
    :param device: Device on board to operate upon
    :param address: Memory address to write to
    :param values: Values to write to memory
    :return: Success or Failure
    """
    global library

    # Check if we have a single value or list of values
    if type(values) is not list:

        # Create an integer and extract it's address
        INTP = ctypes.POINTER(ctypes.c_uint32)
        num  = ctypes.c_uint32(values)
        addr = ctypes.addressof(num)
        ptr  = ctypes.cast(addr, INTP)

        return Error(library.writeAddress(board_id, device.value, address, ptr, 1))

    elif type(values) is list:
        n = len(values)
        vals = (ctypes.c_uint32 * n) (*values)
        return Error(library.writeAddress(board_id, device.value, address, vals, n))
    else:
        return Error.Failure

def call_read_device(board_id, device, address):
    """ Read from an SPI device
    :param board_id: ID of board to operate upon
    :param device: Device on board to operate upon
    :param address: Address on device to read from
    :return: Values
    """
    global library

    # Call function
    values = library.readDevice(board_id, device, address)

    # Check if value succeeded, otherwise reture
    if values.error == Error.Failure.value:
        return Error.Failure

    # Read succeeded, wrap data and return
    valPtr = ctypes.cast(values.values, ctypes.POINTER(ctypes.c_uint32))

    # Return value
    return valPtr[0]

def call_write_device(board_id, device, address, value):
    """
    :param board_id: ID of board to operate upon
    :param device: Device on board to operate upon
    :param address: Address on device to write to
    :param value: Value to write
    :return: Success of Failurent hawn
    """
    global library

    # Call function
    return Error(library.writeDevice(board_id, device, address, value))

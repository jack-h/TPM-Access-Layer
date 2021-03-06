# noinspection PyUnresolvedReferences
from pyfabil.plugins import *
from pyfabil.base.interface import *
import inspect
import logging
import sys
import re

# --------------- Helpers ------------------------------
from pyfabil.plugins.firmwareblock import FirmwareBlock

DeviceNames = { Device.Board  : "Board", Device.FPGA_1 : "FPGA 1", Device.FPGA_2 : "FPGA 2",
                Device.FPGA_3 : "FPGA 3", Device.FPGA_4 : "FPGA 4", Device.FPGA_5 : "FPGA 5",
                Device.FPGA_6 : "FPGA 6", Device.FPGA_7 : "FPGA 7", Device.FPGA_8 : "FPGA 8"}
# ------------------------------------------------------

# Wrap functionality for a TPM board
class FPGABoard(object):
    """ Class which wraps LMC functionality for generic FPGA boards """

    # Class constructor
    def __init__(self, **kwargs):
        """ Class constructor for FPGABoard"""

        # Set defaults
        self.status        = {Device.Board : Status.NotConnected}
        self._programmed   = {Device.Board : False, Device.FPGA_1 : False, Device.FPGA_2 : False}
        self.register_list = None
        self._firmwareList = None
        self._fpga_board   = 0
        self._deviceList   = None
        self.id            = None
        self._logger       = None
        self._string_id    = "Board"

        # Override to make this compatible with IPython
        self.__methods__        = None
        self.trait_names        = None
        self._getAttributeNames = None
        self.__members__        = None

        # Initialise list of available and loaded plugins
        self._available_plugins = {}
        self._loaded_plugins = { }

        # Used by __setattr__ to know how to handle new attributes
        self.__initialised = True  

        # Check if FPGA board type is specified
        self._fpga_board = kwargs.get('fpgaBoard', None)
        if self._fpga_board is None:
            raise LibraryError("No BoarMake specified in FPGABoard initialiser")

        # Get list of available plugins which are compatible with board instance
        # noinspection PyUnresolvedReferences
        for plugin in [cls.__name__ for cls in sys.modules['pyfabil.plugins'].FirmwareBlock.__subclasses__()]:
            constr = eval(plugin).__init__.__dict__
            friendly_name = plugin
            if "_friendly_name" in constr:
                friendly_name = constr['_friendly_name']
            if "_compatible_boards" in constr and self._fpga_board in constr['_compatible_boards']:
                self._available_plugins[plugin] = friendly_name
            elif "_comaptible_boards" in constr:
                self._available_plugins[plugin] = friendly_name

        # Check if filepath is included in arguments
        filepath = kwargs.get('library', None)

        # Initialise library
        initialise_library(filepath)

        # Initialise logging (use default logger which can be set externally)
        self._logger = logging.getLogger('dummy')
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        formatter = logging.Formatter('%(levelname)s\t%(asctime)s\t %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        ch.setFormatter(formatter)
        self._logger.addHandler(ch)

        # Check if ip and port are defined in arguments
        ip   = kwargs.get('ip', None)
        port = kwargs.get('port', None)

        # If so, the connect immediately
        if ip is not None and port is not None:
            self.connect(ip, port)

    # ----------------------------- High-level functionality -------------------------

    def initialise(self, config):
        """ Method for explicit initialisation. This is called by instrument when
            a configuration file is provided
        :param config: Configuration dictionary
        """

        self._string_id = config['id']

        # Configure logging
        if 'log' in config and eval(config['log']):
            self._logger = logging.getLogger()  # Get default logger
        else:
            self._logger = logging.getLogger('dummy')

        # Check if board is already connected, and if not, connect
        if self.id is None:
            if 'ip' not in config and 'port' not in config:
                raise LibraryError("IP and port are required for initialisation")
            self.connect(config['ip'], int(config['port']))

        # Check if firmware was defined in config
        if 'firmware' not in config:
            raise BoardError("Firmware must be specified in configuration file")

        #TODO: Make this generic to any board
        self.load_firmware(Device.FPGA_1, config['firmware'])

        #TODO: Perform board-specific intialisation , if any
        # Load plugins if not already loaded
        if len(self._loaded_plugins) == 0:
            # Check if any plugins are required
            if 'plugins' in config:
                for k, v in config['plugins'].iteritems():
                    # Load and initialise plugins
                    self.load_plugin(k)
                    getattr(self, self._available_plugins[k]).initialise(**v)

    def status_check(self):
        """ Perform board and firmware status checks
        :return: Status
        """

        # Run generic board tests
        status = self.get_status()
        if status is not Status.OK:
            return status

        # Loop over all plugins and perform checks
        if not all([getattr(self, plugin).status_check() == Status.OK
                    for plugin in self._loaded_plugins  ]):
            return Status.FirmwareError

        # All check succesful, return
        return Status.OK

    # -------------------------- Firmware plugin functionality -----------------------
    def load_plugin(self, plugin, **kwargs):
        """ Loads a firmware block plugin and incorporates its functionality
        :param plugin: Plugin class name
        """

        # Check if module is available
        if plugin not in self._available_plugins.keys():
            raise LibraryError("Module %s is not available" % plugin)

        # Check if plugin is compatible with board make
        constr = eval(plugin).__init__.__dict__
        if "_compatible_boards" in constr:
            if self._fpga_board not in constr['_compatible_boards']:
                raise LibraryError("Plugin %s is not compatible with %s" % (plugin, self._fpga_board))
        else:
            self._logger.warn(self.log("Plugin %s does not specify board compatability" % plugin))

        # Check if friendly name was defined for this plugin
        friendly_name = plugin
        if "_friendly_name" not in constr:
            self._logger.warn(self.log("Plugin %s does not specify a friendly name" % plugin))
        else:
            friendly_name = constr['_friendly_name']

        # Check if number of plugin instances has been exceeded
        max_instances = 1
        if "_max_instances" not in constr:
            self._logger.warn(self.log("Plugin %s does not specify maximum number of instances" % plugin))
        else:
            max_instances = constr['_max_instances']

        # Count number of instances already loaded
        # 0 means an unlimited number can be loaded
        if max_instances > 0:
            if friendly_name in self.__dict__.keys() and len(self.__dict__[friendly_name]) > max_instances:
                raise LibraryError("Cannot load more instances on plugin %s" % plugin)

        # Check if a design name is specified in plugin decorator
        if "_design" in constr:
            # A design has been specified, check if it is available on the board
            available_firmware = self.get_firmware_list()
            # Check if firmware is available
            if len(available_firmware) == 0:
                raise LibraryError("No firmware available on board")
            if type(available_firmware[0]) is str and constr['_design'] not in available_firmware:
                raise LibraryError("Cannot load plugin %s because firmware %s is not available"
                                   % (plugin, constr['_design']))
            elif type(available_firmware[0]) is dict:
                if constr['_design'] not in [x['design'] for x in available_firmware]:
                    raise LibraryError("Cannot load plugin %s because firmware %s is not available"
                                       % (plugin, constr['_design']))

            # Loop over all designs with compatible designs
            compatible_design = None
            for i, design in enumerate([x for x in available_firmware if x['design'] == constr['_design']]):
                # Loop over major and minor version numbers
                match = True
                for ver, dver in [('_major', 'major'), ('_minor', 'minor')]:
                    # Check if version information is specified
                    if ver in constr and dver in design.keys():
                        # If major version type is integer, a direct match is required
                        if type(constr[ver]) is int and design[dver] != constr[ver]:
                            match = False
                        # If major version is a string, then a range of version can be defined
                        elif type(constr[ver]) is str:
                            if re.match("[<>=]+\d+", constr[ver]):
                                if not eval(str(design[dver]) + constr[ver]):
                                    match = False
                            elif re.match("\d+", constr[ver]):
                                if int(constr[ver]) != design[dver]:
                                    match = False
                            else:
                                raise LibraryError("Invalid plugin %s %s specification (%s)" % (plugin, dver, constr[ver]))
                        else:
                            raise LibraryError("Invalid plugin %s %s specification (%s)" % (plugin, dver, str(constr[ver])))

                # If match is true, then the current design is compatible with plugin requirements
                if match:
                    compatible_design = design
                    break

            # Check if a compatible design was found
            if compatible_design is not None:
                if 'device' not in kwargs.keys():
                    raise LibraryError("Plugin %s with firmware association required a device argument" % plugin)

                # Load firmware on board, which will check if firmware is already loaded
                # TODO: How to specify firmware when multiple firmware can have the same design name?
                # try:
                #     self.load_firmware(kwargs['device'], compatible_design['design'])
                # except:
                #     raise LibraryError("Failed to load firmware for plugin %s" % plugin)
            else:
                # If no compatible design is found, raise error
                raise LibraryError("No compatible firmware design %s for plugin %s available on board" %
                       (constr['_design'], plugin))

        # Get list of class methods and remove those available in superclass
        methods = [name for name, mtype in
                   inspect.getmembers(eval(plugin), predicate=inspect.ismethod)
                   if name not in
                   [a for a, b in inspect.getmembers(FirmwareBlock, predicate=inspect.ismethod)]
                   and not name.startswith('_')]

        # Create plugin instances, passing arguments if provided
        if len(kwargs) == 0:
            instance = globals()[plugin](self)
        else:
            instance = globals()[plugin](self, **kwargs)

        if friendly_name in self.__dict__.keys():
            # Plugin already loaded once, add to list
            self.__dict__[friendly_name].append(instance)
        else:
            # Plugin not loaded yet
            self.__dict__[friendly_name] = PluginList((instance,))

            # Plugin loaded, add to list
            self._loaded_plugins[friendly_name] = []

            # Some bookeeping
            for method in methods:
                self._logger.debug(self.log("Detected method %s from plugin %s" % (method, plugin)))
                self._loaded_plugins[friendly_name].append(method)

        self._logger.info(self.log("Added plugin %s to class instance" % plugin))

        return self.__dict__[friendly_name][-1]

    def unload_plugin(self, plugin, instance = None):
        """ Unload plugin from instance
        :param plugin: Plugin name
        """
        # Check if plugin has been loaded
        if plugin in self._loaded_plugins.keys():
            # If no instance is specified, remove all plugin instances
            if instance is None:
                del self.__dict__[plugin]
            elif type(instance) is int and len(getattr(self, plugin)) >= instance:
                getattr(self, plugin).remove(getattr(self, plugin)[instance])
            else:
                self._logger.info(self.log("Plugin %s instance %d does not exist" % (plugin, instance)))
        else:
            self._logger.info(self.log("Plugin %s was not loaded." % plugin))

    def unload_all_plugins(self):
        """ Unload all plugins from instance """
        for plugin in self._loaded_plugins.keys():
            del self.__dict__[plugin]
        self._loaded_plugins = { }

    def get_available_plugins(self):
        """ Get list of availabe plugins
        :return: List of plugins
        """
        return self._available_plugins

    def get_loaded_plugins(self):
        """ Get the list of loaded plugins with associated methods
        :return: List of loaded plugins
        """
        return self._loaded_plugins

    # ---------------------------- FPBA Board functionality --------------------------

    def connect(self, ip, port):
        """ Connect to board
        :param ip: Board IP
        :param port: Port to connect to
        """

        # Check if IP is valid, and if a hostname is provided, check whether it
        # exists and get IP address
        import socket
        try:
            socket.inet_aton(ip)
        except socket.error:
            try:
                ip = socket.gethostbyname(ip)
            except socket.gaierror:
                raise BoardError("Provided IP address (%s) is invalid or does not exist")

        # Connect to board
        board_id = call_connect_board(self._fpga_board.value, ip, port)
        if board_id == 0:
            self.status[Device.Board] = Status.NetworkError
            raise BoardError("Could not connect to board with ip %s" % ip)
        else:
            self._logger.info(self.log("Connected to board %s, received ID %d" % (ip, board_id)))
            self.id = board_id
            self.status[Device.Board] = Status.OK

    def disconnect(self):
        """ Disconnect from board """

        # Check if board is connected
        if self.id is None:
            self._logger.warn(self.log("Call disconnect on board which was not connected"))

        ret = call_disconnect_board(self.id)
        if ret == Error.Success:
            self.register_list = None
            self.unload_all_plugins()
            self._logger.info(self.log("Disconnected from board with ID %s" % self.id))
            self.id = None

    def reset(self, device):
        """ Reset device on board
        :param device: Device on board to reset
        """
        return call_reset_board(self.id, device)

    def get_status(self):
        """ Get board status
        :return: Status
        """
        return call_get_status(self.id)

    def get_firmware_list(self, device = Device.Board):
        """ Get list of firmware on board
        :param device: Device on board to get list of firmware
        :return: List of firmware
        """

        # Check if board is connected
        if self.id is None:
            raise LibraryError("Call get_firmware_list for board which is not connected")

        # Call getFirmware on board
        self._firmwareList = call_get_firmware_list(self.id, device)
        self._logger.debug(self.log("Called get_firmware_list"))

        return self._firmwareList

    def load_firmware(self, device, filepath = None, load_values = False, base_address = 0):
        """ Blocking call to load firmware
         :param device: Device on board to load firmware to
         :param filepath: Path to firmware
         :param load_values: Load register values
         """

        # Check if connected
        if self.id is None:
            raise LibraryError("Not connected to board, cannot load firmware")

        # Superclass method required filepath to be not null
        if filepath is None:
            raise LibraryError("Default load_firmware requires a filepath")

        # Check if device argument is of type Device
        if not type(device) is Device:
            raise LibraryError("Device argument for load_firmware should be of type Device")

        # All OK, call function
        self.status[device] = Status.LoadingFirmware
        err = call_load_firmware(self.id, device, filepath, base_address)
        self._logger.debug(self.log("Called load_firmware"))

        # If call succeeded, get register and device list
        if err == Error.Success:
            self._programmed[device] = True
            self.status[device] = Status.OK
            self.get_register_list(load_values = load_values, reset = True)
            self.get_device_list()
            self._logger.info(self.log("Successfully loaded firmware %s on board" % filepath))
        else:
            self._programmed[device] = False
            self.status[device]      = Status.LoadingFirmwareError
            raise BoardError("load_firmware failed on board")

    def download_firmware(self, device, bitfile):
        """ Download firmware onto the FPGA (or FLASH)
        :param device: Device to download firmware to
        """
        raise LibraryError("Download firmware not implemented")

    def get_register_list(self, reset = False, load_values = False):
        """ Get list of registers
        :param load_values: Load register values
        """

        # Check if register list has already been acquired, and if so return it
        if self.register_list is not None and not reset:
            return self.register_list

        # Check if device is programmed
        # TODO: Make this compatible with UniBoard
        if not self._programmed[Device.Board]:
           raise LibraryError("Cannot get_register_list from board which has not been programmed")

        # Call function
        self.register_list = call_get_register_list(self.id, load_values)
        self._logger.debug(self.log("Called get_register_list on board"))

        # All done, return
        return self.register_list

    def get_device_list(self, reset = False):
        """ Get list of SPI devices """

        # Check if register list has already been acquired, and if so return it
        if self._deviceList is not None and not reset:
            return self._deviceList

        # Call function
        self._deviceList = call_get_device_list(self.id)
        self._logger.debug(self.log("Called get_device_list"))

        # All done, return
        return self._deviceList

    def read_register(self, register, n = 1, offset = 0, device = None):
        """" Get register value
         :param register: Register name
         :param n: Number of words to read
         :param offset: Memory address offset to read from
         :param device: Device/node can be explicitly specified
         :return: Values
         """

        # Perform basic checks
        if not self._checks(device):
            return

        # Extract device from register name
        if device is None:
            device = self._get_device(register)
        else:
            if type(device) is not Device:
                LibraryError("Parameter device must be of type Device")

        # Check if device argument is of type Device
        if not type(device) is Device:
            raise LibraryError("Device argument for read_register should be of type Device")

        # Call function
        if self.register_list[register]['type'] == RegisterType.FifoRegister:
            values = call_read_fifo_register(self.id, device, self._remove_device(register), n)
        else:
            values = call_read_register(self.id, device, self._remove_device(register), n, offset)

        self._logger.debug(self.log("Called read_register"))

        # Check if value succeeded, otherwise return
        if values.error == Error.Failure.value:
            raise BoardError("Failed to read_register %s from board" % register)

        # Read succeeded, wrap data and return
        valptr = ctypes.cast(values.values, ctypes.POINTER(ctypes.c_uint32))

        self._logger.debug(self.log("Called read_register on board"))

        if n == 1:
            return valptr[0]
        else:
            return [valptr[i] for i in range(n)]

    def write_register(self, register, values, offset = 0, device = None):
        """ Set register value
         :param register: Register name
         :param values: Values to write
         :param offset: Memory address offset to write to
         :param device: Device/node can be explicitly specified
         """

        # Perform basic checks
        if not self._checks(device):
            return

        # Extract device from register name
        if device is None:
            device = self._get_device(register)
        else:
            if type(device) is not Device:
                LibraryError("Parameter device must be of type Device")

        # Call function and return
        if self.register_list[register]['type'] == RegisterType.FifoRegister:
            err = call_write_fifo_register(self.id, device, self._remove_device(register), values)
        else:
            err = call_write_register(self.id, device, self._remove_device(register), values, offset)

        self._logger.debug(self.log("Called write_register"))
        if err == Error.Failure:
            raise BoardError("Failed to write_register %s on board" % register)

    def read_address(self, address, n = 1):
        """" Get register value
         :param address: Memory address to read from
         :param n: Number of words to read
         :return: Values
         """

        # Call function and return
        ret = call_read_address(self.id, Device.FPGA_1, address, n)
        self._logger.debug(self.log("Called read_address"))
        if ret == Error.Failure:
            raise BoardError("Failed to read_address %s on board" % hex(address))
        else:
            return ret

    def write_address(self, address, values):
        """ Set register value
         :param address: Memory address to write to
         :param values: Values to write
         """

        # Call function and return
        err = call_write_address(self.id, Device.FPGA_1, address, values)
        self._logger.debug(self.log("Called write_address"))
        if err == Error.Failure:
            raise BoardError("Failed to write_address %s on board" % hex(address))

    def read_device(self, device, address):
        """" Get device value
         :param device: SPI Device to read from
         :param address: Address on device to read from
         :return: Value
         """
    
        # Check if device is in device list
        if device not in self._deviceList:
            raise LibraryError("Device argument for read_device should be of type Device")

        # Call function and return
        ret = call_read_device(self.id, device, address)
        self._logger.debug(self.log("Called read_device"))
        if ret == Error.Failure:
            raise BoardError("Failed to read_device %s, %s on board" % (device, hex(address)))
        else:
            return ret

    def write_device(self, device, address, value):
        """ Set device value
        :param device: SPI device to write to
        :param address: Address on device to write to
        :param value: Value to write
        """

        # Check if device is in device list
        if device not in self._deviceList:
            raise LibraryError("Device argument for write_device should be of type Device")

        # Call function and return
        ret = call_write_device(self.id, device, address, value)
        self._logger.debug(self.log("Called write_device"))
        if ret == Error.Failure:
            raise BoardError("Failed to write_device %s, %s on board" % (device, hex(address)))

    def load_spi_devices(self, device, filepath):
        """ Load SPI devices
        :param device: Device
        :param filepath: Path to SPI XML file
        :return:
        """
        return call_load_spi_devices(self.id, device, filepath)

    def list_register_names(self):
        """ Print list of register names """

        if not self._programmed[Device.Board]:
            return

        # Run checks
        if not self._checks():
            return

        # Split register list into devices
        registers = { }
        for k, v in self.register_list.iteritems():
            if v['device'] not in registers.keys():
                registers[v['device']] = []
            registers[v['device']].append(k)

        # Loop over all devices
        for k, v in registers.iteritems():
            print DeviceNames[k]
            print '-' * len(DeviceNames[k])
            for regname in sorted(v):
                print '\t' + str(regname)

    def list_device_names(self):
        """ Print list of SPI device names """
        
        # Run check
        if not self._checks():
            return

        # Loop over all SPI devices
        print "List of SPI Devices"
        print "-------------------"
        for k in self._deviceList:
            print k

    def find_register(self, string, display = False):
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
        for k, v in self.register_list.iteritems():
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
        # return matches

    def find_device(self, string, display = False):
        """ Return SPI device information for provided search string
         :param string: Regular expression to search against
         :param display: True to output result to console
         :return: List of found devices
         """

        # Run check
        if not self._checks():
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
        # return matches

    def __len__(self):
        """ Override __len__, return number of registers """
        if self.register_list is not None:
            return len(self.register_list.keys())

    def _checks(self, device = Device.Board):
        """ Check prior to function calls """

        # Check if board is connected
        if self.id is None:
            raise LibraryError("Cannot perform operation on unconnected board")

        # Check if device is programmed
        # TODO: Make compatbile with UniBoard
        if device is not None and not self._programmed[device]:
           raise LibraryError("Cannot getRegisterList from board which has not been programmed")

        # Check if register list has been populated
        if self.register_list is None:
            self.get_register_list()

        return True

    def log(self, string):
        """ Format string for logging output
        :param string: String to log
        :return: Formatted string
        """
        return "%s (%s)" % (string, self._string_id)

    @staticmethod
    def _get_device(name):
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
        except KeyError:
            return None
            
    @staticmethod
    def _remove_device(name):
        """ Extract device name from register
            :param name: Register name
            :return: Register name without device
        """

        try:
            device = name.split('.')[0].upper()
            if device in ["BOARD", "FPGA1", "FPGA2"]:
                return '.'.join(name.split('.')[1:])
            else:
                return name
        except KeyError:
            return name

# -------------- Logging Functionality --------------------

# Note: Do not run the code below! (temp)
if __name__ == "__main__":
    from pyfabil.boards.tpm import TPM
    tpm = TPM()
    # Simple TPM tests
    # tpm = TPM(ip="127.0.0.1", port=10000)
    # tpm.loadFirmware(Device.FPGA_1, "/home/lessju/map.xml")
    # tpm['fpga1.regfile.block2048b'] = [1] * 512
    # print tpm['fpga1.regfile.block2048b']
    # tpm.disconnect()
    #
    # # Simple ROACH tests
    # roach = Roach(ip="192.168.100.2", port=7147)
    # roach.getFirmwareList()
    # roach.loadFirmware("fenggbe.bof")
    # roach.amp_EQ0_coeff_bram = range(4096)
    # print roach.readRegister('amp_EQ0_coeff_bram', 4096)
    # roach.disconnect()

    pass

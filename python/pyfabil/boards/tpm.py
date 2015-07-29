from pyfabil.boards.fpgaboard import FPGABoard, DeviceNames
from pyfabil.base.definitions import *
from math import ceil
import binascii
import zlib


class TPM(FPGABoard):
    """ FPGABoard subclass for communicating with a TPM board """

    def __init__(self, **kwargs):
        """ Class constructor """
        kwargs['fpgaBoard'] = BoardMake.TpmBoard
        super(TPM, self).__init__(**kwargs)

        # Set hardcoded cpld xml offset address
        self._cpld_xml_offset         = 0x80000004

        # Check if we are simulating or not
        self._simulator = kwargs.get('simulator', False)

        # Placeholder for initialised check
        self._devices_initialised = False
        self._board_initialised    = False

        # Pre-load all required plugins
        self.load_plugin("TpmFirmwareInformation", device=Device.FPGA_1)
        self.load_plugin("TpmFirmwareInformation", device=Device.FPGA_2)
        self.load_plugin("TpmPll", board_type="NOTXTPM")
        [self.load_plugin("TpmAdc", adc_id = adc) for adc in ["adc0", "adc1"]]
        self.load_plugin("TpmJesd", fpga_id = 0, core_id = 0)
        self.load_plugin('TpmFpga', board_type = 'NOTXTPM', device = Device.FPGA_1)

        # Load CPLD XML file from the board if not simulating
        if not self._simulator:
            self._initialise_board()

    def _initialise_board(self):
        """ Initialise the TPM board """

        # Get XML file
        cpld_xml =  self._get_xml_file(self.read_address(self._cpld_xml_offset))

        # Process XML file
        filepath = "/tmp/xml_file.xml"
        with open(filepath, "w") as f:
            # Add necessary XML and write to temporary file
            cpld_xml = "%s%s%s" % ('<node>\n', cpld_xml, "</node>")
            f.write(cpld_xml)
            f.flush()

            # Initialise memory map
            try:
                super(TPM, self).load_firmware(device = Device.Board, filepath = filepath)
            except:
                raise LibraryError("Failed to load CPLD XML file from TPM")

        # Load SPI file, if exists
        if self.register_list.has_key('board.info.spi_xml_offset'):
            # Get SPI XML file
            spi_xml = self._get_xml_file(self.read_register("board.info.spi_xml_offset"))

            # Write to file
            spi_filepath = '/tmp/spi.xml'
            with open(spi_filepath, 'w') as sf:
                sf.write(spi_xml)
                sf.flush()

                # Load XML devices on board
                if self.load_spi_devices(Device.Board, spi_filepath) == Error.Failure:
                    raise LibraryError("Failed to process SPI XML file")

                # Update device list
                self.get_device_list(reset = True)

        # CPLD and SPI XML files have been loaded, check whether FPGA have been programmed
        # If FPGA is programmed, load the firmware's XML file
        self.tpm_firmware_information[0].update_information()
        if self.tpm_firmware_information[0].get_design != "":
            self.load_firmware(device = Device.FPGA_1)

        # self.tpm_firmware_information[1].update_information()
        # if self.tpm_firmware_information[1].get_design != "":
        #     self.load_firmware(device = Device.FPGA_2)

        # Set board as initialised
        self._board_initialised = True

    def _initialise_devices(self, frequency = 700):
        """ Initialise the SPI and other devices on the board """

        # Initialise PLL
        self.tpm_pll.pll_start(frequency)

        # Initialise ADCs
        [self.tpm_adc[i].adc_single_start() for i in range(2)]

        # Initialise JESD core
        self.tpm_jesd.jesd_core_start()

        # Initialise FPGAs
        self.tpm_fpga.fpga_start(range(4), range(4))

        # Set devices as initialised
        self._devices_initialised = True

    def load_firmware(self, device, filepath = None, load_values = False):
        """ Override superclass load_firmware to extract memory map from the bitfile
            This is saved in a tmp directory and forwarded to the superclass for
            processing
            :param device: The device on which the firmware will be loaded
            :param filepath: Filepath of the firmware, None if already loaded
            :param load_values:
            """

        # Check if device is valid
        if device not in [Device.FPGA_1, Device.FPGA_2]:
            raise LibraryError("TPM devices can only be FPGA_1 and FPGA_2")

        # If a filepath is not provided, then this means that we're loading from the board itself
        if not filepath:

            # Check if connected
            if self.id is None:
                raise LibraryError("Not connected to board, cannot load firmware")

            # Check if register exists in map
            register = 'board.info.%s_xml_offset' % ("fpga1" if device == Device.FPGA_1 else "fpga2")
            if not self.register_list.has_key(register):
                raise LibraryError("CPLD XML file must be loaded prior to loading firmware")

            # Get XML file offset and read XML file from board
            zipped_xml = self._get_xml_file(self[register])

            # Process
            filepath = "/tmp/xml_file.xml"
            with open(filepath, "w") as f:
                # Add necessary XML and write to file
                f.write("%s%s%s" % ('<node>\n', zipped_xml.replace('id="tpm_test"', 'id="fpga1"'), "</node>"))
                f.flush()

                # Call superclass with this file
                super(TPM, self).load_firmware(device = device, filepath = filepath)
        else:
            super(TPM, self).load_firmware(device = device, filepath = filepath)

        # If devices were not initialised, initialise them now
        self._initialise_devices()

        # Update firmware information
        self.tpm_firmware_information[0 if device == Device.FPGA_1 else 1].update_information()

    def _get_xml_file(self, xml_offset):
        """ Get XML file from board
        :param xml_offset: Memory offset where XML file is stored
        :return: XML file as string
        """
        # Read length of XML file (first 4 bytes from offset)
        xml_len = self.read_address(xml_offset)

        # Read XML file from board
        zipped_xml = self.read_address(xml_offset + 4, int(ceil(xml_len / 4.0)))

        # Convert to string, decompress and return
        zipped_xml = ''.join([format(n, '08x') for n in zipped_xml])
        return  zlib.decompress(binascii.unhexlify(zipped_xml[: 2 * xml_len]))

    ####################### Methods for syntax candy ###########################

    def __getitem__(self, key):
        """ Override __getitem__, return value from board """

        # Run checks
        if not self._checks():
            return

        # Check if the specified key is a memory address or register name
        if type(key) in [int, long]:
            return self.read_address(key)

        # Check if the specified key is a tuple, in which case we are reading from a device
        if type(key) is tuple:
            if len(key) == 2:
                return self.read_device(key[0], key[1])
            else:
                raise LibraryError("A device name and address need to be specified for writing to SPI devices")

        elif type(key) is str:
            # Check if a device is specified in the register name
            if self.register_list.has_key(key):
                reg = self.register_list[key]
                return self.read_register(key, reg['size'])
        else:
            raise LibraryError("Unrecognised key type, must be register name, memory address or SPI device tuple")

        # Register not found
        raise LibraryError("Register %s not found" % key)

    def __setitem__(self, key, value):
        """ Override __setitem__, set value on board"""

        # Run checks
        if not self._checks():
            return

        # Check is the specified key is a memory address or register name
        if type(key) in [int, long]:
            return self.write_address(key, value)

        # Check if the specified key is a tuple, in which case we are writing to a device
        if type(key) is tuple:
            if len(key) == 2:
                return self.write_device(key[0], key[1], value)
            else:
                raise LibraryError("A device name and address need to be specified for writing to SPI devices")

        elif type(key) is str:      
            # Check if device is specified in the register name
            if self.register_list.has_key(key):
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
        for k, v in self.register_list.iteritems():
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

if __name__ == "__main__":
    tpm = TPM(simulator=True)
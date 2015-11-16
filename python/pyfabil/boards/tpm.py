import os
from time import sleep
import math
from pyfabil.base.utils import swap32
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

        # Check if we are simulating or not
        self._simulator = kwargs.get('simulator', False)

        # Set hardcoded cpld xml offset address
        self._cpld_xml_offset         = 0x80000004

        # Call superclass initialiser
        super(TPM, self).__init__(**kwargs)

    def connect(self, ip, port):
        """ Overload connect method
        :param ip: IP address to connect to
        :param port: Port to connect to
        """

        # Call connect on super class
        super(TPM, self).connect(ip, port)

        # Load CPLD XML file from the board if not simulating
        if (not self._simulator) and self.id is not None:
            # Pre-load all required plugins. Board-level devices are loaded here
            [self.load_plugin("TpmFirmwareInformation", firmware=x) for x in range(1,4)]

            # Load ADCs
            [self.load_plugin("TpmAdc", adc_id = adc) for adc in
                ["adc0", "adc1", "adc2", "adc3", "adc4", "adc5", "adc6", "adc7",
                 "adc8", "adc9", "adc10", "adc11", "adc12", "adc13", "adc14", "adc15"]]

            # Load PLL
            self.load_plugin("TpmPll")
            self._initialise_board()
        else:
            print "Running in simulation mode"

    def get_firmware_list(self, device = Device.Board):
        """ Get list of downloaded firmware on TPM FLASH
        :param device: This should always be the board for the TPM
        :return: List of design name as well as version
        """

        # Got through all firmware information plugins and extract information
        firmware = []
        for plugin in self.tpm_firmware_information:
            # Update information
            plugin.update_information()

            # Check if design is valid:
            if plugin.get_design() is not None:
                firmware.append({'design' : plugin.get_design(),
                                 'major'  : plugin.get_major_version(),
                                 'minor'  : plugin.get_minor_version() })
        # All done, return
        return firmware

    def download_firmware(self, device, bitfile):
        """ Download bitfile to FPGA
        :param device: FPGA to download bitfile
        :param bifile: Bitfile to download
        """

        # Temporary
        xil_registers    = [0x50000004, 0x50000008]
        global_register = 0x50000000
        fifo_register   = 0x50001000

        # Check if FPGA is programmed (if not no need to erase)
        for xil_register in xil_registers:
            if self[xil_register] & 0x1 != 0:
                self[xil_register] = 0x10  # Select FPGA
                self[global_register] = 0x1  # PROG = 0
                while self[xil_register] & 0x1 == 1:
                    sleep(0.1)
                self[global_register] = 0x3
                while self[xil_register] & 0x1 == 0:
                    sleep(0.1)
                self[xil_register] = 0x0

        # Read bistream
        with open(bitfile, "rb") as fp:
            data  = fp.read()

        for xil_register in xil_registers:
            self[xil_register] = 0x10
        self[global_register] = 0x2

        # Group bytes into word and correct endiannes of bitfile content
        formatted_data = [(ord(d) << 24 | ord(c) << 16 | ord(b) << 8 | ord(a))  for (a, b, c, d) in zip(*[iter(data)]*4)]

        # Write bitfile to FPGA
        packet_size = 256
        num = int(math.floor(len(formatted_data) / float(packet_size)))
        for i in range(num):
            self[fifo_register] = formatted_data[i * packet_size : i * packet_size + packet_size]
        self[fifo_register] = formatted_data[num * packet_size:]

        # Wait for operation to complete
        for xil_register in xil_registers:
            while self[xil_register] & 0x10 == 0:
                sleep(0.1)

        self[global_register] = 0x3
        for xil_register in xil_registers:
            self[xil_register] = 0x0


    def load_firmware(self, device, filepath = None, load_values = False):
        """ Override uperclass load_firmware to extract memory map from the bitfile
            This is saved in a tmp directory and forwarded to the superclass for
            processing
            :param device: The device on which the firmware will be loaded
            :param filepath: Filepath of the firmware, None if already loaded
            :param load_values: Register values are loaded
            """

        # Check if device is valid
        if device not in [Device.Board, Device.FPGA_1, Device.FPGA_2]:
            raise LibraryError("TPM devices can only be Board, FPGA_1 and FPGA_2")

        # If a filepath is not provided, then this means that we're loading from the board itself
        if not filepath:

            # Check if connected
            if self.id is None:
                raise LibraryError("Not connected to board, cannot load firmware")

            # Get FPGA base address and check if firmwared is loaded in FPGA
            base_address = self['board.info.fpga1_base_add']   if device == Device.FPGA_1 \
                                                               else self['board.info.fpga2_base_add']
            loaded = self['board.regfile.fpga1_programmed_fw'] if device == Device.FPGA_1 \
                                                               else self['board.regfile.fpga2_programmed_fw']

            register = 'board.info.fw%d_xml_offset' % loaded
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
                super(TPM, self).load_firmware(device = device, filepath = filepath, base_address = base_address)
        else:
            # Check if file exists
            if not os.path.exists(filepath):
                raise LibraryError("Cannot load firmware with file %s, does not exist" % filepath)

            # If file is an XML file, call superclass method directly, otherwise assume that it's a
            # bistream and load bitstream to FPGA first
            if not filepath.endswidth(".xml"):

                # Check that we're trying to program an FPGA not the CPLD
                if device not in [Device.Board, Device.FPGA_1, Device.FPGA_2]:
                    raise LibraryError("Can only program TPM devices FPGA_1 and FPGA_2")

            # Call load firmware method on super class
            super(TPM, self).load_firmware(device = device, filepath = filepath)

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

        # Update firmware information
        [info.update_information() for info in self.tpm_firmware_information ]

        # Initialise devices
        self._initialise_devices()

        # CPLD and SPI XML files have been loaded, check whether FPGA have been programmed
        # If FPGA is programmed, load the firmware's XML file
        if self['board.regfile.fpga1_programmed_fw'] != 0:
           self.load_firmware(device = Device.FPGA_1)

        if self['board.regfile.fpga2_programmed_fw'] != 0:
          self.load_firmware(device = Device.FPGA_2)

    def _initialise_devices(self, frequency = 700):
        """ Initialise the SPI and other devices on the board """

        # Initialise PLL (3 retries)
        for i in range(3):
            try:
                self.tpm_pll.pll_start(frequency)
                self.tpm_pll.pll_start(frequency)
                break
            except PluginError as err:
                if i == 2:
                    raise err

        # Initialise ADCs
        [self.tpm_adc[i].adc_single_start() for i in range(len(self.tpm_adc))]

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

        # Check if the specified key is a memory address or register name
        if type(key) in [int, long]:
            return self.read_address(key)

        # Check if the specified key is a tuple, in which case we are reading from a device
        if type(key) is tuple:
            # Run checks
            if not self._checks():
                return

            if len(key) == 2:
                return self.read_device(key[0], key[1])
            else:
                raise LibraryError("A device name and address need to be specified for writing to SPI devices")

        elif type(key) is str:
            # Run checks
            if not self._checks():
                return

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

        # Check is the specified key is a memory address or register name
        if type(key) in [int, long]:
            return self.write_address(key, value)

        # Check if the specified key is a tuple, in which case we are writing to a device
        if type(key) is tuple:
            # Run checks
            if not self._checks():
                return

            if len(key) == 2:
                return self.write_device(key[0], key[1], value)
            else:
                raise LibraryError("A device name and address need to be specified for writing to SPI devices")

        elif type(key) is str:
            # Run checks
            if not self._checks():
                return

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
from pyfabil.base.utils import convert_uint_to_string
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

        self._firmware_revison_number = 0x0
        self._magic_number            = 0x4
        self._xml_offset              = 0x8
        self._another_magic_number    = 0xC
        self._info_string_offset      = 0x10


    def load_firmware(self, device, filepath = None, load_values = False):
        """ Override superclass load_firmware to extract memory map from the bitfile
            This is saved in a tmp directory and forwarded to the superclass for
            processing
        :param device: The device on which the firmware will be loaded
        :param filepath: Filepath of the firmware, None if already loaded
        :param load_values:
        """

        # If a filename is not provided, then this means that we're loading from the board itself
        if not filepath:
            # Read the offset where the zipped XML is stored
            xml_off = self.read_address(self._xml_offset, device = device)

            # First 4 bytes are the zipped XML file length in byte
            xml_len = self.read_address(xml_off, device = device)

            # Read the zipped XML, this should be optimized using larger accesses
            zipped_xml = self.read_address(xml_off + 4, int(ceil(xml_len / 4.0)), device = device)
            zipped_xml = ''.join([format(n, '08x') for n in zipped_xml])

            # Convert to string
            zipped_xml = zlib.decompress(binascii.unhexlify(zipped_xml[: 2 * xml_len]))

            # Process
            filepath = "/tmp/xml_file.xml"
            with open(filepath, "w") as f:
                # Add necessary XML
                zipped_xml = "%s%s%s" % ('<node>\n', zipped_xml.replace('', 'fpga1'), "</node>")

                # Write to temporary file
                f.write(zipped_xml)
                f.flush()

                # Call superclass with this file
                super(TPM, self).load_firmware(device=device, filepath = filepath)
        else:
            super(TPM, self).load_firmware(device=device, filepath = filepath)


    def __getitem__(self, key):
        """ Override __getitem__, return value from board """

        # Run checks
        if not self._checks():
            return

        # Check if the specified key is a memory address or register name
        if type(key) is int:
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
    tpm = TPM()
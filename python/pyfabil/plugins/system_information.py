__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.utils import convert_uint_to_string
from pyfabil.base.definitions import *
import logging

class UniBoardSystemInformation(FirmwareBlock):
    """ FirmwareBlock tests class """

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_system_information')
    @maxinstances(1)
    def __init__(self, board):
        """ UniBoardSystemInformation initialiser
        :param board: Pointer to board instance
        :return: Nothing
        """
        super(UniBoardSystemInformation, self).__init__(board)

        # Required register names
        self._information_register = "PIO_SYSTEM_INFO"

        # Map of UniBoard peripherals
        self._peripheral_map = { 7 : "eth1g",
                                 6 : "eth10g",
                                 5 : "tr_mesh",
                                 4 : "tr_back",
                                 3 : "ddr3_I",
                                 2 : "ddr3_II",
                                 1 : "adc",
                                 0 : "wdi" }

    def initialise(self):
        """ Initialise FirmwareTest """
        logging.info("UniBoardSystemInformation has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("UniBoardSystemInformation : Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("UniBoardSystemInformation : Cleaning up")
        return True

    def print_system_information(self, nodes='ALL'):
        """ Extract system information from loaded firmware for each node
            :param nodes: Nodes to query
        """

        # Extract information about register from first node, assume that the register
        # on each node has the same size
        if "fpga1.%s" % self._information_register in self.board.register_list.keys():
            system_info_size = self.board.register_list["fpga1.%s" % self._information_register]['size']
        else:
            raise LibraryError("System information register not available")

        # Get required information from all nodes at once
        for (node, result, values) in self.board.read_register("%s.%s" % (nodes, self._information_register), system_info_size):

            # Check for errors
            if result != 0:
                print "Error retrieving system information for node %d" % node

            # Print class-specific information
            print "Node Index:\t\t%d" % node
            print "Node Type:\t\t%s" % {'B' : 'Back', 'F' : 'Front'}[self.board._nodes[node]['type']]
            print "Device:\t\t\t%d" % self.board._nodes[node]['device'].value
            print "Compatible Names:\t%s" % ', '.join(self.board._nodes[node]['names'])

            # Process system information from board
            print "g_sim:\t\t\t%d" % ((values[0] & 0x400) != 0)
            print "Firmware Version:\t%d.%d" % ((values[0] & 0xF00000) >> 20, (values[0] & 0x0F0000) >> 16)
            print "Hardware Version:\t%d" % ((values[0] & 0x300) >> 8)
            print "Design Name:\t\t%s" % convert_uint_to_string(values[2:10])
            print "Design Note:\t\t%s" % convert_uint_to_string(values[13:21])
            print "Stamp date:\t\t%d"  % values[10]
            print "Stamp time:\t\t%d"  % values[11]
            print "Stamp SVN:\t\t%d"   % values[12]
            for item in high_bits(values[1], 32):
                print "Using peripheral:\t%s" % self._peripheral_map[item]
            print

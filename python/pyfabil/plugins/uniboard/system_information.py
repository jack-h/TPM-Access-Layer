__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.utils import convert_uint_to_string, high_bits
from pyfabil.base.definitions import *
import logging

class UniBoardSystemInformation(FirmwareBlock):
    """ FirmwareBlock tests class """

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_system_information')
    @maxinstances(1)
    def __init__(self, board, **kwargs):
        """ UniBoardSystemInformation initialiser
        :param board: Pointer to board instance
        :return: Nothing
        """
        super(UniBoardSystemInformation, self).__init__(board)

        # Required register names
        self._reg_address = "PIO_SYSTEM_INFO"

        # Check if list of nodes are valid and all are front nodes
        self._nodes = self.board._get_nodes(kwargs['nodes'])
        self._nodes = self._nodes if type(self._nodes) is list else [self._nodes]

        # Check if registers are available on all nodes
        for node in self._nodes:
            fpga_number = self.board.device_to_fpga(node)
            register_str = "fpga%d.%s" % (fpga_number, self._reg_address)
            if register_str not in self.board.register_list.keys():
                raise PluginError("UniBoardSystemInformation: Node %d does not have register %s" % (fpga_number, self._reg_address))

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

    def print_system_information(self):
        """ Extract system information from loaded firmware for each node """

        # Get required information from all nodes at once
        for (node, result, values) in self.board.read_register(self._reg_address, n = 13, device = self._nodes):

            # Print class-specific information
            print "Node Index:\t\t%d" % node
            print "Node Type:\t\t%s" % {'B' : 'Back', 'F' : 'Front'}[self.board.nodes[node]['type']]
            print "Device:\t\t\t%d" % self.board.nodes[node]['device'].value
            print "Compatible Names:\t%s" % ', '.join(self.board.nodes[node]['names'])

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

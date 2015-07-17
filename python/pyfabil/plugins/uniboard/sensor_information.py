__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.utils import convert_uint_to_string
from pyfabil.base.definitions import *
import logging

class UniBoardSensorInformation(FirmwareBlock):
    """ FirmwareBlock tests class """

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_beamformer')
    @maxinstances(1)
    def __init__(self, board):
        """ UniBoardSensorInformation initialiser
        :param board: Pointer to board instance
        :return: Nothing
        """
        super(UniBoardSensorInformation, self).__init__(board)

        # Required register names
        self._sensor_register = "REG_UNB_SENS"

    def initialise(self):
        """ Initialise FirmwareTest """
        logging.info("UniBoardSensorInformation has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("UniBoardSensorInformation : Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("UniBoardSensorInformation : Cleaning up")
        return True

    def print_system_information(self, nodes='ALL'):
        """ Extract system information from loaded firmware for each node
            :param nodes: Nodes to query
        """

        I2C_LTC4260_V_UNIT_SENSE   = 0.0003
        I2C_LTC4260_V_UNIT_SOURCE  = 0.4
        SENS_HOT_SWAP_R_SENSE      =  0.005
        SENS_HOT_SWAP_I_UNIT_SENSE = I2C_LTC4260_V_UNIT_SENSE / SENS_HOT_SWAP_R_SENSE

        # Extract information about register from first node, assume that the register
        # on each node has the same size
        if "fpga1.%s" % self._sensor_register in self.board._registerList.keys():
            system_info_size = self.board._registerList["fpga1.%s" % self._sensor_register]['size']
        else:
            raise LibraryError("System information register not available")

        # Get required information from all nodes at once
        for (node, result, values) in self.board.read_register("%s.%s" % (nodes, self._sensor_register), system_info_size):

            # Check for errors
            if result != 0:
                print "Error retrieving sensor information for node %d" % node

            # Print class-specific information
            print "Node Index:\t\t%d" % node
            print "FPGA Temperature:\t%d" % values[0]
            print "ETH PHY Temperature:\t%d" % values[1]
            print "UNB supply current:\t%4.1f [A]" % (values[2] * SENS_HOT_SWAP_I_UNIT_SENSE)
            print "UNB supply voltage:\t%4.1f [V]" % (values[3] * I2C_LTC4260_V_UNIT_SOURCE)
            if values[4] != 0:
                print "Something went wrong with I2C access"
            print

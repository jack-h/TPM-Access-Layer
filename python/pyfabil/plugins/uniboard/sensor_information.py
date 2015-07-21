__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.utils import convert_uint_to_string
from pyfabil.base.definitions import *
import logging

class UniBoardSensorInformation(FirmwareBlock):
    """ FirmwareBlock tests class """

    I2C_LTC4260_V_UNIT_SENSE   = 0.0003
    I2C_LTC4260_V_UNIT_SOURCE  = 0.4
    SENS_HOT_SWAP_R_SENSE      =  0.005
    SENS_HOT_SWAP_I_UNIT_SENSE = I2C_LTC4260_V_UNIT_SENSE / SENS_HOT_SWAP_R_SENSE

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_sensor_information')
    @maxinstances(1)
    def __init__(self, board, **kwargs):
        """ UniBoardSensorInformation initialiser
        :param board: Pointer to board instance
        :return: Nothing
        """
        super(UniBoardSensorInformation, self).__init__(board)

        # Required register names
        self._reg_address = "REG_UNB_SENS"

        # Check if list of nodes are valid and all are front nodes
        self._nodes = self.board._get_nodes(kwargs['nodes'])

        # Check if registers are available on all nodes
        for node in self._nodes:
            fpga_number = self.board.device_to_fpga(node)
            register_str = "fpga%d.%s" % (fpga_number, self._reg_address)
            if register_str not in self.board.register_list.keys():
                raise PluginError("UniBoardSensorInformation: Node %d does not have register %s" % (fpga_number, self._reg_address))

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

    def print_sensor_information(self, nodes='ALL'):
        """ Extract sensor information from loaded firmware for each node
            :param nodes: Nodes to query
        """
        # Get required information from all nodes at once
        for (node, status, node_data) in self.board.read_register(self._reg_address, n = 5, device = self._nodes):

            # Print class-specific information
            if node == 7:
                print
                print "Node Index:\t\t\t%d" % node
                print "FPGA Temperature:\t\t%d   [C]" % node_data[0]
                print "ETH PHY Temperature:\t\t%d   [C]" % node_data[1]
                print "UNB supply current:\t\t%.1f  [A]" % (node_data[2] * self.SENS_HOT_SWAP_I_UNIT_SENSE)
                print "UNB supply voltage:\t\t%.1f [V]" % (node_data[3] * self.I2C_LTC4260_V_UNIT_SOURCE)
                print "UNB supply power:\t\t%.0f  [W]"   % (node_data[3] * self.I2C_LTC4260_V_UNIT_SOURCE * node_data[2] * self.SENS_HOT_SWAP_I_UNIT_SENSE)

                if node_data[4] != 0:
                    print "Something went wrong with I2C access"
            else:
                print "Node %d FPGA Temperature:\t%d" % (node, node_data[0])


__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import *
import logging

"""Peripheral dp_bsn_scheduler

   Register map:

    31             24 23             16 15              8 7               0  wi
   |-----------------|-----------------|-----------------|-----------------|
   |           wr scheduled_bsn[31: 0] / rd current_bsn[31: 0]             |  0
   |-----------------------------------------------------------------------|
   |           wr scheduled_bsn[63:32] / rd current_bsn[63:32]             |  1
   |-----------------------------------------------------------------------|

"""

class UniBoardBsnScheduler(FirmwareBlock):
    """ FirmwareBlock tests class """

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_bsn_scheduler')
    @maxinstances(1)
    def __init__(self, board, **kwargs):
        """ UniBoardBsnScheduler initialiser
        :param board: Pointer to board instance
        """
        super(UniBoardBsnScheduler, self).__init__(board)

        # Check if instance ID is in arguments
        if 'instance_id' not in kwargs.keys():
            raise PluginError("UniBoardBsnScheduler: Instance ID not specified")
        self._instance_id = kwargs['instance_id']

        # Required register names
        self._bsn_register = "REG_BSN_SCHEDULER_%s" % self._instance_id

        # Get list of nodes
        if 'nodes' not in kwargs.keys():
            raise PluginError("UniBoardBsnScheduler: List of nodes not specified")

        # Check if list of nodes are valid, and are all back-nodes
        self._nodes = self.board._get_nodes(kwargs['nodes'])
        for node in self._nodes:
            if self.board.nodes[self.board._device_node_map[node]]['type'] != 'B':
                raise PluginError("UniBoardBsnScheduler: Specified node must be a back node")

        # Check if BSN register is available on all nodes
        for node in self._nodes:
            fpga_number = self.board.device_to_fpga(node)
            register_str = "fpga%d.%s" % (fpga_number, self._bsn_register)
            if register_str % () not in self.board.register_list.keys():
                raise PluginError("UniBoardBsnScheduler: Node %d does not have register %s" % (fpga_number, self._bsn_register))

        # Minimal control response time in BSN units needed to schedule a new BSN relative to the just read current BSN
        # The block size equals the FFT size and is 1024 samples at 800 MHz, so one BSN unit equals 1.28 us. Assume a
        # minimal response latency of about 1 ms is sufficient. To be save on target set the delay to 10 ms on target.
        self.bsn_latency = 10000

    #######################################################################################

    def write_scheduled_bsn(self, bsn):
        """ Write scheduled BSN
            :param bsn: BSN
        """
        self.board.write_register(self._bsn_register, [bsn  % 2**32, bsn // 2**32], device = self._nodes)

    def read_current_bsn(self):
        """ Read current BSN
        :return: Current BSN
        """
        # Read BSN from nodes
        data = self.board.read_register(self._bsn_register, n = 2, device = self._nodes)
        return [node_data[0] + node_data[1] * c_word_mod  for (node, status, node_data) in data]

    ##################### Superclass method implementations #################################

    def initialise(self):
        """ Initialise FirmwareTest """

        logging.info("UniBoardBsnScheduler has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("UniBoardBsnScheduler : Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("UniBoardBsnScheduler : Cleaning up")
        return True
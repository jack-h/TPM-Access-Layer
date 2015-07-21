__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import *
import logging

"""Peripheral dpmm

  RO  read only  (no VHDL present to access HW in write mode)
  WO  write only (no VHDL present to access HW in read mode)
  WE  write event (=WO)
  WR  write control, read control
  RW  read status, write control
  RC  read, clear on read
  FR  FIFO read
  FW  FIFO write

  wi  Bits    R/W Name          Default  Description            |REG_DPMM_CTRL|
  =============================================================================
  0   [31..0] RO  usedw         0x0
  =============================================================================


  wi  Bits    R/W Name          Default  Description            |REG_DPMM_DATA|
  =============================================================================
  0   [31..0] FR  rd_data       0x0
  =============================================================================

"""

class UniBoardDpmm(FirmwareBlock):
    """ FirmwareBlock tests class """

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_dpmm')
    @maxinstances(0)
    def __init__(self, board, **kwargs):
        """ UniBoardBsnScheduler initialiser
        :param board: Pointer to board instance
        """
        super(UniBoardDpmm, self).__init__(board)

        # Register map
        self._reg_usedw   = 0

        # Examples of piNames: REG_DPMM_CTRL_0, REG_DPMM_DATA_0 etc
        self._instance_number = kwargs.get('instance_number', None)
        self._instance_str = []
        self._ctrl_reg_addr = []
        self._data_reg_addr = []
        if self._instance_number is None:
            self._instance_str.append('DM : ')
            self._ctrl_reg_addr.append('REG_DPMM_CTRL')
            self._data_reg_addr.append('REG_DPMM_DATA')
            self._instance_number = [0]
        else:
            # Support multiple instances per node
            for i in self._instance_number:
                self._instance_str.append('DM-%d : ' % i)
                self._ctrl_reg_addr.append('REG_DPMM_CTRL_%d' % i)
                self._data_reg_addr.append('REG_DPMM_DATA_%d' % i)

        # Get list of nodes
        if 'nodes' not in kwargs.keys():
            raise PluginError("UniBoardDpmm: List of nodes not specified")

        # Check if list of nodes are valid, and are all back-nodes
        self._nodes = self.board._get_nodes(kwargs['nodes'])
        self._nodes = self._nodes if type(self._nodes) is list else [self._nodes]

        # Check if registers are available on all nodes
        for node in self._nodes:
            fpga_number = self.board.device_to_fpga(node)
            for reg in self._ctrl_reg_addr:
                register_str = "fpga%d.%s" % (fpga_number, reg)
                if register_str not in self.board.register_list.keys():
                    raise PluginError("UniBoardDpmm: Node %d does not have register %s" % (fpga_number, reg))

            for reg in self._data_reg_addr:
                register_str = "fpga%d.%s" % (fpga_number, reg)
                if register_str not in self.board.register_list.keys():
                    raise PluginError("UniBoardDpmm: Node %d does not have register %s" % (fpga_number, reg))

    #######################################################################################

    def read_usedw(self):
        return [node_data[0] for i in range(len(self._instance_number))
                for (node, status, node_data) in
                self.board.read_register(self._ctrl_reg_addr[i], offset = self._reg_usedw, n = 1, device = self._nodes)]


    def read_data(self, nof):
        return [node_data for i in range(len(self._instance_number))
                for (node, status, node_data) in
                self.board.read_register(self._data_reg_addr[i], n = nof, device = self._nodes)]

    ##################### Superclass method implementations #################################

    def initialise(self):
        """ Initialise UniBoardDpmm """

        logging.info("UniBoardDpmm has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("UniBoardDpmm : Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("UniBoardDpmm : Cleaning up")
        return True
__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import *
import logging

"""
  Peripheral dp_bsn_source

  RO  read only  (no VHDL present to access HW in write mode)
  WO  write only (no VHDL present to access HW in read mode)
  WE  write event (=WO)
  WR  write control, read control
  RW  read status, write control
  RC  read, clear on read
  FR  FIFO read
  FW  FIFO write

  wi  Bits    R/W Name               Default  Description
  ====================================================================================
  0   [0]     RW  dp_on              0x0      WR '1' enables DP (on PPS when dp_on_pps=1)
                                              RD '1' = data path enabled, else disabled
      [1]     RW  dp_on_pps          0x0
  1   [31..0] WR  nof_block_per_sync 0x0
  2   [31..0] RW  bsn[31..0]         0x0      write init_bsn, read current bsn
  3   [31..0] RW  bsn[63..32]        0x0      write init_bsn, read current bsn
  ====================================================================================

"""

class UniBoardBsnSource(FirmwareBlock):
    """ FirmwareBlock tests class """

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_bsn_source')
    @maxinstances(1)
    def __init__(self, board, **kwargs):
        """ UniBoardBsnSource initialiser
        :param board: Pointer to board instance
        """
        super(UniBoardBsnSource, self).__init__(board)

        # Required register names
        self._bsn_register = "REG_BSN_SOURCE"

        # Get list of nodes
        if 'nodes' not in kwargs.keys():
            raise PluginError("UniBoardBsnSource: List of nodes not specified")

        # Check if list of nodes are valid, and are all back-nodes
        self._nodes = self.board._get_nodes(kwargs['nodes'])
        for node in self._nodes:
            if self.board.nodes[self.board._device_node_map[node]]['type'] != 'B':
                raise PluginError("UniBoardBsnSource: Specified node must be a back node")

        # Check if BSN register is available on all nodes
        for node in self._nodes:
            fpga_number = self.board.device_to_fpga(node)
            register_str = "fpga%d.%s" % (fpga_number, self._bsn_register)
            if register_str % () not in self.board.register_list.keys():
                raise PluginError("UniBoardBsnSource: Node %d does not have register %s" % (fpga_number, self._bsn_register))

        self._sample_frequency  = 800 *10 ** 6  # ADC 8-bit sample frequency
        self._samples_per_block = 1024          # Number of ADC 8-bit samples per block, e.g. 1024 for PFB down sample factor of 1024
        self._blocks_per_sync   = -1            # let this be set by read_nof_block_per_sync()
        self._sync_interval     = -1            # let this be set by read_nof_block_per_sync(), in seconds

    #######################################################################################

    def write_enable(self):
        """ Write the register data to the node(s) """
        self.board.write_register(self._bsn_register, 1, device = self._nodes)

    def write_enable_pps(self):
        """ Write the register data to the node(s) """
        self.board.write_register(self._bsn_register, 3, device = self._nodes)

    def write_disable(self):
        """ Write the register data to the node(s) """
        self.board.write_register(self._bsn_register, 0, device = self._nodes)

    def write_restart(self):
        """ Write restart """
        # Disable
        self.write_disable()

        # Wait until data path is off
        do_until_eq( self.read_status, 0, s_timeout = 0.5 )

        # Enable
        self.write_enable()

    def write_restart_pps(self):
        """ Restart PPS """
        # Disable
        self.write_disable()

        # Wait until data path is off
        do_until_eq( self.read_status, 0, s_timeout = 0.5 )

        # Enable
        time.sleep(1)
        self.write_enable_pps()

    def read_status(self):
        """ Read status
            :return Status of each node
         """
        # Read status from nodes
        data = self.board.read_register(self._bsn_register, 1, device = self._nodes)
        return [node_data for (node, status, node_data) in data]

    def write_blocks_per_sync(self, data = None):
        """ Write blocks per sync
            :param data: Value
        """
        if data == None:
            data = self._sample_frequency / self._samples_per_block # Default 781250 blocks per sync interval

        # Write the register data to the nodes(s)
        self.board.write_register(self._bsn_register, data, offset = 1, device = self._nodes)

    def read_blocks_per_sync(self):
        """ Read blocks per sync
            :return Read blocks per sync for each node
        """
        # Get register data from the node(s)
        data = self.board.read_register(self._bsn_register, n = 1, offset = 1, device = self._nodes)

        # Evaluate per node
        result = []
        for (node, status, node_data) in data:
            self._blocks_per_sync = node_data[0]
            self._sync_interval = 1.0 * self._blocks_per_sync * self._samples_per_block / self._sample_frequency
            result.append(node_data[0])

        # All done, return
        return result

    def write_init_bsn(self, bsn):
        """ Write initial BSN
            :param bsn: initial bsn
        """
        # Write the register data to the node(s) and log the access status
        self.board.write_register(self._bsn_register, [bsn % c_word_mod, bsn // c_word_mod], offset = 2, device = self._nodes)

    def read_current_bsn(self, ):
        """ Read current BSN
        :return: current BSN
        """
        # Write the register data to the node(s) and log the access status
        data = self.board.read_register(self._bsn_register, n = 2, offset = 2, device = self._nodes)
        return [node_data[0] + node_data[1] * c_word_mod for (node, status, node_data) in data]

    ##################### Superclass method implementations #################################

    def initialise(self):
        """ Initialise FirmwareTest """
        logging.info("UniBoardBsnSource has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("UniBoardBsnSource : Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("UniBoardBsnSource : Cleaning up")
        return True
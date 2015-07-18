__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import *
import logging

"""Peripheral tr_nonbonded

  RO  read only  (no VHDL present to access HW in write mode)
  WO  write only (no VHDL present to access HW in read mode)
  WE  write event (=WO)
  WR  write control, read control
  RW  read status, write control
  RC  read, clear on read
  FR  FIFO read
  FW  FIFO write

  wi  Bits             R/W Name             Default  Description                      |REG_TR_NONBONDED|
  ======================================================================================================
  0   [  nof_tr-1..0]  WR  tx_align_en      0x0      '1' per TX to send alignment pattern.
  1   [2*nof_tr-1..0]  RO  tx_state         0x3*     2 bits per receiver indicate state:
                                                     0x0 = Reset
                                                     0x1 = Align
                                                     0x3 = Ready
  2   [  nof_tr-1..0]  WO  rx_align_en      0x0      '1' to force RX align FSM to restart.
  3   [2*nof_tr-1..0]  RO  rx_state         0x3*     2 bits per receiver indicate state:
                                                     0x0 = Reset
                                                     0x1 = Align
                                                     0x3 = Valid

  4   [31..0]          RO  rx_dataout_0     0x0      Sample register, RX instance 0
  .   .                .                    .        .                            .
  .   .                .                    .        .                            .
  15  [31..0]          RO  rx_dataout_11    0x0      Sample register, RX instance 11
  ======================================================================================================
  * Default value per transceiver instance

"""

class UniBoardNonBondedTr(FirmwareBlock):
    """ FirmwareBlock tests class """

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_nonbonded_tr')
    @maxinstances(1)
    def __init__(self, board, **kwargs):
        """ UniBoardBsnSource initialiser
        :param board: Pointer to board instance
        """
        super(UniBoardNonBondedTr, self).__init__(board)

        # Required register name
        self._nonbonded_register = "REG_TR_NONBONDED"

        # Check if instance ID is in arguments
        self._instance_id = ''
        if 'instance_id' in kwargs.keys() and kwargs['instance_id'] != '':
            self._nonbonded_register = "REG_TR_NONBONDED_%s" % kwargs['instance_id']
            self._instance_id = kwargs['instance_id']

        # Check if number of transceivers is in arguments
        self._num_transceivers = 12
        if 'num_transceivers' in kwargs.keys():
            self._num_transceivers = kwargs['num_transceivers']

        # Get list of nodes
        if 'nodes' not in kwargs.keys():
            raise PluginError("UniBoardNonBondedTr: List of nodes not specified")

        # Check if list of nodes are valid, and are all back-nodes
        self._nodes = self.board._get_nodes(kwargs['nodes'])

        # Check if register is available on all nodes
        for node in self._nodes:
            fpga_number = self.board.device_to_fpga(node)
            register_str = "fpga%d.%s" % (fpga_number, self._nonbonded_register)
            if register_str % () not in self.board.register_list.keys():
                raise PluginError("UniBoardNonBondedTr: Node %d does not have register %s" % (fpga_number, self._nonbonded_register))

        # Register map
        self._reg_tx_align_en = 0
        self._reg_tx_state    = 1
        self._reg_rx_align_en = 2
        self._reg_rx_state    = 3
        self._reg_rx_dataout  = 4

    #######################################################################################

    def write_tx_align_enable(self, wr_data = None):
        """  Write tx align enable """
        if wr_data is None:
            data = CommonBits(0, c_word_w)
            data[self._num_transceivers - 1 : 0] = -1
        else:
            data = wr_data

        # Write value to nodes
        self.board.write_register(self._nonbonded_register, data, offset = self._reg_tx_align_en, device = self._nodes)

    def read_tx_state(self):
        """ Read tx state
        :return: Tx state
        """
        # Read data from nodes
        data = self.board.read_register(self._nonbonded_register, 1, offset=self._reg_tx_state, device = self._nodes)

        # Evaluate result per node
        result = []
        for (node, status, node_data) in data:
            if status != self.board.ST_OK:
                result.append('X')
            else:
                result.append(node_data[0])
        return result

    def read_rx_state(self):
        """ Read rx state
        :return: Rx state
        """
        # Read data from nodes
        data = self.board.read_register(self._nonbonded_register, 1, offset=self._reg_rx_state, device = self._nodes)
        return [node_data for (node, status, node_data) in data]

    def write_rx_align_enable(self, wr_data = None):
        """  Write rx align enable """
        if wr_data is None:
            data = CommonBits(0, c_word_w)
            data[self._num_transceivers - 1 : 0] = -1
        else:
            data = wr_data

        # Write value to nodes
        self.board.write_register(self._nonbonded_register, data, offset = self._reg_rx_align_en, device = self._nodes)

    def read_rx_dataout(self, instance_number = None):
        """ Read rx dataout
        :param instance_number: Instance number
        :return: result
        """
        num_instances = 1
        if instance_number is None:
            num_instances = self._num_transceivers

        # Read values from nodes
        data = self.board.read_register(self._nonbonded_register, offset = self._reg_rx_dataout,
                                        n = num_instances, device = self._nodes)
        return [node_data for (node, status, node_data) in data]

    ##################### Superclass method implementations #################################

    def initialise(self):
        """ Initialise FirmwareTest """

        logging.info("UniBoardNonBondedTr has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("UniBoardNonBondedTr : Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("UniBoardNonBondedTr : Cleaning up")
        return True
__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import *
import logging

"""Peripheral remu

  RO  read only  (no VHDL present to access HW in write mode)
  WO  write only (no VHDL present to access HW in read mode)
  WE  write event (=WO)
  WR  write control, read control
  RW  read status, write control
  RC  read, clear on read
  FR  FIFO read
  FW  FIFO write

  wi  Bits    R/W Name              Default  Description             |REG_REMU|
  =============================================================================
  0   [0]     RO  reconfigure       0x0      Initiates reconfiguration of FPGA
  1   [2..0]  WO  param
  2   [0]     WE  read_param
  3   [0]     WE  write_param
  4   [23..0] RO  data_out
  5   [23..0] WO  data_in
  6   [0]     RO  busy

  =============================================================================
"""

class UniBoardRemoteUpdate(FirmwareBlock):
    """ FirmwareBlock tests class """

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_remote_update')
    @maxinstances(1)
    def __init__(self, board, **kwargs):
        """ UniBoardBsnSource initialiser
        :param board: Pointer to board instance
        """
        super(UniBoardRemoteUpdate, self).__init__(board)

        # Register map
        self._reg_reconfigure = 0
        self._reg_param       = 1
        self._reg_read_param  = 2
        self._reg_write_param = 3
        self._reg_dataout     = 4
        self._reg_datain      = 5
        self._reg_busy        = 6

        # Param codes
        self._param_start_address = 4 # b'100
        self._param_mode          = 5 # b'101

        # Config modes:
        self._config_mode_factory = 0
        self._config_mode_user    = 1

        # see synth/quartus/[design].map. Note that the page index does not make sense.
        # Address 0   = page_1 (!) = factory
        # Address xxx = page_0 (!) = user
        self._factory_sector_start = 0
        self._user_sector_start    = 26

        # The base (lowest) address of a sector: sector 0 starts at 0x0, sector 1 starts
        # at 0x40000 etc.
        self._factory_address     = self._factory_sector_start * 0x40000
        self._user_address        = self._user_sector_start    * 0x40000

        # Required register names
        self._reg_address = "REG_REMU"

        # Get list of nodes
        if 'nodes' not in kwargs.keys():
            raise PluginError("UniBoardRemoteUpdate: List of nodes not specified")

        # Check if list of nodes are valid, and are all back-nodes
        self._nodes = self.board._get_nodes(kwargs['nodes'])

        # Check if register is available on all nodes
        for node in self._nodes:
            fpga_number = self.board.device_to_fpga(node)
            register_str = "fpga%d.%s" % (fpga_number, self._reg_address)
            if register_str % () not in self.board.register_list.keys():
                raise PluginError("UniBoardRemoteUpdate: Node %d does not have register %s" % (fpga_number, self._reg_address))

    #######################################################################################

    def write_reconfigure(self, data = 0xB007FAC7):
         self.board.write_register(self._reg_address, data, offset = self._reg_reconfigure, device = self._nodes)

    def write_param(self, param):
        self.board.write_register(self._reg_address, param, offset = self._reg_param, device = self._nodes)

    def write_read_param(self, data = 1):
        self.board.write_register(self._reg_address, data, offset = self._reg_read_param, device = self._nodes)

    def write_write_param(self, data = 1):
        self.board.write_register(self._reg_address, data, offset = self._reg_write_param, device = self._nodes)

    def read_dataout(self):
        data = self.board.read_register(self._reg_address, offset = self._reg_dataout, n = 1, device = self._nodes)
        return [node_data for (node, status, node_data) in data]

    def write_datain(self, data):
        self.board.write_register(self._reg_address, data, offset = self._reg_datain, device = self._nodes)

    def read_busy(self):
        data = self.board.read_register(self._reg_address, offset = self._reg_busy, n = 1, device = self._nodes)
        return [node_data for (node, status, node_data) in data]

    def read_mode(self):
        self.write_param(self._param_mode)
        self.write_read_param()
        do_until_eq(self.read_busy, 0)
        return self.read_dataout()

    def write_mode(self, mode):
        self.write_param(self._param_mode)
        self.write_datain(mode)
        self.write_write_param()
        do_until_eq(self.read_busy, 0)

    def write_start_address_user(self):
        self.write_param(self._param_start_address)
        self.write_datain(self._user_address)
        self.write_write_param()
        do_until_eq(self.read_busy, 0)

    def write_start_address_factory(self):
        self.write_param(self._param_start_address)
        self.write_datain(self._factory_address)
        self.write_write_param()
        do_until_eq(self.read_busy, 0)

    def read_start_address(self):
        self.write_param(self._param_start_address)
        self.write_read_param()
        do_until_eq(self.read_busy, 0)
        return self.read_dataout()

    def write_factory_reconfigure(self):
        self.write_mode(self._config_mode_factory)
        self.write_start_address_factory()
        self.write_reconfigure()

    def write_user_reconfigure(self):
        self.write_mode(self._config_mode_user)
        self.write_start_address_user()
        self.write_reconfigure()

    ##################### Superclass method implementations #################################

    def initialise(self):
        """ Initialise FirmwareTest """
        logging.info("UniBoardRemoteUpdate has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("UniBoardRemoteUpdate : Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("UniBoardRemoteUpdate : Cleaning up")
        return True
__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import *
import logging

"""Peripheral ss_ss_wide

   Register map:

    31             24 23             16 15              8 7               0  wi
   |-----------------|-----------------|-----------------|-----------------|
   |                           Select_0[31:0]                              |  0
   |-----------------------------------------------------------------------|
   |                           Select_1[31:0]                              |  1
   |-----------------------------------------------------------------------|
                                       |
                                       |
                                       |
   |-----------------------------------------------------------------------|
   |                          Select_254[31:0]                             |  254
   |-----------------------------------------------------------------------|
   |                          Select_255[31:0]                             |  255
   |-----------------------------------------------------------------------|

   Remark:

"""

class UniBoardSSWide(FirmwareBlock):
    """ UniBoardSSReorder tests class """

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_ss_wide')
    @maxinstances(0)
    def __init__(self, board, **kwargs):
        """ UniBoardSSWide initializer
        :param board: Pointer to board instance
        """
        super(UniBoardSSWide, self).__init__(board)

        # Process arguments
        self._instance_number = kwargs.get('instance_number', 0)
        self._instance_name   = kwargs.get('instance_name', '')
        self._nof_select      = kwargs.get('nof_select', 8)
        self._wb_factor       = kwargs.get('wb_factor', 4)

        # Required register names
        self._ram_address = 'RAM_SS_SS_WIDE' if self._instance_name == '' else 'RAM_SS_SS_WIDE_%' + self._instance_name

        # Check if list of nodes are valid
        self._nodes = self.board._get_nodes(kwargs['nodes'])
        self._nodes = self._nodes if type(self._nodes) is list else [self._nodes]

        # Check if registers are available on all nodes
        for node in self._nodes:
            fpga_number = self.board.device_to_fpga(node)
            register_str = "fpga%d.%s" % (fpga_number, self._ram_address)
            if register_str not in self.board.register_list.keys():
                raise PluginError("UniBoardSSWide: Node %d does not have register %s" % (fpga_number, self._ram_address))

        self._nof_select_per_channel = self._nof_select
        self._address_single_channel = 2**ceil_log2(self._nof_select)
        self._nof_select            *= self._wb_factor

    #######################################################################################

    def read_selects(self):
        # Get the selects from the node(s)
        for k in range(self._wb_factor):
            addr_offset = self._instance_number * self._address_single_channel * self._wb_factor + k * self._address_single_channel
            data = self.board.read_register(self._ram_address, offset = addr_offset, n = self._nof_select, device = self._nodes)
            return [node_data for (node, status, node_data) in data]


    def write_selects(self, data):
        n = len(data)
        if n > self._nof_select:
            raise PluginError('write_selects: Number of selects is too high  (%d > %d)' % (n, self._nof_select))

        # Write the selects to the node(s)
        instance_offset = self._instance_number * self._address_single_channel * self._wb_factor
        for k in range(self._wb_factor):
            addr_offset = instance_offset + k * self._address_single_channel
            self.board.write_register(self._ram_address, data[k * self._nof_select_per_channel : (k +1) * self._nof_select_per_channel],
                                      offset = addr_offset, device = self._nodes)
            print '[%s] SS-WIDE write_selects (Instance Nr = %d)' % (str(self._nodes), self._instance_number)

    @staticmethod
    def subband_select(in_list, sel_list):
        """
        Offline subband select emulation method. in_list is an input stream [0:256].
        sel_list is a flat list [0:192] of which each element may be a value between 0:256.
        The result is an array of selected subbands [0:192].
        """
        result = []
        for sample in sel_list:
            result.append(in_list[sample])
        return result

    ##################### Superclass method implementations #################################

    def initialise(self):
        """ Initialise FirmwareTest """

        logging.info("UniBoardSSWide has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("UniBoardSSWide : Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("UniBoardSSWide : Cleaning up")
        return True
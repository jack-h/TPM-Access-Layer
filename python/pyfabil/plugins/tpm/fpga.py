__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import *
import logging


class TpmFpga(FirmwareBlock):
    """ FirmwareBlock tests class """

    @compatibleboards(BoardMake.TpmBoard)
    @friendlyname('tpm_pll')
    @maxinstances(1)
    def __init__(self, board, **kwargs):
        """ TpmPll initialiser
        :param board: Pointer to board instance
        """
        super(TpmFpga, self).__init__(board)

        self._board_type = kwargs.get('board_type', 'XTPM')
        self._node = self.board._get_nodes(kwargs['nodes'])
        if len(self._nodes) > 1:
            raise PluginError("TpmFpga: Only one node per instance is supported")

    #######################################################################################
    def fpga_start(self, input_list, enabled_list):
        """ Set up FPGA
        :param input_list: List of channel to enable
        :param enabled_list:
        :return:
        """
        filter_list = []
        for n in input_list:
            if n in enabled_list:
                filter_list.append(n)

        disabled_input = 0xFFFF
        for input in filter_list:
            mask = 1 << input
            disabled_input = disabled_input ^ mask

        rmp.wr32(0x30000008, 0x0081)  # Power down ADCs
        rmp.wr32(0x30000010, 0x0000)  # 0x1 Turn on ADA
        rmp.wr32(0x3000000C, 0x0)

        rmp.wr32(0x00030400 + idx * 0x10000000, 0x8);  # bit per sample

        # rmp.wr32(0x0000000C+idx*0x10000000, disabled_input);
        rmp.wr32(0x0001F004 + idx * 0x10000000, disabled_input);
        # rmp.wr32(0x00000004+idx*0x10000000, 0x1);#xTPM
        rmp.wr32(0x00030404 + idx * 0x10000000, 0x1);  # xTPM
        # rmp.wr32(0x00000008+idx*0x10000000, 0x0);
        rmp.wr32(0x0001F000 + idx * 0x10000000, 0x0);
        # rmp.wr32(0x00000008+idx*0x10000000, 0x1);
        rmp.wr32(0x0001F000 + idx * 0x10000000, 0x1);

        # time.sleep(2)

        # setting default buffer configuration
        for n in range(16):
            rmp.wr32(0x00030000 + 4 * n, n)  # first lane
            rmp.wr32(0x00030100 + 4 * n, n)  # last lane
            rmp.wr32(0x00030200 + 4 * n, n)  # write mux
        rmp.wr32(0x00030300, 0xFFFF);  # write mux we
        rmp.wr32(0x00030304, 0);  # write mux we shift

        # setting buffer configuration
        nof_input = len(filter_list)
        if self.board == "XTPM":
            slot_per_input = 16 / nof_input
        else:
            slot_per_input = 8 / nof_input

        k = 0
        for n in sorted(filter_list):
            rmp.wr32(0x00030000 + 4 * n, k);  # first lane
            rmp.wr32(0x00030100 + 4 * n, k + (slot_per_input - 1));  # last lane
            k += slot_per_input
        for n in range(16):
            if n / slot_per_input < len(filter_list):
                rmp.wr32(0x00030200 + 4 * n, sorted(filter_list)[n / slot_per_input]);  # write mux
        mask = 0
        for n in range(nof_input):
            mask = mask << slot_per_input
            mask |= 0x1
        rmp.wr32(0x00030300, mask);
        rmp.wr32(0x00030304, 0);

        # time.sleep(1)
        # self.wr_adc("all",0x572,0x80);
        # self.wr_adc("all",0x572,0xC0); #Force ILA and user data phase
#
#
# def fpga_stop(self):
#     """!@brief This function stops the FPGA acquisition and data downloading through 1Gbit Ethernet
#     """
#     # rmp.wr32(0x00000004, 0x0);
#     rmp.wr32(0x00030404, 0x0);
#     # rmp.wr32(0x10000004, 0x0);
#     # rmp.wr32(0x00000008, 0x0);
#     rmp.wr32(0x0001F000, 0x0);
#     # rmp.wr32(0x10000008, 0x0);
#     time.sleep(1)
#

    ##################### Superclass method implementations #################################


    def initialise(self):
        """ Initialise TpmPll """
        logging.info("TpmPll has been initialised")
        return True


    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("TpmPll : Checking status")
        return Status.OK


    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("TpmPll : Cleaning up")
        return True

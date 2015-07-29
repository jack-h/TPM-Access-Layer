__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import *
import logging


class TpmFpga(FirmwareBlock):
    """ FirmwareBlock tests class """

    @compatibleboards(BoardMake.TpmBoard)
    @friendlyname('tpm_fpga')
    @maxinstances(1)
    def __init__(self, board, **kwargs):
        """ TpmPll initialiser
        :param board: Pointer to board instance
        """
        super(TpmFpga, self).__init__(board)

        self._board_type = kwargs.get('board_type', 'XTPM')

        if 'device' not in kwargs.keys():
            raise PluginError("TpmFpga: Require a node instance")
        self._device = kwargs['device']

        if self._device == Device.FPGA_1:
            self._device = 'fpga1'
        elif self._device == Device.FPGA_2:
            self._device = 'fpga2'
        else:
            raise PluginError("TpmFpga: Invalid device %d" % self._device)

        self._nof_inputs = 16

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
        for item in filter_list:
            mask = 1 << item
            disabled_input ^= mask

        # TODO: Switch the two below when XML behaviour is implemented
        # self.board['board.regfile.ctrl'] = 0x0081  # Power down ADCs
        # self.board['board.regfile.ada_ctrl'] = 0x0000 # 0x1 Turns on ADS
        # self.board['board.regfile.ethernet_pause'] = 0x0
        self.board[0x30000008] = 0x0081  # Power down ADCs
        self.board[0x30000010] = 0x0000 # 0x1 Turns on ADS
        self.board[0x3000000C] = 0xA000

        self.board['%s.jesd_buffer.bit_per_sample' % self._device] = 0x8  # bit per sample
        self.board['%s.jesd204_if.regfile_channel_disable' % self._device] = disabled_input
        self.board['%s.jesd_buffer.test_pattern_enable' % self._device] = 0x0  # xTPM
        self.board['%s.jesd204_if.regfile_ctrl.reset_n' % self._device] = 0x0
        self.board['%s.jesd204_if.regfile_ctrl.reset_n' % self._device] = 0x1

        # Setting default buffer configuration
        for n in range(self._nof_inputs):
            self.board['%s.jesd_buffer.read_first_%d' % (self._device, n)] = n
            self.board['%s.jesd_buffer.read_last_%d' % (self._device, n)] = n
            self.board['%s.jesd_buffer.write_mux_config_%d' % (self._device, n)] = n
        self.board['%s.jesd_buffer.write_mux_we' % self._device] = 0xFFFF # Write mux we
        self.board['%s.jesd_buffer.write_mux_we_shift' % self._device] = 0x0 # Write mux we shift

        # Setting buffer configuration
        nof_input = len(filter_list)
        if self._board_type == "XTPM":
            slot_per_input = self._nof_inputs / nof_input
        else:
            slot_per_input = 8 / nof_input

        k = 0
        for n in sorted(filter_list):
            self.board['%s.jesd_buffer.read_first_%d' % (self._device, n)] = k
            self.board['%s.jesd_buffer.read_last_%d' % (self._device, n)] = k + (slot_per_input - 1)
            k += slot_per_input

        for n in range(16):
            if n / slot_per_input < len(filter_list):
                self.board['%s.jesd_buffer.write_mux_config_%d' % (self._device, n)] = sorted(filter_list)[n / slot_per_input]  # write mux

        mask = 0
        for n in range(nof_input):
            mask <<= slot_per_input
            mask |= 0x1
        self.board['%s.jesd_buffer.write_mux_we' % self._device] = mask
        self.board['%s.jesd_buffer.write_mux_we_shift' % self._device] = 0x0

    def fpga_stop(self):
        """!@brief This function stops the FPGA acquisition and data downloading through 1Gbit Ethernet
        """
        self.board['%s.jesd_buffer.test_pattern_enable' % self._device] = 0x0
        self.board['%s.jesd204_if.regfile_ctrl'] = 0x0
        time.sleep(1)

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

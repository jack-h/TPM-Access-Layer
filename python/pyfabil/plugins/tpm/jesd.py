__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import *
import logging


class TpmJesd(FirmwareBlock):
    """ FirmwareBlock tests class """

    @compatibleboards(BoardMake.TpmBoard)
    @friendlyname('tpm_jesd')
    @maxinstances(1)
    def __init__(self, board, **kwargs):
        """ TpmJesd initialiser
        :param board: Pointer to board instance
        """
        super(TpmJesd, self).__init__(board)

        if 'device' not in kwargs.keys():
            raise PluginError("TpmJesd: device required")

        if 'core' not in kwargs.keys():
            raise PluginError("TpmJesd: core_id required")

        self._board_type = kwargs.get('board_type', 'XTPM')
        self._fpga = 'fpga1' if kwargs['device'] == Device.FPGA_1 else 'fpga2'
        self._core = kwargs['core']

    #######################################################################################

    def jesd_core_start(self):
        """!@brief This function performs the FPGA internal JESD core configuration and initialization procedure as implemented in ADI demo.
        @param bit -- int -- Sample bit width, supported value are 8,14
        """

        # Get FPGA base addresses
        self.board['%s.jesd204_if.core_id_%d_ila_support' % (self._fpga, self._core)] = 0x1
        self.board['%s.jesd204_if.core_id_%d_sysref_handling' % (self._fpga, self._core)] = 0x0
        self.board['%s.jesd204_if.core_id_%d_scrambling' % (self._fpga, self._core)] = 0x1
        self.board['%s.jesd204_if.core_id_%d_octets_per_frame' % (self._fpga, self._core)] = 0x0
        self.board['%s.jesd204_if.core_id_%d_frames_per_multiframe' % (self._fpga, self._core)] = 0x1F
        if self.board == "XTPM":
            self.board['%s.jesd204_if.core_id_%d_lanes_in_use' % (self._fpga, self._core)] = 0x7  # xTPM
        else:
            self.board['%s.jesd204_if.core_id_%d_lanes_in_use' % (self._fpga, self._core)] = 0x3
        self.board['%s.jesd204_if.core_id_%d_subclass_mode' % (self._fpga, self._core)] = 0x1
        self.board['%s.jesd204_if.core_id_%d_reset' % (self._fpga, self._core)] = 0x1

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

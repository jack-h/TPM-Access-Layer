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

        if 'fpga_id' not in kwargs.keys():
            raise PluginError("TpmJesd: fpga_id required")

        if 'core_id' not in kwargs.keys():
            raise PluginError("TpmJesd: core_id required")

        self._board_type = kwargs.get('board_type', 'XTPM')
        self._fpga_id = kwargs['fpga_id']
        self._core_id = kwargs['core_id']

    #######################################################################################

    def jesd_core_start(self):
        """!@brief This function performs the FPGA internal JESD core configuration and initialization procedure as implemented in ADI demo.
        @param bit -- int -- Sample bit width, supported value are 8,14
        """

        # TODO: Update the call below to use registers from memory map
        self.board[0x00010008 + self._fpga_id * 0x10000000 + self._core_id * 0x1000] = 0x1
        self.board[0x00010010 + self._fpga_id * 0x10000000 + self._core_id * 0x1000] = 0x0  # sysref
        self.board[0x0001000C + self._fpga_id * 0x10000000 + self._core_id * 0x1000] = 0x1  # scrambling
        self.board[0x00010020 + self._fpga_id * 0x10000000 + self._core_id * 0x1000] = 0x0
        self.board[0x00010024 + self._fpga_id * 0x10000000 + self._core_id * 0x1000] = 0x1f
        if self.board == "XTPM":
            self.board[0x00010028 + self._fpga_id * 0x10000000 + self._core_id * 0x1000] = 0x7  # xTPM
        else:
            self.board[0x00010028] = 0x3

        self.board[0x0001002C + self._fpga_id * 0x10000000 + self._core_id * 0x1000] = 0x1
        self.board[0x00010004 + self._fpga_id * 0x10000000 + self._core_id * 0x1000] = 0x1

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

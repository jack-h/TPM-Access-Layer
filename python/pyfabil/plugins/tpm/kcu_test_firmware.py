__author__ = 'lessju'

import logging

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *


class KcuTestFirmware(FirmwareBlock):
    """ FirmwareBlock tests class """

    @firmware({'design' : 'tpm_test', 'major' : '1', 'minor' : '>1' })
    @compatibleboards(BoardMake.TpmBoard)
    @friendlyname('kcu_test_firmware')
    @maxinstances(2)
    def __init__(self, board, **kwargs):
        """ KcuTestFirmware initialiser
        :param board: Pointer to board instance
        """
        super(KcuTestFirmware, self).__init__(board)

        # Device must be specified in kwargs
        if kwargs.get('device', None) is None:
            raise PluginError("KcuTestFirmware requires device argument")
        self._device = kwargs['device']

        # Load required plugins
        self._jesd = self.board.load_plugin("TpmJesd", device = self._device, core = 0)
        self._fpga = self.board.load_plugin('TpmFpga', board_type = 'NOTXTPM', device = self._device)

        # Initialise JESD core
        self._jesd.jesd_core_start()

        # Initialise FPGAs
        self._fpga.fpga_start(range(4), range(4))

    #######################################################################################

    def start_streaming(self):
        """ Start data streaming """
        self.board["board.regfile.c2c_stream_enable"] = 0x1

    ##################### Superclass method implementations #################################


    def initialise(self):
        """ Initialise KcuTestFirmware """
        logging.info("KcuTestFirmware has been initialised")
        return True


    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("KcuTestFirmware : Checking status")
        return Status.OK


    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("KcuTestFirmware : Cleaning up")
        return True

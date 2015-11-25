__author__ = 'Alessio Magro'

import logging

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from time import sleep

class TpmTestFirmware(FirmwareBlock):
    """ FirmwareBlock tests class """

    @firmware({'design' : 'tpm_test', 'major' : '1', 'minor' : '>1' })
    @compatibleboards(BoardMake.TpmBoard)
    @friendlyname('tpm_test_firmware')
    @maxinstances(2)
    def __init__(self, board, **kwargs):
        """ TpmTestFirmware initialiser
        :param board: Pointer to board instance
        """
        super(TpmTestFirmware, self).__init__(board)

        # Device must be specified in kwargs
        if kwargs.get('device', None) is None:
            raise PluginError("TpmTestFirmware requires device argument")
        self._device = kwargs['device']

        # Load required plugins
        jesd1 = self.board.load_plugin("TpmJesd", device = self._device, core = 0)
        jesd2 = self.board.load_plugin("TpmJesd", device = self._device, core = 1)
        self._fpga = self.board.load_plugin('TpmFpga', device = self._device)

        self._device_name = "fpga1" if self._device is Device.FPGA_1 else "fpga2"

        # Initialise JESD core (try multiple times)
        max_retries = 4
        retries = 0
	print self.board
        while self.board['%s.jesd204_if.regfile_status' % self._device_name] & 0x1F != 0x1C and retries < max_retries:
            jesd1.jesd_core_start()
            jesd2.jesd_core_start()

            # Initialise FPGAs
            # I have no idea what these ranges are
            self._fpga.fpga_start(range(16), range(16))

            retries += 1
            sleep(0.5)

        if retries == max_retries:
            raise BoardError("TpmTestFirmware: Could not configure JESD cores")

        # Initialise SPEAD transmission
        self.initialize_spead()

    #######################################################################################

    def initialize_spead(self):
        """ Initialize SPEAD  """
        self.board["board.regfile.c2c_stream_enable"] = 0x1
        self.board["%s.spead_tx.control" % self._device_name] = 0x0400100C

    def send_raw_data(self):
        """ Send raw data from the TPM """
        self.board["%s.lmc_gen.request.raw_data" % self._device_name] = 0x1

    def send_channelised_data(self, number_of_samples = 128):
        """ Send channelized data from the TPM """
        self.board["%s.lmc_gen.channelized_pkt_length" % self._device_name] = number_of_samples - 1
        self.board["%s.lmc_gen.request.channelized_data" % self._device_name] = 0x1

    def send_beam_data(self):
        """ Send beam data from the TPM """
        self.board["%s.lmc_gen.request.beamformed_data" % self._device_name] = 0x1

    ##################### Superclass method implementations #################################

    def initialise(self):
        """ Initialise TpmTestFirmware """
        logging.info("TpmTestFirmware has been initialised")
        return True


    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("TpmTestFirmware : Checking status")
        return Status.OK


    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("TpmTestFirmware : Cleaning up")
        return True

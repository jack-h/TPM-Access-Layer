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
        self._jesd1 = self.board.load_plugin("TpmJesd", device = self._device, core = 0)
        self._jesd2 = self.board.load_plugin("TpmJesd", device = self._device, core = 1)
        self._fpga = self.board.load_plugin('TpmFpga', device = self._device)
        self._teng = self.board.load_plugin("TpmTenGCore", device = self._device, core = 0)

        self._device_name = "fpga1" if self._device is Device.FPGA_1 else "fpga2"

    def initialise_firmware(self):
        """ Initialise firmware components """
        max_retries = 4
        retries = 0
        while self.board['%s.jesd204_if.regfile_status' % self._device_name] & 0x1F != 0x1C and retries < max_retries:
            # Reset FPGA
            self._fpga.fpga_reset()

            # Start JESD cores
            self._jesd1.jesd_core_start()
            self._jesd2.jesd_core_start()

            # Initialise FPGAs
            # I have no idea what these ranges are
            self._fpga.fpga_start(range(16), range(16))

            retries += 1
            sleep(0.5)


        # Initialise SPEAD transmission
        self.initialize_spead()

        # Initialise 10G cores
        self._teng.initialise_core()

        if retries == max_retries:
            raise BoardError("TpmTestFirmware: Could not configure JESD cores")

    #######################################################################################

    def initialize_spead(self):
        """ Initialize SPEAD  """
        self.board["%s.lmc_spead_tx.control" % self._device_name] = 0x0400100C

    def send_raw_data(self):
        """ Send raw data from the TPM """
        self.board["%s.lmc_gen.request.raw_data" % self._device_name] = 0x1

    def send_channelised_data(self, number_of_samples = 128):
        """ Send channelized data from the TPM """
        self.board["%s.lmc_gen.channelized_pkt_length" % self._device_name] = number_of_samples - 1
        self.board["%s.lmc_gen.request.channelized_data" % self._device_name] = 0x1

    def send_channelised_data_continuous(self, channel_id, number_of_samples = 128):
        """ Continuously send channelised data from a single channel
        :param channel_id: Channel ID
        """
        self.board["%s.lmc_gen.single_channel_mode.enable" % self._device_name] = 1
        self.board["%s.lmc_gen.single_channel_mode.id" % self._device_name] = channel_id
        self.board["%s.lmc_gen.channelized_pkt_length" % self._device_name] = number_of_samples - 1
        self.board["%s.lmc_gen.request.channelized_data" % self._device_name] = 0x1

    def stop_channelised_data_continuous(self):
        """ Stop sending channelised data """
        self.board["%s.lmc_gen.single_channel_mode.enable" % self._device_name] = 0

    def send_beam_data(self):
        """ Send beam data from the TPM """
        self.board["%s.lmc_gen.request.beamformed_data" % self._device_name] = 0x1

    def send_csp_data(self, samples_per_packet, number_of_samples):
        """ Send CSP data
        :param samples_per_packet: Number of samples in a packet
        :param number_of_samples: Total number of samples to send
        :return:
        """
        self.board['%s.csp_gen.trigger' % self._device_name]    = 0x0 # Reset trigger
        self.board['%s.csp_gen.tlast_mask' % self._device_name] = samples_per_packet - 1
        self.board['%s.csp_gen.pkt_num' % self._device_name]    = number_of_samples - 1
        self.board['%s.csp_gen.trigger' % self._device_name]    = 0x1

    #######################################################################################
    def download_beamforming_weights(self, weights, antenna):
        """ Apply beamforming weights
        :param weights: Weights array
        :param antenna: Antenna ID
        """
        self.board["%s.beamf.ch%02dcoeff" % (self._device_name, antenna)] = weights

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

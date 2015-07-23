__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import *
import logging


class TpmAdc(FirmwareBlock):
    """ TpmAdc tests class """

    @compatibleboards(BoardMake.TpmBoard)
    @friendlyname('tpm_adc')
    @maxinstances(16)
    def __init__(self, board, **kwargs):
        """ TpmAdc initialiser
        :param board: Pointer to board instance
        """
        super(TpmAdc, self).__init__(board)

        if 'adc_id' not in kwargs.keys():
            raise PluginError("TpmAdc: adc_id required")
        self._adc_id = kwargs['adc_id']

    #######################################################################################

    def adc_single_start(self):
        """!brief This function performs the ADC configuration and initialization procedure as implemented in ADI demo.

        @param self._adc_id -- int -- ADC SPI index, legal value with ADI FMC are 0x1 and 0x2
        @param bit -- int -- Sample bit width, supported value are 8,14
        """

        self.board[(self._adc_id, 0x0)] = 0x1

        do_until_eq(lambda : self.board[(self._adc_id, 0x0)] & 0x1, 0, ms_retry=100, s_timeout=10)


        self.board[(self._adc_id, 0x18)] =  0x44  # input buffer current 3.0X
        self.board[(self._adc_id, 0x120)] = 0x0  # sysref
        self.board[(self._adc_id, 0x550)] = 0x00
        self.board[(self._adc_id, 0x573)] = 0x00

        self.board[(self._adc_id, 0x571)] = 0x15
        self.board[(self._adc_id, 0x572)] = 0x10  # SYNC CMOS level

        self.board[(self._adc_id, 0x58b)] = 0x81
        self.board[(self._adc_id, 0x58d)] = 0x1f

        self.board[(self._adc_id, 0x58f)] = 0x7
        self.board[(self._adc_id, 0x590)] = 0x27
        self.board[(self._adc_id, 0x570)] = 0x48
        self.board[(self._adc_id, 0x58b)] = 0x81
        print "0x58b is " + str(self.board[(self._adc_id, 0x58b)])
        self.board[(self._adc_id, 0x590)] = 0x27

        # Lane remap
        self.board[(self._adc_id, 0x5b2)] = 0x00
        self.board[(self._adc_id, 0x5b3)] = 0x01
        self.board[(self._adc_id, 0x5b5)] = 0x00
        self.board[(self._adc_id, 0x5b6)] = 0x01
        self.board[(self._adc_id, 0x5b0)] = 0xFA  # xTPM unused lane power down

        self.board[(self._adc_id, 0x571)] = 0x14

        if self.board[(self._adc_id, 0x58b)] != 0x81:  # jesd lane number
            raise PluginError("TpmAdc: Number of lane is not correct")
        if self.board[(self._adc_id, 0x58c)] != 0:  # octets per frame
            raise PluginError("TpmAdc: Number of octets per frame is not correct")
        if self.board[(self._adc_id, 0x58d)] != 0x1f:  # frames per multiframe
            raise PluginError("TpmAdc: Number of frame per multifram is not correct")
        if self.board[(self._adc_id, 0x58e)] != 1:  # virtual converters
            raise PluginError("TpmAdc: Number of virtual converters is not correct")

        print "ADC " + str(self._adc_id) + " configured!"

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

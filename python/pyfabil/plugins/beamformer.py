__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
import logging

class UniBoardBeamformer(FirmwareBlock):
    """ FirmwareBlock tests class """

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_beamformer')
    @maxinstances(1)
    def __init__(self, board):
        """ FirmwareTest initialiser
        :param board: Pointer to board instance
        :return: Nothing
        """
        super(UniBoardBeamformer, self).__init__(board)

    def initialise(self):
        """ Initialise FirmwareTest
        :param kwargs:
        """

        logging.info("UniBoardBeamformer has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("UniBoardBeamformer : Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("UniBoardBeamformer : Cleaning up")
        return True
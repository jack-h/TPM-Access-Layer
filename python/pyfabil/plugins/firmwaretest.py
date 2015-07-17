from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
import logging

class FirmwareTest(FirmwareBlock):
    """ FirmwareBlock tests class """

    @compatibleboards(BoardMake.TpmBoard)
    @friendlyname('firmware_tesst')
    @maxinstances(2)
    def __init__(self, board):
        """ FirmwareTest initialiser
        :param board: Pointer to board instance
        :return: Nothing
        """
        super(FirmwareTest, self).__init__(board)

    def initialise(self, **kwargs):
        """ Initialise FirmwareTest
        :param kwargs:
        """
        if len(kwargs) == 0:
            raise PluginError("FirmwareTest initialiser requires some arguments")

        #print kwargs

        logging.info("FirmwareTest has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("FirmwareTest: Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("FirmwareTest: Cleaning up")
        return True

    @validstates(BoardState.All)
    def read_date_code(self):
        """ Test method
        :return: None
        """
        return self.board.read_register('board.regfile.date_code')

    @validstates(BoardState.All)
    def write_date_code(self, value):
        """ Test method
        :param value: Value to write to date_code
        :return: None
        """
        return self.board.write_register('board.regfile.date_code', value)
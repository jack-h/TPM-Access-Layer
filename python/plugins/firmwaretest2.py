from firmwareblock import FirmwareBlock
from firmwaretest import FirmwareTest
from definitions import *
import logging

class FirmwareTest2(FirmwareBlock):
    """ FirmwareBlock test class """

    @compatibleboards(BoardMake.TpmBoard)
    @friendlyname('firmware_test2')
    def __init__(self, board):
        """ FirmwareTest initialiser
        :param board: Pointer to board instance
        :return: Nothing
        """
        super(FirmwareTest2, self).__init__(board)

        self._test = FirmwareTest(board)

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
        return self.board.read_register(Device.Board, 'regfile.date_code')

    @validstates(BoardState.All)
    def write_date_code(self, value):
        """ Test method
        :param value: Value to write to date_code
        :return: None
        """
        return self.board.write_register(Device.Board, 'regfile.date_code', value)

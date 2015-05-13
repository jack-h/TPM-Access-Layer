from firmwareblock import FirmwareBlock
from definitions import *
import logging

class FirmwareTest(FirmwareBlock):
    """ FirmwareBlock test class """

    @compatibleboards(BoardMake.TpmBoard)
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

        print kwargs

        logging.info("FirmwareTest has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        print "Checking status"
        return Status.OK

    def test(self):
        """ Test firmware
        :return: Success or Failure
        """
        print "Testing firmware"
        return True

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        print "Performed clean_up"
        return True

    @validstates(BoardState.All)
    def read_date_code(self):
        """ Test method
        :return: None
        """
        return self.read_register(Device.Board, 'regfile.date_code')

    @validstates(BoardState.All)
    def write_date_code(self, value):
        """ Test method
        :param value: Value to write to date_code
        :return: None
        """
        return self.write_register(Device.Board, 'regfile.date_code', value)
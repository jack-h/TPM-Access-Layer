from firmwareblock import FirmwareBlock
from definitions import *

class FirmwareTest(FirmwareBlock):
    """ FirmwareBlock test class """

    @compatible_boards(BoardMake.TpmBoard)
    def __init__(self, board):
        """ FirmwareTest initialiser
        :param board: Pointer to board instance
        :return: Nothing
        """
        super(FirmwareTest, self).__init__(board)

    def initialise(self, **kwargs):
        """ Initialise FirmwareTest
        :return: Success
        """
        print "FirmwareTest has been initialised"
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        print "Checking status"
        return True

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

    @valid_states(BoardState.All)
    def read_date_code(self):
        """ Test method
        :return: None
        """
        return self.readRegister(Device.Board, 'regfile.date_code')

    @valid_states(BoardState.All)
    def write_date_code(self, value):
        """ Test method
        :param value: Value to write to date_code
        :return: None
        """
        return self.writeRegister(Device.Board, 'regfile.date_code', value)
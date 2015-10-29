from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
import logging

class c2cTest(FirmwareBlock):
    """ FirmwareBlock tests class """

    @compatibleboards(BoardMake.TpmBoard)
    @friendlyname('c2c_test')
    def __init__(self, board):
        """ c2cTest initialiser
        :param board: Pointer to board instance
        :return: Nothing
        """
        super(c2cTest, self).__init__(board)

    def initialise(self, **kwargs):
        """ Initialise c2cTest
        :param kwargs:
        """
        if len(kwargs) == 0:
            raise PluginError("c2cTest initialiser requires some arguments")

        #print kwargs

        logging.info("c2cTest has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("c2cTest: Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("c2cTest: Cleaning up")
        return True

    @validstates(BoardState.All)
    def start(self,num):
        """ Test method
        :return: None
        """
        reg = self.board.find_register('size1024b')[0]['name']
        for n in range(num):
            self.board.write_register(reg,n)
            rd = self.board.read_register(reg)
            if rd != n:
               print "c2c test error!"
               print "Expected data:",str(n)
               print "Received data:",str(rd)
               return Error.Failure
        print "c2c test success!"
        return Error.Success

from math import ceil
import re
from pyfabil.base.utils import convert_uint_to_string

__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
import logging


class TpmFirmwareInformation(FirmwareBlock):
    """ FirmwareBlock tests class """

    @compatibleboards(BoardMake.TpmBoard)
    @friendlyname('tpm_firmware_information')
    @maxinstances(2)
    def __init__(self, board, **kwargs):
        """ TpmPll initialiser
        :param board: Pointer to board instance
        """
        super(TpmFirmwareInformation, self).__init__(board)

        if 'device' not in kwargs.keys():
            raise PluginError("TpmFirmwareInformation: Require a device instance")
        device = kwargs['device']

        if device == Device.FPGA_1:
            self._register = 'board.info.fpga1_extended_info'
        elif device == Device.FPGA_2:
            self._register = 'board.info.fpga2_extended_info'
        else:
            raise PluginError("TpmFirmwareInformation: Invalid device %d" % device)

        # Check that register is available in register list
        #if not self.board.register_list.has_key(self._register):
        #    raise PluginError("TpmFirmwareInformation: CPLD XML file must be processed before plugin can be loaded")

        # Extended information regular expression
        self._search_string = re.compile(r'DESIGN: (?P<design>\S+)\s+BOARD: (?P<board>\S+)\s+MAJOR: (?P<major>\d+)\s+'
                                         r'MINOR: (?P<minor>\d+)\s+BUILD: (?P<build>\d+)\s+'
                                         r'UTC compile time: (?P<time>\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.[\d,\.]+)\s+'
                                         r'User: (?P<user>\S+)\s+Host: (?P<host>[a-zA-Z0-9_ -.]+).*', re.IGNORECASE)

        # Initialise information
        self._reset_information()


    #######################################################################################

    def update_information(self):
        """ Update firmware extended information
        :return:
        """

        # Read information data from board
        offset = self.board[self._register]
        size = self.board[offset]
        data = self.board.read_address(offset + 4, n = int(ceil(size / 4.0)))
        data = convert_uint_to_string(data)
        res = re.match(self._search_string, data)

        if res is None:
            self._reset_information()
        else:
            res = res.groupdict()
            self._major = int(res['major'])
            self._minor = int(res['minor'])
            self._host  = res['host']
            self._design = res['design']
            self._user = res['user']
            self._time = res['time']
            self._build = res['build']
            self._board = res['board']

    def _reset_information(self):
        """ Reset firmware information """
        self._major = -1
        self._minor = -1
        self._host  = ""
        self._design = ""
        self._user = ""
        self._time = ""
        self._build = ""
        self._board = ""

    def print_information(self):
        """ Print firmware information """
        print "Board: %s" % self._board
        print "Design: %s" % self._design
        print "Major version: %d" % self._major
        print "Minor version: %d" % self._minor
        print "Build: %s" % self._build
        print "UTC compile time: %s" % self._time
        print "User: %s" % self._user
        print "Host: %s" % self._host

    # Information getters
    def get_major_version(self): return self._major
    def get_minor_version(self): return self._minor
    def get_host(self):          return self._host
    def get_design(self):        return self._design
    def get_user(self):          return self._user
    def get_time(self):          return self._time
    def get_build(self):         return self._build
    def get_board(self):         return self._board

    ##################### Superclass method implementations #################################


    def initialise(self):
        """ Initialise TpmPll """
        logging.info("TpmFirmwareInformation has been initialised")
        return True


    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("TpmFirmwareInformation : Checking status")
        return Status.OK


    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("TpmFirmwareInformation : Cleaning up")
        return True

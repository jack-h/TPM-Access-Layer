__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import *
import logging

class TpmTenGCore(FirmwareBlock):
    """ TpmTenGCore plugin  """

    @compatibleboards(BoardMake.TpmBoard)
    @friendlyname('tpm_10g_core')
    @maxinstances(8)
    def __init__(self, board, **kwargs):
        """ TpmTenGCore initialiser
        :param board: Pointer to board instance
        """
        super(TpmTenGCore, self).__init__(board)

        if 'device' not in kwargs.keys():
            raise PluginError("TpmTenGCore: Require a node instance")
        self._device = kwargs['device']

        if 'core' not in kwargs.keys():
            raise PluginError("TpmTenGCore: core_id required")

        if self._device == Device.FPGA_1:
            self._device = 'fpga1'
        elif self._device == Device.FPGA_2:
            self._device = 'fpga2'
        else:
            raise PluginError("TpmTenGCore: Invalid device %s" % self._device)

        self._core = kwargs['core']

    #######################################################################################

    def set_src_ip(self, ip):
        """ Set source IP address
        :param ip: IP address
        """
        self.board['%s.udp_core_10g.core_%d_regname' % (self._device, self._core)]

    def set_dest_ip(self, ip):
        """ Set source IP address
        :param ip: IP address
        """
        self.board['']


    def set_src_port(self, ip):
        """ Set source IP address
        :param ip: IP address
        """
        self.board['']


    def set_dest_port(self, ip):
        """ Set source IP address
        :param ip: IP address
        """
        self.board['']


    ##################### Superclass method implementations #################################

    def initialise(self):
        """ Initialise TpmTenGCore """
        logging.info("TpmTenGCore has been initialised")
        return True


    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("TpmTenGCore : Checking status")
        return Status.OK


    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("TpmTenGCore : Cleaning up")
        return True

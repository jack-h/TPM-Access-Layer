import socket

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

    def initialise_core(self):
        """ Initialise 10G core """

        # Reset core
        self.board['%s.regfile.reset.eth10g_rst' % self._device] = 0x1
        self.board['%s.regfile.reset.eth10g_rst' % self._device] = 0x0

        # Packet split size: 1025
        self.board['%s.udp_core%d.udp_core_top_udp_core_config_packet_split_size'
                    % (self._device, self._core)] = 0x00000401

        # Disabling header/trailer insert
        self.board['%s.udp_core%d.udp_core_top_udp_core_config_hdr_tlr_inserter'
                    % (self._device, self._core)] = 0x0000F300

        # Packet Length and IP Count Values
        self.board['%s.udp_core%d.udp_core_top_udp_core_config_ip_v4_header_1'
                    % (self._device, self._core)] = 0xDB00001C

        # UDP length: 0x0008
        self.board['%s.udp_core%d.udp_core_top_udp_core_config_udp_length'
                    % (self._device, self._core)] = 0x00000008

        # Enabling Inter-Frame Gap
        self.board['%s.udp_core%d.udp_core_top_udp_core_config_inter_gap_value'
                    % (self._device, self._core)] = 0x00000001
        self.board['%s.udp_core%d.udp_core_top_udp_core_config_control'
                    % (self._device, self._core)] = 0x00000041

        # Configure TX formatter
        self.board['%s.udp_core%d.spead_formatter_control'
                    % (self._device, self._core)] = 0x20001000
        self.board['%s.udp_core%d.int_gen_spead_formatter_control'
                    % (self._device, self._core)] = 0x20001000

        # Frame generator
        self.board['%s.udp_core%d.frame_generator_control'
                    % (self._device, self._core)] = 0x0

    def set_src_mac(self, mac):
        """ Set source MAC address
        :param mac: MAC address
        """
        self.board['%s.udp_core%d.udp_core_top_udp_core_config_src_mac_addr_lower'
                    % (self._device, self._core)] = mac & 0xFFFFFFFF
        self.board['%s.udp_core%d.udp_core_top_udp_core_config_src_mac_addr_upper'
                    % (self._device, self._core)] = (mac >> 32) & 0xFFFFFFFF

    def set_dst_mac(self, mac):
        """ Set destination MAC address
        :param mac: MAC address
        """
        self.board['%s.udp_core%d.udp_core_top_udp_core_config_dst_mac_addr_lower'
                    % (self._device, self._core)] = mac & 0xFFFFFFFF
        self.board['%s.udp_core%d.udp_core_top_udp_core_config_dst_mac_addr_upper'
                    % (self._device, self._core)] = (mac >> 32) & 0xFFFFFFFF

    def set_src_ip(self, ip):
        """ Set source IP address
        :param ip: IP address
        """
        try:
            ip = struct.unpack("!L", socket.inet_aton(ip))[0]
            self.board['%s.udp_core%d.udp_core_top_udp_core_config_udp_src_ip_addr'
                % (self._device, self._core)] = ip
        except:
            raise PluginError("Tpm10GCore: Could not set source IP")

    def set_dst_ip(self, ip):
        """ Set source IP address
        :param ip: IP address
        """
        try:
            ip = struct.unpack("!L", socket.inet_aton(ip))[0]
            self.board['%s.udp_core%d.udp_core_top_udp_core_config_udp_dst_ip_addr'
                % (self._device, self._core)] = ip
        except:
            raise PluginError("Tpm10GCore: Could not set source IP")


    def set_src_port(self, port):
        """ Set source IP address
        :param port: Port
        """
       # self.board['%s.udp_core%d.udp_core_top.udp_core_config_udp_ports.udp_src_port'
       #             % (self._device, self._core)] = port
        if self._device == "fpga1":
            self.board[0x30102c] = (self.board[0x30102c] & 0xFFFF0000) | port
        else:
            self.board[0x1030102c] = (self.board[0x1030102c] & 0xFFFF0000) | port

    def set_dst_port(self, port):
        """ Set source IP address
        :param port: Port
        """
        #self.board['%s.udp_core%d.udp_core_top.udp_core_config_udp_ports.udp_dst_port'
        #            % (self._device, self._core)] = port
        if self._device == "fpga1":
            self.board[0x30102c] = (self.board[0x30102c] & 0xFFFF) | port << 16
        else:
            self.board[0x1030102c] = (self.board[0x1030102c] & 0xFFFF) | port << 16

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

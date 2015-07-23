__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import *
import logging


class TpmPll(FirmwareBlock):
    """ FirmwareBlock tests class """

    @compatibleboards(BoardMake.TpmBoard)
    @friendlyname('tpm_pll')
    @maxinstances(1)
    def __init__(self, board, **kwargs):
        """ TpmPll initialiser
        :param board: Pointer to board instance
        """
        super(TpmPll, self).__init__(board)

        self._board_type = kwargs.get('board_type', 'XTPM')

        if self._board_type == "XTPM":
            self._pll_out_config = ["sysref_hstl",  # "sysref_hstl",
                                    "unused",       # "clk",
                                    "clk",          # "unused",
                                    "unused",       # "unused",
                                    "sysref_hstl",  # "sysref_hstl",
                                    "unused",       # "unused",
                                    "clk_div_4",    # "unused",
                                    "unused",       # "unused",
                                    "clk_div_4",    # "unused",
                                    "sysref",       # "unused",
                                    "sysref",       # "unused",
                                    "unused",       # "unused",
                                    "clk_div_4",    # "unused",
                                    "clk_div_4"]    # "unused",
        else:
            self._pll_out_config = ["clk_div_4",
                                    "clk_div_4",
                                    "sysref",
                                    "clk",
                                    "unused",
                                    "unused",
                                    "unused",
                                    "unused",
                                    "clk",
                                    "sysref",
                                    "unused",
                                    "unused",
                                    "unused",
                                    "sysref"]

    #######################################################################################

    def pll_out_set(self, idx):
        """ Set PLL out
        :param idx:
        :return:
        """

        type = self._pll_out_config[idx]
        if type == "clk":
            reg0 = 0x0
            reg1 = 0x0
            reg2 = 0x0
        elif type == "clk_div_4":
            reg0 = 0x0
            reg1 = 0x0
            reg2 = 0x3
        elif type == "sysref":
            reg0 = 0x40
            reg1 = 0x0
            reg2 = 0x0
        elif type == "sysref_hstl":
            reg0 = 0x40
            reg1 = 0x80
            reg2 = 0x0
        else:
            reg0 = 0x0
            reg1 = 0x0
            reg2 = 0x0

        return reg0, reg1, reg2

    def pll_start(self, freq):
        """!@brief This function performs the PLL initialization procedure as implemented in ADI demo.

        @param freq -- int -- PLL output frequency in MHz. Supported frequency are 700,800,1000 MHz
        """
        print "Setting PLL. Frequency is " + str(freq)
        if freq != 1000 and freq != 800 and freq != 700:
            print "Frequency " + str(freq) + " MHz is not currently supported."
            print "Switching to default frequency 700 MHz"
            freq = 700

        self.board['board.regfile.ctrl.ad9528_rst'] = 0
        time.sleep(1)
        self.board['board.regfile.ctrl.ad9528_rst'] = 1

        self.board[('pll', 0x0)] = 0x1
        do_until_eq(lambda : self.board[('pll', 0x0)] & 0x1, 0, ms_retry = 100, s_timeout = 10)
        self.board[('pll', 0xf)] = 0x1

        if self._board_type == "XTPM":
            self.board[('pll', 0x100)] = 0x1
            self.board[('pll', 0x102)] = 0x1
            self.board[('pll', 0x104)] = 0xA   # VCXO100MHz
            self.board[('pll', 0x106)] = 0x14  # VCXO100MHz ##mod
            self.board[('pll', 0x107)] = 0x13  # Not disable holdover

            old = 0
            if old == 1:
                self.board[('pll', 0x108)] = 0x10
            else:
                self.board[('pll', 0x100)] = 0x38 # VCXO100MHz ##mod  ##10MHZ: 0x38

            self.board[('pll', 0x109)] = 0x4

            if old == 1:
                self.board[('pll', 0x10A)] = 0x0
            else:
                self.board[('pll', 0x10A)] = 0x2  ###10MHZ: 0x2

        else:
            self.board[('pll', 0x100)] = 0x1
            self.board[('pll', 0x102)] = 0x1
            self.board[('pll', 0x104)] = 0x8
            self.board[('pll', 0x106)] = 0x14
            self.board[('pll', 0x107)] = 0x13
            self.board[('pll', 0x108)] = 0x2A
            self.board[('pll', 0x109)] = 0x4
            self.board[('pll', 0x10A)] = 0x0

        if self.board == "XTPM":
            self.board[('pll', 0x200)] = 0xE6

            if freq == 1000:
                self.board[('pll', 0x201)] = 0x10
                self.board[('pll', 0x202)] = 0x33
                self.board[('pll', 0x203)] = 0x10
                self.board[('pll', 0x204)] = 0x4 # M1
                self.board[('pll', 0x205)] = 0x2
                self.board[('pll', 0x207)] = 0x2
                self.board[('pll', 0x208)] = 0x9 # N2
            elif freq == 800:
                self.board[('pll', 0x201)] = 0x10
                self.board[('pll', 0x202)] = 0x33
                self.board[('pll', 0x203)] = 0x10
                self.board[('pll', 0x204)] = 0x5 # M1
                self.board[('pll', 0x205)] = 0x2
                self.board[('pll', 0x207)] = 0x2
                self.board[('pll', 0x208)] = 0x7 # N2
            elif freq == 700:
                self.board[('pll', 0x201)] = 0xC8
                self.board[('pll', 0x202)] = 0x33
                self.board[('pll', 0x203)] = 0x10
                self.board[('pll', 0x204)] = 0x5 # M1
                self.board[('pll', 0x205)] = 0x2
                self.board[('pll', 0x207)] = 0x2
                self.board[('pll', 0x208)] = 0x6 # N2
            else:
                raise PluginError("TpmPll: Frequency not supported")
        else:
            self.board[('pll', 0x200)] = 0xE6
            if freq == 1000:
                self.board[('pll', 0x201)] = 0x19
                self.board[('pll', 0x202)] = 0x13
                self.board[('pll', 0x203)] = 0x10
                self.board[('pll', 0x204)] = 0x4
                self.board[('pll', 0x205)] = 0x2
                self.board[('pll', 0x207)] = 0x2
                self.board[('pll', 0x208)] = 0x18
            elif freq == 800:
                self.board[('pll', 0x201)] = 0x46
                self.board[('pll', 0x202)] = 0x33
                self.board[('pll', 0x203)] = 0x10
                self.board[('pll', 0x204)] = 0x5
                self.board[('pll', 0x205)] = 0x2
                self.board[('pll', 0x207)] = 0x1
                self.board[('pll', 0x208)] = 0x4
            elif freq == 700:
                self.board[('pll', 0x201)] = 0xEB
                self.board[('pll', 0x202)] = 0x13
                self.board[('pll', 0x203)] = 0x10
                self.board[('pll', 0x204)] = 0x5
                self.board[('pll', 0x205)] = 0x2
                self.board[('pll', 0x207)] = 0x4
                self.board[('pll', 0x208)] = 0x22
            else:
                raise PluginError("TpmPll: Frequency not supported")

        # Setting PLL Outputs
        for n in range(14):
            reg0, reg1, reg2 = self.pll_out_set(n)
            self.board[('pll', 0x300 + 3 * n + 0)] = reg0
            self.board[('pll', 0x300 + 3 * n + 1)] = reg1
            self.board[('pll', 0x300 + 3 * n + 2)] = reg2

        # Setting SYSREF
        self.board[('pll', 0x400)] = 0x14
        self.board[('pll', 0x403)] = 0x96
        self.board[('pll', 0x500)] = 0x10

        pd = 0
        for c in range(14):
            if self._pll_out_config[c] == "unused":
                pd |= 2 ** c

        self.board[('pll', 0x501)] = pd & 0xFF
        self.board[('pll', 0x502)] = (pd & 0xFF00) >> 8

        for i in range(10):
            if self.board[('pll', 0xF)] == 0:
                break
            if i == 9:
                raise PluginError("TpmPll: ")
            time.sleep(1)

        self.board[('pll', 0x203)] = 0x10
        do_until_eq(lambda : self.board[('pll', 0xF)], 0, ms_retry = 100, s_timeout = 10)
        self.board[('pll', 0xF)] = 0x1

        self.board[('pll', 0x203)] = 0x11
        do_until_eq(lambda: self.board[('pll', 0xF)], 0, ms_retry = 100, s_timeout = 10)
        self.board[('pll', 0xF)] = 0x1

        self.board[('pll', 0x403)] = 0x97
        do_until_eq(lambda : self.board[('pll', 0xF)], 0, ms_retry = 100, s_timeout = 10)
        self.board[('pll', 0xF)] = 0x1

        self.board[('pll', 0x32A)] = 0x1
        do_until_eq(lambda : self.board[('pll', 0xF)], 0, ms_retry = 100, s_timeout = 10)
        self.board[('pll', 0xF)] = 0x1

        self.board[('pll', 0x32A)] = 0x0
        do_until_eq(lambda : self.board[('pll', 0xF)], 0, ms_retry = 100, s_timeout = 10)
        self.board[('pll', 0xF)] = 0x1

        self.board[('pll', 0x203)] = 0x10
        self.board[('pll', 0xF)] = 0x1
        self.board[('pll', 0x203)] = 0x11
        self.board[('pll', 0xF)] = 0x1

        do_until_eq(lambda : self.board[('pll', 0x509)] & 0x1, 0x0, ms_retry = 100, s_timeout = 10)

        self.board[('pll', 0x403)] = 0x97
        self.board[('pll', 0xF)] = 0x1

        self.board[('pll', 0x32A)] = 0x1
        self.board[('pll', 0xF)] = 0x1

        self.board[('pll', 0x32A)] = 0x0
        self.board[('pll', 0xF)] = 0x1

        while True:
            rd = self.board[('pll', 0x508)]
            print "register 0x508 " + hex(rd)
            print "register 0x509 " + hex(self.board[('pll', 0x509)])
            print hex(rd)
            if rd == 0xF2 or rd == 0xe7:
                print "PLL Locked!"
                break
            else:
                print "PLL not Locked!"

        return Error.Success

# def fpga_start(self, idx, input_list, enabled_list):
#     """!@brief This function starts the FPGA acquisition and data downloading through 1Gbit Ethernet
#     """
#     filter_list = []
#     for n in input_list:
#         if n in enabled_list:
#             filter_list.append(n)
#
#     disabled_input = 0xFFFF
#     for input in filter_list:
#         mask = 1 << input
#         disabled_input = disabled_input ^ mask
#
#     rmp.wr32(0x30000008, 0x0081);  # pwdn ADCs
#     rmp.wr32(0x30000010, 0x0000);  # 0x1 accende ADA
#     rmp.wr32(0x3000000C, 0x0);
#
#     rmp.wr32(0x00030400 + idx * 0x10000000, 0x8);  # bit per sample
#
#     # rmp.wr32(0x0000000C+idx*0x10000000, disabled_input);
#     rmp.wr32(0x0001F004 + idx * 0x10000000, disabled_input);
#     # rmp.wr32(0x00000004+idx*0x10000000, 0x1);#xTPM
#     rmp.wr32(0x00030404 + idx * 0x10000000, 0x1);  # xTPM
#     # rmp.wr32(0x00000008+idx*0x10000000, 0x0);
#     rmp.wr32(0x0001F000 + idx * 0x10000000, 0x0);
#     # rmp.wr32(0x00000008+idx*0x10000000, 0x1);
#     rmp.wr32(0x0001F000 + idx * 0x10000000, 0x1);
#
#     # time.sleep(2)
#
#     # setting default buffer configuration
#     for n in range(16):
#         rmp.wr32(0x00030000 + 4 * n, n);  # first lane
#         rmp.wr32(0x00030100 + 4 * n, n);  # last lane
#         rmp.wr32(0x00030200 + 4 * n, n);  # write mux
#     rmp.wr32(0x00030300, 0xFFFF);  # write mux we
#     rmp.wr32(0x00030304, 0);  # write mux we shift
#
#     # setting buffer configuration
#     nof_input = len(filter_list)
#     if self.board == "XTPM":
#         slot_per_input = 16 / nof_input
#     else:
#         slot_per_input = 8 / nof_input
#
#     k = 0
#     for n in sorted(filter_list):
#         rmp.wr32(0x00030000 + 4 * n, k);  # first lane
#         rmp.wr32(0x00030100 + 4 * n, k + (slot_per_input - 1));  # last lane
#         k += slot_per_input
#     for n in range(16):
#         if n / slot_per_input < len(filter_list):
#             rmp.wr32(0x00030200 + 4 * n, sorted(filter_list)[n / slot_per_input]);  # write mux
#     mask = 0
#     for n in range(nof_input):
#         mask = mask << slot_per_input
#         mask |= 0x1
#     rmp.wr32(0x00030300, mask);
#     rmp.wr32(0x00030304, 0);
#
#     # time.sleep(1)
#     # self.wr_adc("all",0x572,0x80);
#     # self.wr_adc("all",0x572,0xC0); #Force ILA and user data phase
#
#
# def fpga_stop(self):
#     """!@brief This function stops the FPGA acquisition and data downloading through 1Gbit Ethernet
#     """
#     # rmp.wr32(0x00000004, 0x0);
#     rmp.wr32(0x00030404, 0x0);
#     # rmp.wr32(0x10000004, 0x0);
#     # rmp.wr32(0x00000008, 0x0);
#     rmp.wr32(0x0001F000, 0x0);
#     # rmp.wr32(0x10000008, 0x0);
#     time.sleep(1)
#
#
# def write_tag_ram(self, tag):
#     print "Writing TAG ram..."
#     word = 0
#     for n in range(4096):
#         if n < len(tag):
#             word = (word >> 8) | (int(tag[n].encode("hex"), 16) << 24)
#         else:
#             word = (word >> 8) | (int(" ".encode("hex"), 16) << 24)
#         if n % 4 == 3:
#             rmp.wr32(0x00031000 + 4 * (n / 4), word)
#             word = 0
#
#
# def acq_start(self, freq, bit, input_list, ada):
#     """!@brief This function performs the start-up procedure of the whole system.
#
#     It configures PLL, ADCs and FPGA and starts the data download.
#
#     @param freq -- int -- PLL output frequency in MHz. Supported frequency are 700,800,1000 MHz
#     @param bit -- int -- Sample bit width, supported value are 8,14
#     """
#     if self.board == "XTPM":
#         enabled_adc = [0, 1, 2, 3, 4, 5, 6, 7]
#         fpga_num = 1
#         jesd_core_num = 2
#     else:
#         enabled_adc = [0, 1]
#         fpga_num = 1
#         jesd_core_num = 1
#     adc_per_fpga = len(enabled_adc) / fpga_num
#
#     self.fpga_stop()
#     # Configure PLL
#     self.pll_start(freq)
#     # Configure all ADC
#     for n in enabled_adc:
#         self.adc_start(n, bit)
#     for n in enabled_adc:
#         self.wr_adc(n, 0x3F, 0x80);  # disabling pwdn input pin
#     # Configure JESD core
#     for f in range(fpga_num):
#         for c in range(jesd_core_num):
#             self.jesd_core_start(f, c, bit)
#     # Start download
#     for f in range(fpga_num):
#         self.fpga_start(f, input_list, range(adc_per_fpga * 2 * f, adc_per_fpga * 2 * (f + 1)))
#
#     # time.sleep(1)
#
#     rmp.wr32(0x00030404 + 0 * 0x10000000, 0x0);
#     rmp.wr32(0x00030404 + 1 * 0x10000000, 0x0);
#
#     if ada == True:
#         rmp.wr32(0x30000008, 0x281)
#         rmp.wr32(0x30000010, 0x5)
#         print "ADAs powered on!"
#
#     time.sleep(1)
#     print "acq_start done!"
#

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

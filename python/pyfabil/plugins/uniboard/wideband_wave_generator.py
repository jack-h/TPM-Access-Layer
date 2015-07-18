__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import *
import logging

"""Peripheral diag_wg_wideband

   Register map:

    31             24 23             16 15              8 7               0  wi
   |-----------------|-----------------|-----------------|-----------------|
   |          nof_samples[15:0]        |       xxx       |   Mode[7:0]     |  0
   |-----------------------------------------------------------------------|
   |                xxx                |            Phase[15:0]            |  1
   |-----------------------------------------------------------------------|
   |x|                             Freq[30:0]                              |  2
   |-----------------------------------------------------------------------|
   |                xxx                |             Ampl[15:0]            |  3
   |-----------------------------------------------------------------------|

   Remark:
   . This diag_wg_wideband_reg also suits diag_wg. Hence no need to make a
     diag_wg_reg

"""

class UniBoardWBWaveGenerator(FirmwareBlock):
    """ FirmwareBlock tests class """

    # Control register
    c_mode_w        = 8
    c_mode_mask     = 2**c_mode_w - 1
    c_nofSamples_w  = 16  # >~ minimum data path block size
    c_nofSamples_bi = 16
    c_phase_w       = 16  # =  c_nofSamples_w
    c_freq_w        = 31  # >> c_nofSamples_w, determines the minimum frequency = Fs / 2**c_freq_w
    c_ampl_w        = 17  # Typically fit DSP multiply 18x18 element so use <= 17, to fit unsigned in 18 bit signed,
                         # = waveform data width-1 (sign bit) to be able to make a 1 LSBit amplitude sinus
    c_mode_off      = 0
    c_mode_calc     = 1
    c_mode_repeat   = 2
    c_mode_single   = 3

    c_ampl_norm     = 1.0  # Use this default amplitude norm = 1.0 when WG data width = WG waveform buffer data width,
                           # else use extra amplitude unit scaling by (WG data max)/(WG data max + 1)
    c_gain_w        = 1    # Normalized range [0 1>  maps to fixed point range [0:2**c_ampl_w>
                           # . use gain 2**0        = 1 to have fulle scale without clipping
                           # . use gain 2**c_gain_w > 1 to cause clipping
    c_ampl_unit     = 2.0**(c_ampl_w-c_gain_w)*c_ampl_norm  # = Full Scale range [-c_wg_full_scale +c_wg_full_scale] without clipping
    c_freq_unit     = 2.0**(c_freq_w)                       # = c_clk_freq = Fs (sample frequency), assuming one sinus waveform in the buffer
    c_phase_unit    = 2.0**(c_phase_w)/ 360.0               # = 1 degree

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_wb_wave_generator')
    @maxinstances(16)
    def __init__(self, board, **kwargs):
        """ UniBoardBsnSource initialiser
        :param board: Pointer to board instance
        """
        super(UniBoardWBWaveGenerator, self).__init__(board)

        # Check if instance ID is in arguments
        if 'instance_number' not in kwargs.keys():
            raise PluginError("UniBoardWBWaveGenerator: Instance number must be in arguments")
        self._instance_number = kwargs['instance_number']

        # Required register names
        self._wg_register = "REG_DIAG_WG_%d" % self._instance_number
        self._wg_ram      = "RAM_DIAG_WG_%d" % self._instance_number

        # Get list of nodes
        if 'nodes' not in kwargs.keys():
            raise PluginError("UniBoardNonBondedTr: List of nodes not specified")

        # Check if list of nodes are valid, and are all back-nodes
        self._nodes = self.board._get_nodes(kwargs['nodes'])
        if type(self._nodes) is not list:
            self._nodes = [self._nodes]

        # Check if registers are available on all nodes
        for node in self._nodes:
            fpga_number = self.board.device_to_fpga(node)
            register_str = "fpga%d.%s" % (fpga_number, self._wg_register)
            if register_str % () not in self.board.register_list.keys():
                raise PluginError("UniBoardNonBondedTr: Node %d does not have register %s" % (fpga_number, self._wg_register))

            register_str = "fpga%d.%s" % (fpga_number, self._wg_ram)
            if register_str % () not in self.board.register_list.keys():
                raise PluginError("UniBoardNonBondedTr: Node %d does not have register %s" % (fpga_number, self._wg_ram))

        self.fs          = 800000000
        self.max_samples = 1024
        self.samples     = 1024


    #######################################################################################

    def write_mode_off(self):
        """ Write mode off """
        # Preserve number of samples in mode word
        data = [(self.samples << self.c_nofSamples_bi) + self.c_mode_off]
        # Write the register data to the node(s) and log the access status
        self.board.write_register(self._wg_register, data, device = self._nodes)

    def write_mode_sinus(self):
        """ Write mode sinusoid """
        # Preserve number of samples in mode word
        data = [(self.samples << self.c_nofSamples_bi) + self.c_mode_calc]
        # Write the register data to the node(s) and log the access status
        self.board.write_register(self._wg_register, data, device = self._nodes)

    def write_mode_repeat(self):
        """ Write mode repeat """
        # Preserve number of samples in mode word
        data = [(self.samples << self.c_nofSamples_bi) + self.c_mode_repeat]
        # Write the register data to the node(s) and log the access status
        self.board.writeRegister(self._wg_register, data, device = self._nodes)

    def write_sinus_settings(self, phase = 0, frequency = 0.0625, amplitude = 1.0):
        """ Write sinusoid settings. Mode = off
        :param phase: phase offset in degrees so [0 .. 360]
        :param frequency: freq normalized to the sample frequency Fs so [0 .. 1], so typically <= 0.5,
                          e.g. freq = 1/16 yields Fs=800 MSps / 16 = 50 MHz sinus
        :param amplitude: amplitude normalized to full scale sinus [0 .. 1], using > 1.0 will clip the tops of the sinus
        """

        data = [(self.samples << self.c_nofSamples_bi) + self.c_mode_off, int(phase*self.c_phase_unit),
                int(frequency * self.c_freq_unit), int(amplitude * self.c_ampl_unit)]
        # Write the register data to the node(s) and log the access status
        self.board.write_register(self._wg_register, data, device = self._nodes)

    def read_settings(self):
        """ Read settings """
        # Get the register data from the node(s) and log the access status
        data = self.board.read_register(self._wg_register, n = 4, device = self._nodes)

        # Evaluate per node
        result = []
        for (node, status, node_data) in data:
            if status != self.board.ST_OK:
                result.append('X')
            else:
                print "Node %d" % node
                mode = node_data[0] & self.c_mode_mask
                print 'Mode          = %s'            %  self.mode_to_str(mode)
                print 'NofSamplesMax = %d'            %  self.max_samples
                print 'NofSamples    = %d'            % (node_data[0] >> self.c_nofSamples_bi)
                print 'Phase         = %.2f degrees' % (node_data[1] / self.c_phase_unit)
                print 'Freq          = %.2f MHz'     % (node_data[2] / self.c_freq_unit*self.fs / 10.0**6)
                print 'Ampl          = %.2f'         % (node_data[3] / self.c_ampl_unit)
                print
                result.append(node_data)
        return result

    def read_waveform_ram(self, n = None):
        """ Read waveform from RAM
        :param n: Number of samples
        :return: read data
        """
        if n in None:
            n = self.samples

        # If if required number of samples is too large
        if n > self.max_samples:
            n = self.max_samples

        # Get the memory data from the node(s)
        data = self.board.read_register(self._wg_register, n = n, device = self._nodes)

        # Return result
        return [node_data for (node, status, node_data) in data]

    def write_waveform_ram(self, data):
        """ Write waveform to RAM
        :param data: Data represening waveform
        """
        n = len(data)
        if n > self.max_samples:
            raise PluginError("Waveform is too large to store in RAM")

        # Write the memory data to the node(s) and log the access status
        self.board.write_register(self._wg_register, data[:n], device = self._nodes)

    def mode_to_str(self, mode):
        if mode == self.c_mode_off:
            return 'off'
        if mode == self.c_mode_calc:
            return 'calc'
        if mode == self.c_mode_repeat:
            return 'repeat'
        if mode == self.c_mode_single:
            return 'single'
        return 'Illegal'

    ##################### Superclass method implementations #################################

    def initialise(self):
        """ Initialise FirmwareTest """

        logging.info("UniBoardWBWaveGenerator has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("UniBoardWBWaveGenerator : Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("UniBoardWBWaveGenerator : Cleaning up")
        return True
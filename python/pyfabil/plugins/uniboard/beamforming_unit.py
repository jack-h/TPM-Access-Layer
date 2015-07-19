__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import largest, int_requantize
import logging

class UniBoardBeamformingUnit(FirmwareBlock):
    """ UniBoardBeamformingUnit tests class """

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_beamforming_unit')
    @maxinstances(16)
    def __init__(self, board, **kwargs):
        """ UniBoardBeamformingUnit initialiser
        :param board: Pointer to board instance
        """
        super(UniBoardBeamformingUnit, self).__init__(board)

        # List of required parameters which should be passed in kwargs
        required_parameters = ['nof_weights', 'nof_signal_paths', 'nof_input_streams']

        # Check if all required parameters were passed
        if len(set(required_parameters) - set(kwargs.keys())) > 0:
            raise PluginError("Insufficient parameters for UniBoardBeamformingUnit, missing: %s" % \
                              [str(x) for x in set(required_parameters) - set(kwargs.keys())])

        # All OK, add to class instance
        self._nof_weights       = kwargs['nof_weights']
        self._nof_signal_paths  = kwargs['nof_signal_paths']
        self._nof_input_streams = kwargs['nof_input_streams']
        self._stat_data_width   = kwargs.get('stat_data_width', 56)
        self._nof_regs_per_stat = kwargs.get('nof_regs_per_stat', 2)
        self._xst_enable        = kwargs.get('xst_enable', False)
        self._instance_number   = kwargs.get('instance_number', 0)

       # self._reg_address = 'REG_BF_OFFSETS'  # NOTE: Seems that this is not used anywhere here
        self._ram_address = 'RAM_BF_WEIGHTS'

        # Check if list of nodes are valid and all are front nodes
        self._nodes = self.board._get_nodes(kwargs['nodes'])
        for node in self._nodes:
            if self.board.nodes[self.board._device_node_map[node]]['type'] != 'F':
                raise PluginError("UniBoardBeamformingUnit: Specified node must be a front node")

        # Check if registers are available on all nodes
        for node in self._nodes:
            fpga_number = self.board.device_to_fpga(node)
         #   register_str = "fpga%d.%s" % (fpga_number, self._reg_address)
         #   if register_str not in self.board.register_list.keys():
         #       raise PluginError("UniBoardBeamformingUnit: Node %d does not have register %s" % (fpga_number, self._reg_address))

            register_str = "fpga%d.%s" % (fpga_number, self._ram_address)
            if register_str  not in self.board.register_list.keys():
                raise PluginError("UniBoardBeamformingUnit: Node %d does not have register %s" % (fpga_number, self._ram_address))


        # Quantization defintions as in bf_pkg.vhd and bf_unit.vhd
        self._in_dat_w      = 16
        self._in_weight_w   = 16
        self._sum_of_prod_w = 1
        self._sign_w        = 1
        self._unit_w        = self._in_dat_w + self._in_weight_w - self._sign_w  # skip double sign bit
        self._prod_w        = self._unit_w + self._sum_of_prod_w                 # keep bit for sum of products in complex multiply
        self._bst_gain_w    = 1
        self._out_gain_w    = -5
        self._bst_dat_w     = 16
        self._out_dat_w     = 8
        self._gain_w        = largest(self._bst_gain_w, self._out_gain_w)
        self._sum_w         = self._unit_w + self._gain_w
        self._bst_lsb_w     = self._unit_w + self._bst_gain_w - self._bst_dat_w   # number of LSbits to remove to get bst_dat
        self._out_lsb_w     = self._unit_w + self._out_gain_w - self._out_dat_w   # number of LSbits to remove to get out_dat

        # SS
        self._nof_signal_paths_per_stream = self._nof_signal_paths / self._nof_input_streams
        self.ss_wide = []
        for i in range(self._nof_input_streams):
            x = self.board.load_plugin("UniBoardSSWide", nof_select = self._nof_weights,
                                                         wb_factor = self._nof_signal_paths_per_stream,
                                                         instance_number = self._instance_number * self._nof_input_streams + i,
                                                         nodes = kwargs['nodes'])
            self.ss_wide.append(x)

        # Load ST Beamlet statistics plugin
        self.st = self.board.load_plugin("UniBoardBeamletStatistics", nof_stats = self._nof_weights,
                                         stat_data_width = self._stat_data_width, nof_regs_per_stat = self._nof_regs_per_stat,
                                         xst_enable = self._xst_enable, instance_number = self._instance_number,
                                         nodes = kwargs['nodes'])

    #########################################################################################

    def read_weights(self, signal_path_number = 0):
        if signal_path_number > self._nof_signal_paths:
            print 'read_weights: Signal path number is too high  (%d > %d)' % (signal_path_number, self._nof_signal_paths)
            signal_path_number = self._nof_signal_paths - 1

        # Get the weights from the node(s)
        addr_offset = self._instance_number * self._nof_signal_paths * self._nof_weights + signal_path_number * self._nof_weights
        data = self.board.read_register(self._ram_address, offset = addr_offset, n = self._nof_weights, device = self._nodes)
        return [node_data for (node, status, node_data) in data]

    def read_weight(self, signal_path_number=0, weight_number = 0):
        if signal_path_number > self._nof_signal_paths:
            print 'read_weights: Signal path number is too high  (%d > %d)' % (signal_path_number, self._nof_signal_paths)
            signal_path_number = self._nof_signal_paths - 1

        if weight_number > self._nof_weights - 1:
            print 'read_weight: Weight number is too high  (%d > %d)' % (weight_number, self._nof_weights)
            weight_number = self._nof_weights - 1

        # Get the weight from the node(s)
        addr_offset = self._instance_number * self._nof_signal_paths * self._nof_weights + \
                      signal_path_number * self._nof_weights + weight_number
        data = self.board.read_register(self._ram_address, offset = addr_offset, device = self._nodes)
        return [node_data for (node, status, node_data) in data]

    def write_weights(self, data, signal_path_number=0):
        n = len(data)
        if n > self._nof_weights:
            print 'write_weights: Number of weights is too high  (%d > %d). Will truncate' % (n, self._nof_weights)
        if signal_path_number > self._nof_signal_paths:
            print 'write_weights: Signal path number is too high  (%d > %d)' % (signal_path_number, self._nof_signal_paths)
            signal_path_number = self._nof_signal_paths - 1

        # Write the weights to the node(s)
        addr_offset = self._instance_number * self._nof_signal_paths * self._nof_weights + signal_path_number * self._nof_weights
        self.board.write_register(self._ram_address,  data[:self._nof_weights], offset = addr_offset, device = self._nodes)

    def write_weight(self, data, signal_path_number=0, weight_number=0):
        n = len(data)
        if n > 1:
            print 'write_weight: Number of weights is too high  (%d > 1). Will truncate' % n
        if signal_path_number > self._nof_signal_paths:
            print 'write_weights: Signal path number is too high  (%d > %d)' % (signal_path_number, self._nof_signal_paths)
            signal_path_number = self._nof_signal_paths - 1
        # Write the weight to the node(s)
        addr_offset = self._instance_number * self._nof_signal_paths * self._nof_weights + \
                      signal_path_number * self._nof_weights + weight_number
        self.board.writeRegister(self._ram_address, data, offset = addr_offset, device = self._nodes)

    @staticmethod
    def generate_weights(nof_weights, real_offset, imag_offset, weight_width):
        weights=[]
        for i in xrange(0, nof_weights):
            real = (i + real_offset) & (2**weight_width-1)
            imag = (i + imag_offset) & (2**weight_width-1)
            weights.append((imag << weight_width) + real)
        return weights

    def generate_weights_uniform(self, real, imag, weight_width):
        weights=[]
        for i in xrange(0, self._nof_weights):
            real &= 2 ** weight_width - 1
            imag &= 2 ** weight_width - 1
            weights.append((imag << weight_width) + real)
        return weights

    def calculate_beamlets_sum(self, input_data, selection, weights):
        # Perform ss_wide selection
        bfUnitData=[]
        for i in range(self._nof_input_streams):
            for j in range(self._nof_signal_paths_per_stream):
                bfUnitData.append(self.ss_wide[0].subband_select(input_data[i], selection[j]))

        # Calculate all beamlets
        beamlets=[]
        for i in xrange(0, self._nof_weights):
            beamlet = 0
            for j in xrange(0, self._nof_signal_paths):
                product = weights[j][i] * bfUnitData[j][i]
                beamlet += product
            beamlets.append(beamlet)
        return beamlets

    def quantize_beamlets_sum(self, beamlets, use_16b=True):
        for i in xrange(0, self._nof_weights):
            if use_16b:
                # Quantize the beamlets for 16 bit output that is used for the BST and the UDP offload via 1GbE to a PC
                realPart = int_requantize(inp = int(beamlets[i].real), inp_w = self._sum_w, outp_w = self._bst_dat_w,
                                          lsb_w = self._bst_lsb_w, lsb_round = True, msb_clip = False, gain_w = 0)
                imagPart = int_requantize(inp = int(beamlets[i].imag), inp_w = self._sum_w, outp_w = self._bst_dat_w,
                                          lsb_w = self._bst_lsb_w, lsb_round = True, msb_clip = False, gain_w = 0)
            else:
                # Quantize the beamlets for 8 bit output that is used for the UDP offload via 10GbE to the correlator
                realPart = int_requantize(inp = int(beamlets[i].real), inp_w = self._sum_w, outp_w = self._out_dat_w,
                                          lsb_w = self._out_lsb_w, lsb_round = True, msb_clip = False, gain_w = 0)
                imagPart = int_requantize(inp = int(beamlets[i].imag), inp_w = self._sum_w, outp_w = self._out_dat_w,
                                          lsb_w = self._out_lsb_w, lsb_round = True, msb_clip = False, gain_w = 0)
            beamlets[i]=complex(realPart, imagPart)
        return beamlets

    def calculate_beamlet_statistics(self, beamlets, nofIntegration):
        # Calculate beamlet statistics for nof_blocks_per_sync
        statisticsAccumulated = []
        statistics = []

        for i in xrange(0, self._nof_weights):
            statistic=beamlets[i] * beamlets[i].conjugate()
            statistics.append(statistic)

        # Calculate the integrated values
        for i in xrange(0, self._nof_weights):
            statisticsAccumulated.append(nofIntegration * statistics[i].real)

        return statisticsAccumulated

    def calculate_bf_unit_statistics(self, input_data, selection, weights, nof_integrations, use_16b = True):
        beamlets=self.calculate_beamlets_sum(input_data, selection, weights)
        beamlets=self.quantize_beamlets_sum(beamlets, use_16b)
        return self.calculate_beamlet_statistics(beamlets, nof_integrations)

    # Map method name for backwards compatibility
    def calculate_beamlets(self, input_data, selection, weights, weights_width, nof_integrations):
        return self.calculate_bf_unit_statistics(input_data, selection, weights, nof_integrations, use_16b=True)


    ##################### Superclass method implementations #################################

    def initialise(self):
        """ Initialise FirmwareTest
        :param kwargs:
        """

        logging.info("UniBoardBeamformingUnit has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("UniBoardBeamformingUnit : Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("UniBoardBeamformingUnit : Cleaning up")
        return True

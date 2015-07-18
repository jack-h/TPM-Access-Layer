__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import *
import logging

"""Peripheral aduh_quad

   Register map REG_ADC_QUAD:

   . Report the locked status for ADU-AB and CD
   . Report pattern verification result for each ADC [A,B,C,D]

    31             24 23             16 15              8 7               0  wi
   |-----------------|-----------------|-----------------|-----------------|
   |         xxx                              ab_stable & ab_locked = [1:0]|  0
   |-----------------------------------------------------------------------|
   |         xxx                              cd_stable & cd_locked = [1:0]|  1
   |-----------------------------------------------------------------------|
   |         xxx            a_verify_res_val[12]|   xxx   a_verify_res[8:0]|  2
   |-----------------------------------------------------------------------|
   |         xxx            b_verify_res_val[12]|   xxx   b_verify_res[8:0]|  3
   |-----------------------------------------------------------------------|
   |         xxx            c_verify_res_val[12]|   xxx   c_verify_res[8:0]|  4
   |-----------------------------------------------------------------------|
   |         xxx            d_verify_res_val[12]|   xxx   d_verify_res[8:0]|  5
   |-----------------------------------------------------------------------|

"""

class UniBoardAduhQuad(FirmwareBlock):
    """ UniBoardAduhQuad tests class """



    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_aduh_quad')
    @maxinstances(1)
    def __init__(self, board, **kwargs):
        """ UniBoardBsnSource initialiser
        :param board: Pointer to board instance
        """
        super(UniBoardAduhQuad, self).__init__(board)

        # Required register names
        self._reg_address = 'REG_ADC_QUAD'

        # Check if list of nodes are valid, and are all back-nodes
        self._nodes = self.board._get_nodes(kwargs['nodes'])
        for node in self._nodes:
            if self.board.nodes[self.board._device_node_map[node]]['type'] != 'B':
                raise PluginError("UniBoardAduhQuad: Specified node must be a back node")

        # Check if registers are available on all nodes
        for node in self._nodes:
            fpga_number = self.board.device_to_fpga(node)
            register_str = "fpga%d.%s" % (fpga_number, self._reg_address)
            if register_str % () not in self.board.register_list.keys():
                raise PluginError("UniBoardAduhQuad: Node %d does not have register %s" % (fpga_number, self._reg_address))

        self._nof_dp_phs_clk = 6    # number of dp_phs_clk that are available to find ADUH lock

    #######################################################################################

    # NOTE: This will need testing and re-writing
    def read_lock_status(self):
        # Get the register data from the node(s)
        data = self.board.read_register(self._reg_address, offset = 0, n = 2, device = self._nodes)

        # Evaluate per node
        result = []
        for (node, status, node_data) in data:

            adu = ['AB', 'CD']  # ADUH_NOF_SP = 4
            res = []
            for i, ai_status in enumerate(node_data):
                extra_status   = (ai_status >> 2)
                raw_phs        = (ai_status >> 28) & 0xF
                clk_phs_select = (ai_status >> 24) & 0xF
                wb_cnt         = (ai_status >> 16) & 0xFF
                fifo_usedw     = (ai_status >> 8) & 0xFF
                phase          = (ai_status >> 4) & 0x1
                in_clk_locked  = (ai_status >> 6) & 0x3  # in_clk_stable, in_clk_detected

                if extra_status == 0:
                    status_str = ''
                else:
                    status_str = '(%3d, %3d, %3d,  %x, %x,   %x)' % (clk_phs_select, wb_cnt, fifo_usedw, raw_phs, phase, in_clk_locked)

                lock = ai_status & 3
                if lock == 1:
                    print 'ADUH-%s %s is locked but not stable (%x)' % (adu[i], status_str, lock)
                elif lock == 3:
                    print 'ADUH-%s %s is locked and stable (%x)' % (adu[i], status_str, lock)
                else:
                    print 'ADUH-%s %s is not locked (%x)' % (adu[i], status_str, lock)
                res.append(ai_status)
            result.append(res)
        return result

    def read_control(self):
        # Get the register data from the node(s)
        data = self.board.read_register(self._reg_address, offset = 6, n = 2, device = self._nodes)

        # Gather result
        result = []
        for (node, status, node_data) in data:
            res = []
            for i in len(node_data):
                res.append(node_data[i] & 0xFF)
            result.append(res)
        return result

    def write_control(self, adu_ab, adu_cd):
        # Write the memory data to the node(s) and log the access status
        self.board.write_register(self._reg_address, [adu_ab, adu_cd], offset = 6, device = self._nodes)

    def read_bist(self):
        """ Build in self test (aduh_verify.vhd and bn_capture/main.c for explanation) """

        ADUH_NOF_SP               = 4
        ADUH_ADC_BIST_VALID_MASK  = 0x1000
        ADUH_ADC_BIST_RESULT_MASK = 0x01FF

        # Get the register data from the node(s)
        data = self.board.read_register(self._reg_address, offset = 2, n = ADUH_NOF_SP, device = self._nodes)

        # Evaluate per node
        result = []
        for (node, status, node_data) in data:
            for sp in range(len(node_data)):
                 bist_val    = node_data[sp] & ADUH_ADC_BIST_VALID_MASK
                 bist_result = node_data[sp] & ADUH_ADC_BIST_RESULT_MASK
                 result.append((bist_val, bist_result))
        return result

    ##################### Superclass method implementations #################################

    def initialise(self):
        """ Initialise FirmwareTest """

        logging.info("UniBoardAduhQuad has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("UniBoardAduhQuad : Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("UniBoardAduhQuad : Cleaning up")
        return True
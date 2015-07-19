__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import *
import logging

"""Peripheral st_sst

   Register map:

    31             24 23             16 15              8 7               0  wi
   |-----------------|-----------------|-----------------|-----------------|
   |                           Statistic_0[31:0]                           |  0
   |-----------------------------------------------------------------------|
   |                           Statistic_0[63:32]                          |  1
   |-----------------------------------------------------------------------|
                                       |
                                       |
                                       |
   |-----------------------------------------------------------------------|
   |                          Statistic_255[31:0]                          |  510
   |-----------------------------------------------------------------------|
   |                          Statistic_255[63:32]                         |  511
   |-----------------------------------------------------------------------|

   Remark:

"""

class UniBoardSubbandStatistics(FirmwareBlock):
    """ UniBoardBeamletStatistics tests class """

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_subband_statistics')
    @maxinstances(16)
    def __init__(self, board, **kwargs):
        """ UniBoardSubbandStatistics initialiser
        :param board: Pointer to board instance
        """
        super(UniBoardSubbandStatistics, self).__init__(board)

        self._instance_number       = kwargs.get('instance_number', 0)
        self._xst_enable            = kwargs.get('xst_enable', False)
        self._instance_number       = kwargs.get('instance_number', 0)
        self._nof_stats             = kwargs.get('nof_stats', 256) if not self._xst_enable else\
                                                                    kwargs.get('nof_stats', 256) * c_nof_complex
        self._nof_regs_per_stat     = kwargs.get('nof_regs_per_stat', 2)
        self._nof_regs_per_instance = self._nof_regs_per_stat * self._nof_stats
        self._stat_data_width       = kwargs.get('stat_data_width', 56)
        self._reg_span = 2

        self._ram_address = 'RAM_ST_SST'
        self._reg_address = 'REG_ST_SST'

        # Check if list of nodes are valid and all are front nodes
        self._nodes = self.board._get_nodes(kwargs['nodes'])
        for node in self._nodes:
            if self.board.nodes[self.board._device_node_map[node]]['type'] != 'B':
                raise PluginError("UniBoardSubbandStatistics: Specified node must be a back node")

        # Check if registers are available on all nodes
        for node in self._nodes:
            fpga_number = self.board.device_to_fpga(node)
            # register_str = "fpga%d.%s" % (fpga_number, self._reg_address)
            # if register_str not in self.board.register_list.keys():
            #     raise PluginError("UniBoardSubbandStatistics: Node %d does not have register %s" % (fpga_number, self._reg_address))

            register_str = "fpga%d.%s" % (fpga_number, self._ram_address)
            if register_str not in self.board.register_list.keys():
                raise PluginError("UniBoardSubbandStatistics: Node %d does not have register %s" % (fpga_number, self._ram_address))


    #########################################################################################

    def read_and_verify_stats(self, reference = None):

        # Get the statistics from the node(s)
        addr_offset = self._instance_number * self._nof_regs_per_instance
        data = self.board.read_register(self._ram_address, offset = addr_offset, n = self._nof_regs_per_instance, device = self._nodes)
        reference = [] if reference is None else reference

        # Evaluate per node
        result = []
        for (node, status, node_data) in data:

            ni_stats = []
            ni_complex_stats=[]

            for k in xrange(0, self._nof_stats):
                temp =long((node_data[2*k+1] << c_word_w) + (node_data[2*k] & (c_word_mod-1)) & 2**self._stat_data_width-1)
                if temp & 2**(self._stat_data_width-1):
                    temp += -2 ** self._stat_data_width
                ni_stats.append(temp)
            print 'FN %d Read statistics (instance = %d)' % (node, self._instance_number)

            # make complex list and verify
            err_cnt = 0
            if self._xst_enable:
                for k in xrange(0, self._nof_stats/c_nof_complex):
                    ni_complex_stats.append(complex(ni_stats[k], ni_stats[k+self._nof_stats/c_nof_complex]))
                    if reference[k] != ni_complex_stats[k]:
                        err_cnt += 1
                        print 'Bf ='+ str(ni_complex_stats[k]) + 'Reference = ' + str(reference[k])
            else:
                for k in xrange(0, self._nof_stats):
                    ni_complex_stats.append(complex(ni_stats[k], 0))
                    if reference[k] != ni_complex_stats[k]:
                        err_cnt +=1
                        print 'Bf ='+ str(ni_complex_stats[k]) + 'Reference = ' + str(reference[k])
            if err_cnt > 0:
                print 'Verify statistics from instance = %d got %d errors' % (self._instance_number, err_cnt)
            else:
                print 'Verify statistics from instance = %d went OK' % self._instance_number
            result.append(ni_complex_stats)
        return result


    def read_stats(self, return_complex=True):
        # Get the statistics from the node(s)
        addr_offset = self._instance_number * self._nof_regs_per_instance
        data = self.board.read_register(self._ram_address, offset = addr_offset, n = self._nof_regs_per_instance, device = self._nodes)

        # Evaluate per node
        result = []
        for (node, status, node_data) in data:
            ni_stats = []
            ni_complex_stats=[]
            for k in xrange(0, self._nof_stats):
                temp =long((node_data[2*k+1] << c_word_w) + (node_data[2*k] & (c_word_mod-1)) & 2**self._stat_data_width-1)
                if temp & 2**(self._stat_data_width-1):
                    temp += -2 ** self._stat_data_width
                ni_stats.append(temp)
            print 'FN %d Read statistics (instance = %d)' % (node, self._instance_number)

            if self._xst_enable:
                for k in xrange(0, self._nof_stats/c_nof_complex):
                     ni_complex_stats.append(complex(ni_stats[k], ni_stats[k+self._nof_stats/c_nof_complex]))
            else:
                for k in xrange(0, self._nof_stats):
                     ni_complex_stats.append(complex(ni_stats[k], 0))
            if return_complex:
                result.append(ni_complex_stats)
            else:
                result.append(ni_stats)
        return result

    def read_treshold(self):
        # Write the treshold to the node(s)
        addr_offset = self._reg_span * self._instance_number
        data = self.board.read_register(self._reg_address, offset = addr_offset, n = 1, device = self._nodes)
        return [node_data for (node, status, node_data) in data]


    def write_treshold(self, data):
        # Write the treshold to the node(s)
        addr_offset = self._reg_span * self._instance_number
        self.board.writeRegister(self._reg_address, data, offset = addr_offset, device = self._nodes)

    def overwrite_stats(self, data):
        addr_offset = self._instance_number * self._nof_regs_per_instance
        self.board.write_register(self._ram_address, data[:self._nof_regs_per_instance],
                                  offset = addr_offset, device = self._nodes)

    ##################### Superclass method implementations #################################

    def initialise(self):
        """ Initialise FirmwareTest
        """
        logging.info("UniBoardSubbandStatistics has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("UniBoardSubbandStatistics : Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("UniBoardSubbandStatistics : Cleaning up")
        return True

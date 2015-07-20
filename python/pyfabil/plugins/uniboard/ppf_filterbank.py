__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.utils import flatten, concat_complex
from pyfabil.base.definitions import *
import logging

"""Peripheral fil_ppf_w

   This class defines methods to read and write the filtercoefficients
   of a wideband poly phase filter structure.

   The coefficients memory is organised as follows:

   Parameters in the example are:
   nof_taps  = 16
   wb_factor = 4 (resulting in 4 parallel paths)
   nof_bands = 1024

   ----------------------------------------
   | 256 coefs instance 0, tap 0,  path 0 |
   ----------------------------------------
   | 256 coefs instance 0, tap 1,  path 0 |
   ----------------------------------------
                       |
   ----------------------------------------
   | 256 coefs instance 0, tap 15, path 0 |
   ----------------------------------------
   | 256 coefs instance 0, tap 0,  path 1 |
   ----------------------------------------
                       |
                       |
                       |
   ----------------------------------------
   | 256 coefs instance 0, tap 15, path 3 |
   ----------------------------------------
   | 256 coefs instance 1, tap 0,  path 0 |
   ----------------------------------------
                       |
                       |
                       |
   ----------------------------------------
   | 256 coefs instance 3, tap 14, path 3 |
   ----------------------------------------
   | 256 coefs instance 3, tap 15, path 3 |
   ----------------------------------------

   Remark: It is recommended to use the read_coefs and write_coefs to transfer
           blocks of data that contain the coefficients for a single tap in
           a single path.

"""
class UniBoardPpfFilterbank(FirmwareBlock):
    """ FirmwareBlock tests class """

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_ppf_filterbank')
    @maxinstances(1)
    def __init__(self, board, **kwargs):
        """ UniBoardPpfFilterbank initialiser
        :param board: Pointer to board instance
        """
        super(UniBoardPpfFilterbank, self).__init__(board)

        # Process parameters
        self._nof_instances = kwargs.get('nof_instances', 4)
        self._nof_taps      = kwargs.get('nof_taps', 16)
        self._nof_bands     = kwargs.get('nof_bands', 1024)
        self._wb_factor     = kwargs.get('wb_factor', 4)
        self._nof_bands_per_parallel_path = self._nof_bands / self._wb_factor

        # Required register names
        self._ram_address = 'RAM_FIL_COEFS'

        # Check if list of nodes are valid
        self._nodes = self.board._get_nodes(kwargs['nodes'])
        for node in self._nodes:
            if self.board.nodes[self.board._device_node_map[node]]['type'] != 'B':
                raise PluginError("UniBoardPpfFilterbank: Specified node must be a back node")

        # Check if registers are available on all nodes
        for node in self._nodes:
            fpga_number = self.board.device_to_fpga(node)
            register_str = "fpga%d.%s" % (fpga_number, self._ram_address)
            if register_str not in self.board.register_list.keys():
                raise PluginError("UniBoardPpfFilterbank: Node %d does not have register %s" % (fpga_number, self._ram_address))

    #########################################################################################

    def read_coefs(self, instance_number = 0, tap_number = 0, path_number = 0, nof_coeffs = 256):
        if instance_number > self._nof_instances - 1:
            print 'read_coefs: instance number is too high (%d > %d)' % (instance_number, self._nof_instances)
            instance_number = self._nof_instances - 1

        if tap_number > self._nof_taps - 1:
            print 'read_coefs: Tap number is too high (%d > %d)' % (tap_number, self._nof_taps)
            tap_number = self._nof_taps - 1

        if path_number > self._wb_factor - 1:
            print 'read_coefs: Path number is too high (%d > %d)' % (path_number, self._wb_factor)
            path_number = self._wb_factor - 1

        # Get the coefficients from the node(s)
        # Determine the address offset:
        instance_offset = instance_number * self._nof_taps * self._nof_bands
        path_offset     = path_number * self._nof_taps * self._nof_bands_per_parallel_path
        tap_offset      = tap_number  * self._nof_bands_per_parallel_path
        addr_offset     = instance_offset + path_offset + tap_offset

        data = self.board.read_register(self._ram_address, offset = addr_offset, n = nof_coeffs, device = self._nodes)
        return [node_data for (node, status, node_data) in data]

    def write_coefs(self, data, instance_number = 0, tap_number = 0, path_number = 0):

        n = len(data)
        if n > self._nof_taps * self._nof_bands_per_parallel_path:
            raise PluginError('write_coefs: Number of coefs is too high  (%d > %d)' % (n, self._nof_taps * self._nof_bands))

        if instance_number > self._nof_instances - 1:
            print 'read_coefs: instance number is too high (%d > %d)' % (instance_number, self._nof_instances)
            instance_number = self._nof_instances - 1

        if tap_number > self._nof_taps \
                - 1:
            print 'read_coefs: Tap number is too high (%d > %d)' % (tap_number, self._nof_taps)
            tap_number = self._nof_taps - 1

        if path_number > self._wb_factor - 1:
            print 'read_coefs: Path number is too high (%d > %d)' % (path_number, self._wb_factor)
            path_number = self._wb_factor - 1

        # Write the coefficients to the node(s)
        # Determine the address offset:
        instance_offset = instance_number * self._nof_taps * self._nof_bands
        path_offset     = path_number*self._nof_taps * self._nof_bands_per_parallel_path
        tap_offset      = tap_number*self._nof_bands_per_parallel_path
        addr_offset     = instance_offset + path_offset + tap_offset

        self.board.write_register(self._ram_address,  data[:self._nof_bands_per_parallel_path],
                                  offset = addr_offset, device = self._nodes)

    ##################### Superclass method implementations #################################

    def initialise(self):
        """ Initialise FirmwareTest """
        logging.info("UniBoardPpfFilterbank has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("UniBoardPpfFilterbank : Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("UniBoardPpfFilterbank : Cleaning up")
        return True
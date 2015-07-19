__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import *
import logging

"""Peripheral ss_reorder

   Register map:

   The register map contains the selection words for the reorder function.
   The width(w) of each selection word is defined by ceil_log2(nof_inputs)*nof_outputs.

   Currently the maximum width w = 32.
   The depth of the selection buffer is defined by the frame_size.

    31             24 23             16 15              8 7               0  wi
   |-----------------|-----------------|-----------------|-----------------|
   |                         Select_buf_0[w-1:0]                           |  0
   |-----------------------------------------------------------------------|
   |                         Select_buf_1[w-1:0]                           |  1
   |-----------------------------------------------------------------------|
                                       |
                                       |
                                       |
   |-----------------------------------------------------------------------|
   |                        Select_buf_254[w-1:0]                          |  frame_size-2
   |-----------------------------------------------------------------------|
   |                        Select_buf_255[w-1:0]                          |  frame_size-1
   |-----------------------------------------------------------------------|

   Remark:

"""

class UniBoardSSReorder(FirmwareBlock):
    """ UniBoardSSReorder tests class """

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_ss_reorder')
    @maxinstances(1)
    def __init__(self, board, **kwargs):
        """ UniBoardSSReorder initialiser
        :param board: Pointer to board instance
        """
        super(UniBoardSSReorder, self).__init__(board)

        # Process arguments
        self._instance_number = kwargs.get('instance_number', 0)
        self._instance_name   = kwargs.get('instance_name', '')
        self._nof_outputs     = kwargs.get('nof_outputs', 8)
        self._nof_inputs      = kwargs.get('nof_inputs', 4)
        self._frame_size      = kwargs.get('frame_size', 128)

        # Required register names
        self._ram_address = 'RAM_SS_REORDER' if self._instance_name == '' else 'RAM_SS_REORDER_' + self._instance_name

        # Check if list of nodes are valid
        self._nodes = self.board._get_nodes(kwargs['nodes'])

        # Check if registers are available on all nodes
        for node in self._nodes:
            fpga_number = self.board.device_to_fpga(node)
            register_str = "fpga%d.%s" % (fpga_number, self._ram_address)
            if register_str not in self.board.register_list.keys():
                raise PluginError("UniBoardSSReorder: Node %d does not have register %s" % (fpga_number, self._ram_address))

        self._select_w         = ceil_log2(self._nof_inputs)
        self._select_word_w    = self._nof_outputs * self._select_w
        # The number of 32-bit registers that is required for one selection word.
        self._nof_regs_per_sel = 2**ceil_log2(ceil_div(self._select_word_w, c_word_w))
        self._address_span     = 2**ceil_log2(self._frame_size * self._nof_regs_per_sel)

    #######################################################################################

    def read_selects(self):
        # Get the selects from the node(s)
        addr_offset = 0 + self._instance_number * self._address_span
        data = self.board.read_register(self._ram_address, offset = addr_offset,
                                        n = self._frame_size * self._nof_regs_per_sel, device = self._nodes)
        # Evaluate results
        result = []
        for (node, status, node_data) in data:
            if self._select_word_w > c_word_w:
                for i in range(len(node_data) / self._nof_regs_per_sel):
                    word = CommonBits(0, c_word_w * self._nof_regs_per_sel)
                    for j in range(self._nof_regs_per_sel):
                        word[(j + 1) * c_word_w - 1 : j * c_word_w] = node_data[i * self._nof_regs_per_sel + j]
                    result.append(word)
            else:
                for i in range(len(node_data)):
                    result.append(data[i])
        return result

    def write_selects(self, data):
        # Check if number of selects is valid
        n = len(data)
        if n > self._frame_size:
            raise PluginError("UniBoardSSReorder: Number of selects too high (%d > %d)" % (n, self._frame_size))

        write_data = []
        if self._select_word_w > c_word_w:
            for i in range(n):
                word = CommonBits(data[i], c_word_w * self._nof_regs_per_sel)
                for j in range(self._nof_regs_per_sel):
                    write_data.append(word[(j + 1) * c_word_w - 1 : j * c_word_w])
        else:
            write_data = data

        # Write the selects to the node(s)
        addr_offset = 0 + self._instance_number * self._address_span
        self.board.write_register(self._ram_address, write_data, offset = addr_offset, device = self._nodes)
        print 'write_selects InstanceNr:' + str(self._instance_number)

    def create_reference(self, x_re_arr, x_im_arr, select_buf):
        # Create reference output based on settings of the select buffer
        ref_re_arr = []
        ref_im_arr = []

        for i in range(self._nof_outputs):
            ref_stream_re = []
            ref_stream_im = []
            for j in range(len(x_re_arr[0])):
                selector = CommonBits(select_buf[j], self._select_word_w)
                indexor  = selector[(i + 1) * self._select_w - 1 : i * self._select_w]
                ref_stream_re.append(x_re_arr[indexor][j])
                ref_stream_im.append(x_im_arr[indexor][j])
            ref_re_arr.append(ref_stream_re)
            ref_im_arr.append(ref_stream_im)
        return ref_re_arr, ref_im_arr

    def verify(self, ref_re_arr, ref_im_arr, dut_re_arr, dut_im_arr):
        # Verify the data
        err = 0
        for i in range(self._nof_outputs):
            for j in range(len(ref_re_arr[0])):
                if dut_re_arr[i][j] != ref_re_arr[i][j] or dut_im_arr[i][j] != ref_im_arr[i][j]:
                    err += 1
                    print 'Verify error: ref_re_arr[%d][%d] = %d , dut_re_arr[%d][%d] = %d' % (i, j, ref_re_arr[i][j], i, j, dut_re_arr[i][j])
                    print 'Verify error: ref_im_arr[%d][%d] = %d , dut_im_arr[%d][%d] = %d' % (i, j, ref_im_arr[i][j], i, j, dut_im_arr[i][j])
        print '>>> Number of errors: %d' % err

    def create_reference_and_verify(self, x_re_arr, x_im_arr, select_buf, dut_re_arr, dut_im_arr):
        (ref_re_arr, ref_im_arr) = self.create_reference(x_re_arr, x_im_arr, select_buf)
        self.verify(ref_re_arr, ref_im_arr, dut_re_arr, dut_im_arr)

    def create_selection_buf(self, sel_matrix_in):
        selection_buf = []
        for i in range(self._frame_size):
            select_value = CommonBits(0, self._select_word_w)
            for j in range(self._nof_outputs):
                select_value[(j + 1) * self._select_w-1 : j * self._select_w] = sel_matrix_in[i][j]
            selection_buf.append(long(select_value))
        return selection_buf

    ##################### Superclass method implementations #################################

    def initialise(self):
        """ Initialise FirmwareTest """

        logging.info("UniBoardSSReorder has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("UniBoardSSReorder : Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("UniBoardSSReorder : Cleaning up")
        return True
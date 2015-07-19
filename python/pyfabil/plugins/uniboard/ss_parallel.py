__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import *
import logging, copy

class UniBoardSSParallel(FirmwareBlock):
    """ UniBoardSSParallel tests class """

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_ss_parallel')
    @maxinstances(1)
    def __init__(self, board, **kwargs):
        """ UniBoardSSParallel initialiser
        :param board: Pointer to board instance
        """
        super(UniBoardSSParallel, self).__init__(board)

        # Process arguments
        self._instance_number = kwargs.get('instance_number', 0)
        self._nof_outputs     = kwargs.get('nof_outputs', 16)
        self._nof_inputs      = kwargs.get('nof_inputs', 8)
        self._frame_size_in   = kwargs.get('frame_size', 256)
        self._frame_size_out  = kwargs.get('frame_size', 96)
        self._nof_internals   = kwargs.get('nof_internals', 16)

        # Required register names
        # self._ram_address = 'RAM_SS_PARALLEL' NOTE: Doesn't seem to be used anywhere

        # Check if list of nodes are valid
        self._nodes = self.board._get_nodes(kwargs['nodes'])

        # Check if registers are available on all nodes
        # for node in self._nodes:
        #     fpga_number = self.board.device_to_fpga(node)
        #     register_str = "fpga%d.%s" % (fpga_number, self._ram_address)
        #     if register_str not in self.board.register_list.keys():
        #         raise PluginError("UniBoardSSParallel: Node %d does not have register %s" % (fpga_number, self._ram_address))

        # Load required plugins
        self.ss_reorder_in = self.board.load_plugin("UniBoardSSReorder", nof_inputs = self._nof_inputs,
                                                     nof_outputs = self._nof_internals, frame_size = self._frame_size_in,
                                                     instance_number = self._instance_number, nodes = kwargs['nodes'],
                                                     instance_name = 'IN')

        self.ss_reorder_out = self.board.load_plugin("UniBoardSSReorder", nof_inputs = self._nof_internals,
                                                     nof_outputs = self._nof_outputs, frame_size = self._frame_size_out,
                                                     instance_number = self._instance_number, nodes = kwargs['nodes'],
                                                     instance_name = 'OUT')

        self.ss_wide = self.board.load_plugin("UniBoardSSWide", nof_select = self._frame_size_out,
                                               wb_factor = self._nof_internals, instance_number = self._instance_number,
                                               nodes = kwargs['nodes'])

    #########################################################################################

    def create_reference_and_verify(self, x_re_arr, x_im_arr, reorder_in_buf, select_buf,
                                          reorder_out_buf, dut_re_arr, dut_im_arr):
        (ref_re_arr, ref_im_arr) = self.ss_reorder_in.create_reference(x_re_arr, x_im_arr, reorder_in_buf)
        sel_re_arr = []
        sel_im_arr = []
        for i in range(len(ref_re_arr)):
            sel_re_arr.append(self.ss_wide.subband_select(ref_re_arr[i], select_buf[(i+1)*len(ref_re_arr[0]):i*len(ref_re_arr[0])]))
            sel_im_arr.append(self.ss_wide.subband_select(ref_im_arr[i], select_buf[(i+1)*len(ref_im_arr[0]):i*len(ref_im_arr[0])]))
        self.ss_reorder_out.create_reference_and_verify(sel_re_arr, sel_im_arr, reorder_out_buf, dut_re_arr, dut_im_arr)

    def create_reference(self, x_re_arr, x_im_arr, Rin, Dsel, Rout):
        # Create the register settings for the reorder units
        reorder_in_buf  = self.ss_reorder_in.create_selection_buf(Rin)
        reorder_out_buf = self.ss_reorder_out.create_selection_buf(Rout)

        # Apply the input reordering:
        (ref_re_arr, ref_im_arr) = self.ss_reorder_in.create_reference(x_re_arr, x_im_arr, reorder_in_buf)

        # Apply the subband selection
        sel_re_arr = []
        sel_im_arr = []
        for i in range(self._nof_internals):
            sel_re_arr.append(self.ss_wide.subband_select(ref_re_arr[i], Dsel[i]))
            sel_im_arr.append(self.ss_wide.subband_select(ref_im_arr[i], Dsel[i]))

        # Apply the output reordering
        (res_re_arr, res_im_arr) = self.ss_reorder_out.create_reference(sel_re_arr, sel_im_arr, reorder_out_buf)

        return res_re_arr, res_im_arr

    def create_settings(self, Din, Dout):
        """  The aim is to locate every value in the Dout matrix in the Din matrix. When this location is
             found a suitable spot in the Dram matrix is to be found. Based on this Dram location settings
             for Rin, Dsel and Rout can be derived.  """

        result = True
        Rin    = self.init_array(self._nof_internals, self._frame_size_in,  0)
        Rout   = self.init_array(self._nof_outputs,   self._frame_size_out, 0)
        Dram   = self.init_array(self._nof_internals, self._frame_size_in,  [-1, -1])
        Dsel   = self.init_array(self._nof_internals, self._frame_size_out, -1)
        misses = 0

        for m in range(self._frame_size_out):
            print 'create_settings: processing column %d of %d)' % (m + 1, self._frame_size_out)
            for n in range(self._nof_outputs):
                # Check if the current Dout value is already placed in Dram. This is only the case when
                # Dout contains multiple copies of the same input value.(For instance when a subband is
                # selected multiple times). Current Dout value is located in Dram, using "locate_value".
                location = self.locate_value(Dout[n][m], Dram, 0, 0)
                if location != [-1, -1]:
                    # When the current value is found in Dram the according settings for Dsel and Rout
                    # [can be derived from the Dram location. The according Dsel location must hold the
                    # column of the found location, for the  according Rout setting the found row must
                    # be filled in.
                    Dsel[location[0]][m] = location[1]   # Assign Dsel with found column
                    Rout[n][m] = location[0]             # Assign Rout with found row
                else:
                    # When the current data is not found in Dram.  Check where the current data value from
                    # Dout is located in Din, using "locate_value".
                    location = self.locate_value(Dout[n][m], Din, 0, 0)
                    if location == [-1, -1]:
                        print "Value " + str(Dout[n][m]) + " not found in Din..."
                    else:
                        # Find a free and valid location (=row) in the Dram column that was returned.
                        # Method find_free_spot is used.
                        mem_row = self.find_free_spot(Dram, Dout[n][m], location[1], Dout, m, 0)

                        if mem_row != -1 :
                            Rin[mem_row][location[1]] = location[0]
                            Dsel[mem_row][m] = location[1]
                            Rout[n][m] = mem_row
                            #print "Set in Dram[" + str(mem_row) + "][" + str(location[1]) + "]"
                            #print ""
                        else:
                            print "Not Found"
                            misses += 1
                            for x in Dram:
                                print x
                                print ""

        Rin  = transpose(Rin)
        Rout = transpose(Rout)

        if misses == 0:
            [verify_result, Errout] = self.verify_settings(Din, Dout, Rin, Dsel, Rout)
            if verify_result:
                pass
            else:
                result = False
        else:
            result = False

        return (result, Rin, Dram, Dsel, Rout, Errout)

    def locate_value(self, value, matrix, start_row, start_col):
        """ Returns the coordinates of the last found instance of "value" in "matrix". It is possible to
            supply an offset for both row and column. The return value is a 2-element list: [row, column]
        """
        result = [-1,-1]
        i_order = rotate_list(range(0, len(matrix), 1), start_row)
        j_order = rotate_list(range(0, len(matrix[0]), 1), start_col)
        for i in i_order:
            for j in j_order:
                if value == matrix[i][j]:
                    result = [i,j]
        return result

    def find_free_spot(self, Dram, wr_data, DinCol, Dout, DoutCol, offset):
        """  Returns a row number of the Dram in which the wr_data can  an be stored. It does the following in a
             loop until succesful:
             1. Check for a row that is free
             2. Fill in the wr_data on the free spot and on the complementary spots(if available)
             3. Check if the column of Dout(in which wr_dat is located) can be made. This is done
                by checking if there is more than one value of the column in the same row. If that
                is the case, the selected row is not suitable.
             4. If not succesfull, go back to 1 and try another row.
        """
        result = -1
        row_nr = 0
        while row_nr < self._nof_internals :
            if Dram[row_nr][DinCol] == [-1,-1]:     # Check if location is still free
                Dram[row_nr][DinCol] = wr_data       # Place the data in the free cell
                # Check if all output columns can be made
                if self.multiple_more_than_one_equal(Dram[row_nr], Dout, wr_data) != True:
                    result = row_nr
                else:
                    Dram[row_nr][DinCol] = [-1, -1]  # Free the cell again
            if result == -1:
                row_nr +=1
            else:
                break
        return result

    @staticmethod
    def more_than_one_equal(list_a, list_b):
        """
        :return: True when there is more than one pair of equal numbers in list_a and
        list_b. List_a and List_b may contain doubles though. The following list shows examples:
            #   list_a         list_b           return
            #   0,1,2,3        0,4,5,6           True   (only 0 forms equal pair)
            #   0,1,2,3        0,0,5,6           True   (only 0 forms equal pair)
            #   0,1,2,3        0,1,5,6           False  (both 0 and 1 from equal pairs)
            #   0,1,2,3        0,1,5,6           False  (both 0 and 1 from equal pairs)
            #   0,1,-1,-1      1,2,3,4           True   (only 1 forms equal pair)
        """
        result = False
        cnt = 0
        checker = -1
        for i in list_a:
            if i == -1:
                break
            for j in list_b:
                if i == j:
                    if i != checker:  # The checker is used to detect double values in list_b (which is allowed!)
                        cnt += 1
                        if cnt > 1:
                            break
                    checker = i
            if cnt > 1:
                break
        if cnt > 1:
            result = True
        return result

    #--------------------------------------------------------------------------------
    #
    # Method: multiple_more_than_one_equal
    #
    # Returns .
    #--------------------------------------------------------------------------------
    def multiple_more_than_one_equal(self, list_a, matrix, data):
        """
        :return: True when one of the colums of the given matrix contains more than one
                 pair of equal numbers with list_a. It only checks the columns that contain the
                 value "data" that is given as a argument.
                 The method repeatedly calls more_than_one_equal
        """
        result = False
        for i in range(len(matrix[0])):
            column = self.column_to_list(matrix, i)
            if data in column:
                if self.more_than_one_equal(list_a, column) == True:
                    result = True
                    break

        return result

    def verify_settings(self, Din, Dout, Rin, Dsel, Rout):
        """
        :return: True when the provided output(Dout) matches the output of the python
                 model of ss_parallel, based on the provided input(Din) and the settings(Rin, Dsel and Rout)
        """
        result = True

        # Create seperate matrices for the real and imaginary part
        data_re = []
        for i in Din:
            row =[]
            for j in i:
                row.append(j[0])
            data_re.append(row)

        data_im = []
        for i in Din:
            row =[]
            for j in i:
                row.append(j[1])
            data_im.append(row)

        (res_re_arr, res_im_arr) = self.create_reference(data_re, data_im, Rin, Dsel, Rout)

        # Compose the Refout matrix that has the same format as Dout for comparisson.
        Refout = []
        for i in range(len(res_re_arr)):
            row =[]
            for j in range(len(res_re_arr[i])):
                row.append([res_re_arr[i][j], res_im_arr[i][j]])
            Refout.append(row)

        # Verify
        Errout = copy.deepcopy(Refout)
        errors = 0
        for i in range(len(Refout)):
            for j in range(len(Refout[i])):
                if Refout[i][j] != Dout[i][j]:
                   Errout[i][j] = "*"
                   errors += 1
                   result = False
                else:
                   Errout[i][j] = "-"

        return result, Errout

    @staticmethod
    def column_to_list(matrix, col):
        result = []
        for i in matrix:
            result.append(i[col])
        return result

    def init_array(self, rows, columns, init_value):
        result = []
        for i in range(rows):
            row = []
            for j in range(columns):
                row.append(init_value)
            result.append(row)
        return result

    def create_Din(self):
        result = []
        for i in range(self._nof_inputs):
            row = []
            for j in range(self._frame_size_in):
                row.append([i, j])
            result.append(row)

        return result

    ##################### Superclass method implementations #################################

    def initialise(self):
        """ Initialise FirmwareTest """

        logging.info("UniBoardSSParallel has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("UniBoardSSParallel : Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("UniBoardSSParallel : Cleaning up")
        return True
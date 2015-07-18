__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.utils import flatten, concat_complex
from pyfabil.base.definitions import *
import logging

# This is the 'master' beamformer plugin, which will create a beamformer
# unit for each back node on the UniBoard. It will also load other plugins
# including subband select reorder plugin instances

class UniBoardBeamformer(FirmwareBlock):
    """ FirmwareBlock tests class """

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_beamformer')
    @maxinstances(1)
    def __init__(self, board, **kwargs):
        """ UniBoardBeamformer initialiser
        :param board: Pointer to board instance
        """
        super(UniBoardBeamformer, self).__init__(board)

        # List of required parameters which should be passed in kwargs
        required_parameters = ['fft_size', 'nof_input_signals_per_bn', 'nof_wb_ffts', 'nof_iblets',
                               'nof_bf_units_per_node', 'nof_signal_paths', 'nof_weights',
                               'nof_subbands', 'nof_input_streams', 'in_weight_w', 'wb_factor', 'stat_data_w',
                               'stat_data_sz', 'nof_sp_per_input_stream', 'use_backplane']

        # Check if all required parameters were passed
        if len(set(required_parameters) - set(kwargs)) > 0:
            raise PluginError("Insufficient parameters for UniBoardBeamformer, missing: %s" % \
                              [str(x) for x in set(required_parameters) - set(kwargs)])

        # Save passed in kwargs as config
        self._config = kwargs

        self._sel_subbands = []       # List with the selected subbands = iBlets list
        self._nof_beamlets = []       # List that holds the number of beamlets to be made from every selected subband
        self._weights      = []       # Matrix holding the weights

        # Dimension definition for the subband selection
        self._nof_inputs     = self._config['nof_wb_ffts'] * self._config['wb_factor']                 #   8     The number of inputs
        self._nof_outputs    = self._config['nof_input_streams']                                       #  16     The number of outputs
        self._nof_internals  = self._config['nof_input_streams']                                       #  16
        self._frame_size_in  = self._config['fft_size'] / self._config['wb_factor']                    # 256     Number of samples in a frame at the input(between assertion of SOP and EOP)
        self._frame_size_out = self._config['nof_sp_per_input_stream'] * self._config['nof_subbands']  #  96     Number of samples in a frame at the output(between assertion of SOP and EOP)

        # Create a selection matrix based on specified rows and columns
        self._sel_matrix = SelMatrix(self._config, self._nof_outputs, self._frame_size_out)

        # Create subband select reorder plugin
        self._ss_par = self.board.load_plugin("UniBoardSSParallel", nodes = self.board.back_nodes, nof_inputs = self._nof_inputs,
                                              nof_internals = self._nof_internals, nof_outputs = self._nof_outputs,
                                              frame_size_in = self._frame_size_in, frame_size_out = self._frame_size_out)

        # Create Beamforming Units plugins
        for i in range(self.board.front_nodes):
            for j in kwargs['nof_bf_units_per_node']:
                self.board.load_plugin("UniBoardBeamformingUnit", nof_weights =  kwargs['nof_weights'],
                                        nof_signal_paths = kwargs['nof_signals_paths'], nof_input_streams = kwargs['nof_input_streams'],
                                        stat_data_width = kwargs['stat_data_w'], nof_regs_per_stat = kwargs['stat_data_sz'],
                                        xst_enable = True, instance_number = j, nodes = self.board.front_nodes)
        self._bf = self.board.uniboard_beamforming_units

    #########################################################################################

    def select_subbands(self, sel_subbands, nof_beamlets, write_settings = True):
        """ The desired subbands are mapped on the available iblets.
            The number of beamlets per iblet are stored.
            Settings for the ss_aparallel unit are derived, verified and written.  """

        # Update the object attributes
        self._sel_subbands = sel_subbands

        # The selected subbands are mapped in a matrix that represents Dout
        self._sel_matrix.map_subbands(sel_subbands)

        # The applied number of selected subbands are checked against the constraints/limitations of the Apertif Beamformer system.
        self._nof_beamlets = self._sel_matrix.check_nof_iblets(nof_beamlets)

        # Dout is extracted from the sel_matrix to which the selected subbands are mapped.
        Dout = self._sel_matrix.create_Dout()

        # The settings for ss_parallel are derived from Din and Dout.
        [result, Rin, Dram, Dsel, Rout, Errout] = self._ss_par.create_settings(self._ss_par.create_Din(), Dout)

        # Convert the returned settings to register settings fro the ss_parallel unit:
        reorder_in_buf  = self._ss_par.ssReorderIn.create_selection_buf(Rin)
        reorder_out_buf = self._ss_par.ssReorderOut.create_selection_buf(Rout)
        select_buf      = flatten(Dsel)

        # Replace -1 with 0
        for i in range(len(select_buf)):
            if select_buf[i] == -1:
                select_buf[i] = 0

        for i in range(len(reorder_in_buf)):
            if reorder_in_buf[i] == -1:
                reorder_in_buf[i] = 0

        for i in range(len(reorder_out_buf)):
            if reorder_out_buf[i] == -1:
                reorder_out_buf[i] = 0

        ## Create and write the selection buffers in the bf_units
        for i in range(len(self.board.front_nodes)):
            # Create selection line for one node
            select_buf_line = []
            for j in xrange(self._config['nof_subbands']):
                select_buf_line.append([j] * self._nof_beamlets[i * self._config['nof_subbands'] + j])

            select_buf_line = flatten(select_buf_line)

            # write selection lines to every bf_unit.
            bf_ss_wide_buf = []
            for k in range(self._config['nof_bf_units_per_node']):
                bf_select_buf = []
                for m in range(self._config['nof_sp_per_input_stream']):
                    next_line = []
                    for t in select_buf_line[k * self._config['nof_weights']:(k + 1) * self._config['nof_weights']]:
                        next_line.append(t + m * self._config['nof_subbands'])
                    bf_select_buf.append(next_line)
                bf_ss_wide_buf.append(bf_select_buf)
                if write_settings:
                    for n in range(self._config['nof_input_streams']):
                        self._bf[i*self._config['nof_bf_units_per_node']+k].ss_wide[n].write_selects(flatten(bf_select_buf))

        # Write the settings to the ss_parallel peripheral
        if write_settings:
            self._ss_par.ssReorderIn.write_selects(reorder_in_buf)
            self._ss_par.ssReorderOut.write_selects(reorder_out_buf)
            self._ss_par.ssWide.write_selects(select_buf)

        return reorder_in_buf, reorder_out_buf, Dsel, bf_ss_wide_buf

    #--------------------------------------------------------------------------------
    #
    # Method: setAllWeights
    #
    # Write the weights to the memories.
    #
    #   This requires a conversion from the weights[x][y][z]-format to
    #   the implementation format.
    #
    #   The weights[x][y][z] format is as follows:
    #
    #     x represents the Iblet-number ranging from 0-383
    #     y represents the Signalpath-number ranging from 0-63
    #     z represents the Beamlet-number ranging from 1-250 (peak) 42 (average)
    #       z is equal for all y's, but unique for every x.
    #
    #   The implementation format requires the weights to be written per bf_unit.
    #   Within a bf_unit the weights are stacked as follows:
    #
    #     sp0_w0      (Signalpath 0, Weight 0)
    #        |
    #     sp0_w255    (Signalpath 0, Weight 255)
    #     sp1_w0      (Signalpath 1, Weight 0)
    #        |
    #     sp1_w255    (Signalpath 1, Weight 255)
    #        |
    #        |
    #        |
    #     sp63_w0      (Signalpath 63, Weight 0)
    #        |
    #     sp63_w255    (Signalpath 63, Weight 255)
    #
    #     Note that the 256 weights are devided over the 6 subbands that each
    #     bf_unit processes.
    #
    #--------------------------------------------------------------------------------
    def convert_weights_format(self, weights):
        self._weights = weights
        nodes_list = []
        for k in range(len(self.board.front_nodes)):
            sp_list = []
            for j in range(self._config['nof_signal_paths']):
                beamlet_list = []
                for x in range(self._config['nof_subbands']):
                    for y in range(self._nof_beamlets[k * self._config['nof_subbands'] + x]):
                        beamlet_list.append(weights[k*self._config['nof_subbands'] + x][j][y])
                sp_list.append(beamlet_list)
            nodes_list.append(sp_list)

        return nodes_list

    def set_all_weights(self, weights):
        self._weights = weights

        nodes_list = self.convert_weights_format(weights)
        for k in range(len(self.board.front_nodes)):
            for j in range(self._config['nof_signal_paths']):
                for i in range(self._config['nof_bf_units_per_node']):
                    self._bf[k * self._config['nof_bf_units_per_node']+i].write_weights(
                        concat_complex(nodes_list[k][j][i * self._config['nof_weights']:(i + 1) * self._config['nof_weights']],
                                       self._config['in_weight_w']), j)

    ##################### Superclass method implementations #################################

    def initialise(self):
        """ Initialise FirmwareTest
        """
        logging.info("UniBoardBeamformer has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("UniBoardBeamformer : Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("UniBoardBeamformer : Cleaning up")
        return True

############################### Matrix and Cell Classes ###################################
class SelCell:

    def __init__(self, row_number = 0, column_number = 0):
        self.destFnNr      = row_number
        self.destBfUnitNr  = int((column_number % 24) / 6)
        self.destFifoId    = column_number % 6
        self.sp            = 0
        self.sb            = 0
        self.DinIndex      = 0

    @staticmethod
    def find_Dindex(sp, sb):
        col = 2 * (sb % 128) + (sp % 2)
        row = (sb / 128) + 4*(sp / 2)
        return [row, col]

class SelMatrix:
    """ Selection Matrix """

    def __init__(self, config, nof_rows = 16, nof_cols = 96):
        """ Class initialiser
        :param config: Dictionary holding configuration object passed to beamformer
        :param nof_rows: Number of rows
        :param nof_cols: Number of columns
        """
        self._nof_rows       = nof_rows
        self._nof_cols       = nof_cols
        self._config         = config
        self._cells          = []
        for i in range(nof_rows):
            cellRow = []
            for j in range(nof_cols):
                cellRow.append(SelCell(i,j))
            self._cells.append(cellRow)

    def map_subbands(self, subbands):
        if len(subbands) > self._config['nof_iblets']:
            raise PluginError("SelMatrix: Number of selected subbands is too high (%d > %d)" % (len(subbands), self._config['nof_iblets']))

        # System with the backplane connected
        sig_per_bn = self._config['nof_input_signals_per_bn']
        if self._config['use_backplane']:
            for i in range(sig_per_bn):
                h = 0
                for j in range(self._nof_rows):
                    for k in range(self._nof_cols / sig_per_bn):
                        self._cells[j][k + i * (self._nof_cols/sig_per_bn)].sb = subbands[h]
                        self._cells[j][k + i * (self._nof_cols/sig_per_bn)].sp = i
                        self._cells[j][k + i * (self._nof_cols/sig_per_bn)].DinIndex = self._cells[0][0].find_index(i, subbands[h])
                        h += 1

        # Single Uniboard system with MESH connections only.
        else:
            for i in range(sig_per_bn):  #4
                h = 0
                for j in range(self._config['nof_input_streams'] / sig_per_bn): # 16 / 4 = 4
                    for k in range(self._config['nof_subbands']):
                        self._cells[i + j * sig_per_bn][k].sb = subbands[h]
                        self._cells[i + j * sig_per_bn][k].sb = i
                        self._cells[i + j * sig_per_bn][k].DinIndex = self._cells[0][0].find_index(i, subbands[h])
                        h += 1

    def create_Dout(self):
        Dout = []
        for i in range(self._nof_rows):
            row = []
            for j in range(self._nof_cols):
                row.append(self._cells[i][j].DinIndex)
            Dout.append(row)

        return Dout

    def check_nof_iblets(self, iblets):
        result = iblets
        max_nof_iblets = self._config['nof_bf_units_per_node'] * self._config['nof_weights']
        min_nof_iblets = 0
        nof_subbands = self._config['nof_subbands']

        if len(iblets) != self._config['nof_iblets']:
            print 'check_iblets: Length of iblets list must be exactly %d  (%d != %d)' % \
                  (self._config['nof_iblets'], len(iblets), self._config['nof_iblets'])

        for i in range(self._config['nof_iblets'] / self._config['nof_subbands']):
            subtotal = 0
            for j in range(nof_subbands):
                if iblets[i * nof_subbands + j] > max_nof_iblets:
                    print 'check_iblets: Maximum number of iblets is %d  (%d != %d), truncating to %d' % \
                    (max_nof_iblets, iblets[i * nof_subbands + j], max_nof_iblets, max_nof_iblets)
                    result[i * nof_subbands + j] = max_nof_iblets

                if iblets[i * nof_subbands + j] < min_nof_iblets:
                    print 'check_iblets: Minimum number of iblets is %d  (%d != %d), truncating to %d' % \
                          (min_nof_iblets, iblets[i * nof_subbands + j], min_nof_iblets, min_nof_iblets)
                    result[i * nof_subbands + j] = min_nof_iblets

                subtotal += iblets[i * nof_subbands + j]

            if subtotal > max_nof_iblets:
                print 'check_iblets: Total number of 24-iblets %d (=%d) is too high. Should be equal or less than %d' % \
                      (i, subtotal, max_nof_iblets)
                print 'check_iblets: Total number of 24-iblets %d (=%d) is too high. Should be equal or less than %d' % \
                      (i, subtotal, max_nof_iblets)
                print 'check_iblets: Please reconsider the number of iblets.'
                print 'check_iblets: All modifications are reversed...'
                result = iblets
                break

            if subtotal < max_nof_iblets:
                print 'check_iblets: Total number of 24-iblets %d (=%d) is less than allowed.' % (i, subtotal)
                print 'check_iblets: Filling up the 24-iblets to %d, by changing iblet[%d] from %d to %d' % \
                      (max_nof_iblets, i * nof_subbands + nof_subbands - 1,
                       iblets[i * nof_subbands + nof_subbands - 1],
                       iblets[i * nof_subbands + nof_subbands - 1] + max_nof_iblets - subtotal)

                result[i * nof_subbands + nof_subbands - 1] = iblets[i * nof_subbands + nof_subbands - 1] + max_nof_iblets - subtotal

        return result
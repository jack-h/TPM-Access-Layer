__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
import logging

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
        if len(set(kwargs) - set(required_parameters)) > 0:
            raise PluginError("Insufficient parameters for UniBoardBeamformer, missing: %s" % \
                              [str(x) for x in set(kwargs) - set(required_parameters)])

        # Save passed in kwargs as config
        self._config = kwargs

        self.sel_subbands = []       # List with the selected subbands = iBlets list
        self.nof_beamlets = []       # List that holds the number of beamlets to be made from every selected subband
        self.weights      = []       # Matrix holding the weights

        # Dimension definition for the subband selection
        self.nof_inputs     = self._config['nof_wb_ffts'] * self._config['wb_factor']                 #   8     The number of inputs
        self.nof_outputs    = self._config['nof_input_streams']                                       #  16     The number of outputs
        self.nof_internals  = self._config['nof_input_streams']                                       #  16
        self.frame_size_in  = self._config['fft_size'] / self._config['wb_factor']                    # 256     Number of samples in a frame at the input(between assertion of SOP and EOP)
        self.frame_size_out = self._config['nof_sp_per_input_stream'] * self._config['nof_subbands']  #  96     Number of samples in a frame at the output(between assertion of SOP and EOP)

        # Create a selection matrix based on specified rows and columns
        self.sel_matrix = SelMatrix(self._config, self.nof_outputs, self.frame_size_out)

    #########################################################################################

    

    ##################### Superclass method implementations #################################

    def initialise(self):
        """ Initialise FirmwareTest
        :param kwargs:
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
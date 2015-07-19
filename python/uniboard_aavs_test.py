from pyfabil.tests.uniboard_aavs_test_plotting import *
from pyfabil.base.utils import *
from pyfabil import UniBoard
import time

#################################### Definitions ##################################

# START_VHDL_GENERICS
c_fft_size          =     1024  #  1024    Specifies the size of the FFT
c_nof_taps          =       16  #    16    The number of taps in de poly phase filter bank
c_wb_factor         =        4  #     4    The wideband factor
c_stat_data_w       =       56  #    56
c_stat_data_sz      =        2  #     2
c_nof_input_streams =       16  #    16
c_nof_subbands      =       96  #    96
c_nof_signal_paths  =       16  #    16
c_fft_out_dat_w     =       14  #    14
c_nof_weights       =      256  #   256
c_in_weight_w       =       16  #    16
c_nof_bf_units      =        4  #     4
# END_VHDL_GENERICS

c_coefs_input_file  ="../../../../Firmware/modules/Lofar/pfs/src/data/Coeffs16384Kaiser-quant.dat"
c_nof_coefs_in_file = 16384
c_downsample_factor = c_nof_coefs_in_file/(c_nof_taps*c_fft_size)

c_nof_wb_ffts              = 2           # The number of wideband FFTs. Each FFT processes two (real) signal paths.
c_nof_input_signals_per_bn = 4
c_nof_iblets               = 384
c_nof_sp_per_input_stream  = c_nof_signal_paths/c_nof_input_streams
c_blocks_per_sync          = 781250     # Samplefrequency/nof_samples_per_packet = 800Mhz/1024= 781250
c_clk_period               = 5  # ns
c_sample_clk_freq          = 800000000   # Sample clock frequency
c_bsn_period               = 1.0 * c_fft_size / c_sample_clk_freq
c_bsn_delay                = 5
c_bg_buf_size              = c_fft_size / c_wb_factor
c_stat_input_bits          = 16
c_coefs_width              = 16

# General purpose vars
c_write_coefs          = False
c_align_mesh           = True
c_use_adc_data         = False
c_read_subband_stats   = True
c_read_beamlet_stats   = True
c_verify_beamlet_stats = False
c_single_beam          = False
c_close_figures        = False
c_use_default_settings = True   # Set to True in order to skip the mm writes to ss_parallel, ss_wides and weights. To boost simulation time.
c_write_settings       = True

#########################################################################################################

nodelist = [(0,'F'), (1,'F'),(2,'F'), (3,'F'), (4,'B'), (5,'B'), (6,'B'), (7,'B')]
unb = UniBoard(ip = "10.99.0.1", port = 5000, nodelist = nodelist)
print "Connected to UniBoard with start ip 10.99.0.1. ID: %d" % unb.id

signal_paths = 16
sp_per_node  = 4

# WG constants
phase    = 0.0          # phase : 0.0 to 360.0 degrees
freq     = 0.101531982  # freq  : 0.0 = DC, 1.0 = Fs = 800 MHz
ampl     = 0.6          # ampl  : 1.0 = full scale

# Load mesh plugin
trnb_mesh = unb.load_plugin("UniBoardNonBondedTr", nodes='ALL', instance_id = 'MESH')

# Load BSN source plugin
bsn_source = unb.load_plugin("UniBoardBsnSource", nodes = 'BACK')

# Load BSN scheduler plugin
bsn_scheduler = unb.load_plugin("UniBoardBsnScheduler", nodes = 'BACK', instance_id = 'WG')

# Load ADU I2C commander plugins
adu = ['AB', 'CD']
for ai in adu:
    unb.load_plugin("UniBoardAduI2CCommander", instance_id = ai, nodes='BACK')
aduI2C = unb.uniboard_adu_i2c_commander

# Create aduh control object
quad = unb.load_plugin("UniBoardAduhQuad", nodes='BACK')

# Load wave generator plugins (one per SP / BN combination)
for node in unb.back_nodes: # Number of back nodes
    for si in range(sp_per_node): # Number of signal paths
        unb.load_plugin("UniBoardWBWaveGenerator", instance_number = si, nodes = node)

# Get pointer to internal list representation of loaded wave generator plugins
wg = unb.uniboard_wb_wave_generator

# - Create filter instance
fil = unb.load_plugin("UniBoardPpfFilterbank", nof_instances = c_nof_input_signals_per_bn, nof_taps = c_nof_taps,
                      nof_bands = c_fft_size, wb_factor = c_wb_factor, nodes = 'BACK')

# Create statistics instances for the subband statistics
for i in range(c_nof_wb_ffts * c_wb_factor):
    unb.load_plugin("UniBoardSubbandStatistics", nof_stats = c_fft_size / c_wb_factor, stat_data_width = c_stat_data_w,
                    nof_regs_per_stat = c_stat_data_sz, xst_enable = False, instance_number = i, nodes = 'BACK')
sst = unb.uniboard_subband_statistics

# Create beamformer
beamformer = unb.load_plugin("UniBoardBeamformer", fft_size                 = c_fft_size,
                                                   nof_input_signals_per_bn = c_nof_input_signals_per_bn,
                                                   nof_wb_ffts              = c_nof_wb_ffts,
                                                   nof_iblets               = c_nof_iblets,
                                                   nof_bf_units_per_node    = c_nof_bf_units,
                                                   nof_signal_paths         = c_nof_signal_paths,
                                                   nof_weights              = c_nof_weights,
                                                   nof_subbands             = c_nof_subbands,
                                                   nof_input_streams        = c_nof_input_streams,
                                                   in_weight_w              = c_in_weight_w,
                                                   wb_factor                = c_wb_factor,
                                                   stat_data_w              = c_stat_data_w,
                                                   stat_data_sz             = c_stat_data_sz,
                                                   nof_sp_per_input_stream  = c_nof_sp_per_input_stream,
                                                   use_backplane            = False)

# Get pointer to internal list of beamforming statistics plugins
bst = unb.uniboard_beamlet_statistics

def_iblets = []
def_nof_beamlets_per_iblet = []
for i in range(c_nof_iblets):
    def_iblets.append(i)
    def_nof_beamlets_per_iblet.append(10)

##############################################################################################################

#######################################################################
# Write filter filterbankcoefficients to memory in case the .mif files
# were not in place. In most cases this step is skipped, since the
# coefficients are already defined in the .mif files that are located
# in $UNB\Firmware\dsp\filter\build\data\*.mif.
# This code shows how to upload different coefficients.
#######################################################################
if c_write_coefs:
    # Read all the coefficients from the file into a list.
    coefs_list_from_file =[]
    f = file(c_coefs_input_file, "r")
    for i in range(c_nof_coefs_in_file):
        s = int(f.readline())
        s &= 2 ** c_coefs_width - 1
        coefs_list_from_file.append(s)
    f.close()

    # Downsample the list to the number of required coefficients, based on the c_nof_taps and the c_fft_size
    coefs_list = []
    for i in range(c_nof_taps*c_fft_size):
        s = coefs_list_from_file[i*c_downsample_factor]
        coefs_list.append(s)

    # Write the coefficients to the memories
    for l in range(c_nof_input_signals_per_bn):
        for k in range(c_wb_factor):
            for j in range(c_nof_taps):
                write_list=[]
                for i in range(c_fft_size/c_wb_factor):
                    write_list.append(coefs_list[j*c_fft_size+i*c_wb_factor + c_wb_factor-1-k])
                write_list_rev = []
                for i in range(c_fft_size/c_wb_factor):                          # Reverse the list
                    write_list_rev.append(write_list[c_fft_size/c_wb_factor-i-1])
                fil.write_coefs(write_list_rev,l,j,k)

# Stop the datastream that is currently running
bsn_source.write_disable()

# Setting the interval of the sync pulse to 781250 packets, which corresponds to 1 second integration time.
bsn_source.write_blocks_per_sync(781250)

# Set up mesh
trnb_mesh.write_tx_align_enable()
time.sleep(0.5)
trnb_mesh.write_rx_align_enable()
trnb_mesh.write_rx_align_enable(0)
# We don't want to take away the alignment pattern too soon..RX needs some time to align
time.sleep(3)
trnb_mesh.write_tx_align_enable(0)

# Set up wave generators, giving each signal a unique frequency

freqStep   = 1.0 / ( 2 * signal_paths)
freqOffset = 1.0 / 64
for i in range(signal_paths):
    wg[i].write_sinus_settings(phase, freqStep * i + freqOffset, amplitude = 0.8)  # Specify the waveform

for i in range(signal_paths):
    wg[i].write_mode_sinus()    # Enable the waveform generator in sinewave-mode

# Switch between ADC of wave generators
if c_use_adc_data:
    for i in range(16):
        wg[i].write_mode_off()      # Disable the waveform generator

    for ai in range(len(adu)):            # Enable the ADCs
        aduI2C[ai].write_set_adc()

    quad.read_lock_status()
    quad.read_lock_status()

# Set up BSN and restart
bsn_source.write_restart_pps()
time.sleep(1)

# Schedule the BSN scheduler that triggers the waveform generators to start. This is done by reading out the
# current BSN and add a number to it. This calculated "future" BSN is written. As soon as this BSN
# number passes the Waveform generators are started. In this way all nodes start  at the same time.
bsn = bsn_scheduler.read_current_bsn()
bsn = bsn[0] + bsn_scheduler.bsn_latency
bsn_scheduler.write_scheduled_bsn(bsn)
time.sleep(1)

# Select subbands and specify the number of beamlets to be created.
iblets = []
nof_beamlets_per_iblet = []
if c_use_default_settings:
    iblets = def_iblets
    nof_beamlets_per_iblet = def_nof_beamlets_per_iblet
else:
    # Create custom selection of subbands here:
    for i in range(c_nof_iblets):
        iblets.append(i + 127)
        nof_beamlets_per_iblet.append(10)

# Apply subband selection to beamformer
beamformer.select_subbands(iblets, nof_beamlets_per_iblet, write_settings = c_write_settings)
import sys; sys.exit()
#######################################################################
# Create weights for all signal paths, all selected subband(iblets) and
# for every beam(nof_beamlets_per_iblet).
#
#   The weights[x][y][z] format is as follows:
#
#     x represents the Iblet-number ranging from 0-383
#     y represents the Signalpath-number ranging from 0-63
#     z represents the Beamlet-number ranging from 0-1023 (peak) 10 (average)
#       The range of z is equal for all y's, but unique for every x.
#######################################################################
first_si = 0
n_weights = 0
weights = []
for h in range(c_nof_iblets):                       # Selected subbands (384)
    iblet_weights = []
    for i in range(c_nof_signal_paths):             # inputs (16)
        sp_iblet_weights = []
        for j in range(nof_beamlets_per_iblet[h]):  # beamlets (avg=10)
            if c_use_default_settings:     # Make all weights real and set to +1
                n_weights += 1
                sp_iblet_weights.append(complex(32760,0))
            elif c_single_beam == True and (j < nof_beamlets_per_iblet[0]):
                n_weights += 1
                if i%2 == 0:
                    sp_iblet_weights.append(complex(1024,0))
                else:
                    sp_iblet_weights.append(complex(1024,0))
            elif c_single_beam == False and i == (j+first_si):
                n_weights += 1
                sp_iblet_weights.append(complex(32760,0))
            else:
                sp_iblet_weights.append(complex(0,0))
        iblet_weights.append(sp_iblet_weights)
    weights.append(iblet_weights)
print 'Number of nonzero values in weight matrix is ' + str(n_weights)

if c_write_settings:
    bsn_source.write_disable()
    beamformer.set_all_weights(weights)
    bsn_source.write_restart_pps()

# Wait a while before reading out the statistics(allow at least four sync periods to pass to have the filter settled)
time.sleep(2)

# Create objects for post processing tools
stati_conf = statiConfiguration(c_fft_size, c_nof_wb_ffts, c_bsn_period, c_blocks_per_sync,
                                c_stat_input_bits, c_wb_factor, c_nof_bf_units)
stati_h    = Stati_functions(stati_conf)


#######################################################################
# Download the subband statistics. After capturing, the subband
# statistics can be found in stati_h.sub_stati (real values) and in
# stati_h.db_sub_stati (logarithmic values).
#######################################################################
# Wait a while before reading out the statistics(allow at least four sync periods to pass to have the filter settled)
time.sleep(1)

stati_h.plot_init()
xas_type = 'freq_z2'
fig_cnt  = 0

if c_read_subband_stats:
    stati_h.subband_stati_capture(sst)

    #######################################################################
    # Plot the subband statistics.
    #######################################################################
    stati_h.plot_subband_stati(figs='one', xas=xas_type, norm='dBFS',lim_axis='off', bck_fft='off', fig_nr=fig_cnt, pl_legend='on'); fig_cnt+=1

 #######################################################################
    # Download the beamlet statistics.
    #######################################################################
    if c_read_beamlet_stats:
        beamlets = stati_h.beamlet_stati_capture(bst)
        import sys; sys.exit()

        #######################################################################
        # Plot the beamlet statistics.
        #######################################################################
        plot_iblets = []
        plot_nof_beamlets_per_iblet = []
        # Check which front nodes are in the system. Only those beamlet statistics have been read and can be plotted.
        for i in range(4):
            plot_iblets.append(iblets[i*c_nof_subbands:(i+1)*c_nof_subbands])
            plot_nof_beamlets_per_iblet.append(nof_beamlets_per_iblet[i*c_nof_subbands:(i+1)*c_nof_subbands])
        stati_h.plot_beamlet_subband(beamformer.bf, norm='dB', xas=xas_type, plot_type='freq',iblets=flatten(plot_iblets), nof_beamlets_per_iblet=flatten(plot_nof_beamlets_per_iblet), beams_to_plot=10, fig_nr=fig_cnt, pl_legend='on',lim_axis='off'); fig_cnt+=1

        c_threshold_high = 100000
        if c_verify_beamlet_stats:
            for i in range(len(beamlets)):
                for j in range(c_nof_weights):
                    if beamlets[i][j].real > c_threshold_high and ((((i % c_nof_bf_units)*c_nof_weights + j)/10-16) % 32 != 0):
                        print 'FAILED'
                        stri = 'Spike on unexpected bin! ' + "i=" + str(i) + " j=" + str(j) + "  " + str(beamlets[i][j])
                        print stri

#######################################################################################################################
stati_h.plot_last()
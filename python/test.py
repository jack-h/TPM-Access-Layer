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

###################################################################################

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
        unb.load_plugin("UniBoardWBWaveGenerator", instance_number = si, nodes=unb.nodes[node]['names'][0])

# Get pointer to internal list representation of loaded wave generator plugins
wg = unb.uniboard_wb_wave_generator

# Create beamformer
beamformer = unb.load_plugin("UniBoardBeamformer", fft_size                 = c_fft_size,\
                                                   nof_input_signals_per_bn = c_nof_input_signals_per_bn,\
                                                   nof_wb_ffts              = c_nof_wb_ffts,\
                                                   nof_iblets               = c_nof_iblets,\
                                                   nof_bf_units_per_node    = c_nof_bf_units,\
                                                   nof_signal_paths         = c_nof_signal_paths,\
                                                   nof_weights              = c_nof_weights,\
                                                   nof_subbands             = c_nof_subbands,\
                                                   nof_input_streams        = c_nof_input_streams,\
                                                   in_weight_w              = c_in_weight_w,\
                                                   wb_factor                = c_wb_factor,\
                                                   stat_data_w              = c_stat_data_w,\
                                                   stat_data_sz             = c_stat_data_sz,\
                                                   nof_sp_per_input_stream  = c_nof_sp_per_input_stream,\
                                                   use_backplane            = False )

##############################################################################################################

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

# Set up BSN and restart
bsn_source.write_restart_pps()
time.sleep(1)

# Schedule the BSN scheduler that triggers the waveform generators to start. This is done by reading out the
# current BSN and add a number to it. This calculated "future" BSN is written. As soon as this BSN
# number passes the Waveform generators are started. In this way all nodes start  at the same time.
bsn = bsn_scheduler.read_current_bsn()
bsn = bsn[0] + bsn_scheduler.bsn_latency
bsn_scheduler.write_scheduled_bsn(bsn)
# time.sleep(1)

print bsn_source.read_current_bsn()
# time.sleep(1)
print bsn_source.read_current_bsn()
# time.sleep(3)
print bsn_source.read_current_bsn()
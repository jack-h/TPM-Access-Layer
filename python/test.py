from pyfabil import UniBoard
import time

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

# Load wave generator plugins (one per SP / BN combination)
for node in unb.back_nodes: # Number of back nodes
    for si in range(sp_per_node): # Number of signal paths
        unb.load_plugin("UniBoardWBWaveGenerator", instance_number = si, nodes=unb.nodes[node]['names'][0])

# Get pointer to internal list representation of loaded wave generator plugins
wg = unb.uniboard_wb_wave_generator

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
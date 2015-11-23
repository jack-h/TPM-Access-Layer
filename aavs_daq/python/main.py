from time import sleep

from persisters import *
from interface import *
import numpy as np

# DAQ configuration, set with defaults
configuration = { "nof_antennas"                : 16,
                  "nof_channels"                : 512,
                  "nof_beams"                   : 1,
                  "tiles_per_station"           : 1,
                  "nof_stations"                : 1,
                  "nof_polarisations"           : 2,
                  "start_station_id"            : 0,
                  "nof_raw_samples"             : 65536,
                  "nof_channel_samples"         : 128,
                  "nof_beam_samples"            : 64,
                  "receiver_ports"              : [4660, 4661],
                  "channel_channels_per_packet" : 1,
                  "channel_antennas_per_packet" : 16,
                  "channel_samples_per_packet"  : 32,
                  "beam_samples_per_packet"     : 1,
                  "receiver_frame_size"         : 2048,
                  "receiver_frames_per_block"   : 32,
                  "receiver_nof_blocks"         : 128,
                  "receiver_interface"          : "eth0"}

# Global HDF5 persisters handles
persisters = { }

def raw_data_callback(data, timestamp):
    # Extract data sent by DAQ
    print "Raw data callback"
    nof_values = configuration['nof_antennas'] * configuration['nof_polarisations'] * configuration['nof_raw_samples']
    values_ptr = ctypes.cast(data, ctypes.POINTER(ctypes.c_int8))
    values     = np.array([values_ptr[i] for i in range(nof_values)])

    # Persist extracted data to file
  #  persisters['RAW_DATA'].ingest_data(values, timestamp)

def channel_data_callback(data, timestamp):
    # Extract data sent by DAQ
    print "Channel data callback"
    nof_values = configuration['nof_antennas'] * configuration['nof_polarisations'] * \
                 configuration['nof_channel_samples'] * configuration['nof_channels']
    values_ptr = ctypes.cast(data, ctypes.POINTER(ctypes.c_int8))
    values     = np.array([values_ptr[i] for i in range(nof_values * 2)], dtype='float')
    values     = values[::2] + values[1::2] * 1j

    # Persist extracted data to file
    persisters['CHANNEL_DATA'].ingest_data(values, timestamp)

def beam_data_callback(data, timestamp):
    # Extract data sent by DAQ
    print "Beam data callback"
    nof_values = configuration['nof_beams'] * configuration['nof_polarisations'] * \
                 configuration['nof_beam_samples'] * configuration['nof_channels']
    values_ptr = ctypes.cast(data, ctypes.POINTER(ctypes.c_int8))
    values     = np.array([values_ptr[i] for i in range(nof_values * 2)], dtype='float')
    values     = values[::2] + values[1::2] + 1j

    # Persist extracted data to file
  #  persisters['BEAM_DATA'].ingest_data(values, timestamp)

# ----------------------------------------- Script Body ------------------------------------------------

# Script main entry point
if __name__ == "__main__":

    # Create data persisters
    raw_file = RawFormatFile(path="raw_data.hdf5", mode = FileModes.Write)
    raw_file.set_metadata(configuration['nof_antennas'], configuration['nof_polarisations'],
                          configuration['nof_stations'], configuration['nof_beams'], configuration['tiles_per_station'],
                          configuration['nof_channels'], configuration['nof_raw_samples'])
    persisters['RAW_DATA'] = raw_file

    channel_file = ChannelFormatFile(path="channel_data.hdf5", mode = FileModes.Write)
    channel_file.set_metadata(configuration['nof_antennas'], configuration['nof_polarisations'],
                          configuration['nof_stations'], configuration['nof_beams'], configuration['tiles_per_station'],
                          configuration['nof_channels'], configuration['nof_channel_samples'])
    persisters['CHANNEL_DATA'] = channel_file

    beam_file = BeamFormatFile(path="beam_data.hdf5", mode = FileModes.Write)
    beam_file.set_metadata(configuration['nof_antennas'], configuration['nof_polarisations'],
                          configuration['nof_stations'], configuration['nof_beams'], configuration['tiles_per_station'],
                          configuration['nof_channels'], configuration['nof_beam_samples'])
    persisters['BEAM_DATA'] = beam_file


    # Initialise AAVS DAQ library
    initialise_library("/usr/local/lib/libaavsdaq")

    # Configure receiver
    call_set_receiver_configuration(configuration['nof_antennas'],
                                    configuration['nof_channels'],
                                    configuration['nof_beams'],
                                    configuration['tiles_per_station'],
                                    configuration['nof_stations'],
                                    configuration['nof_polarisations'],
                                    configuration['start_station_id'])

    # Start receiver
    if call_start_receiver(configuration['receiver_interface'],
                           configuration['receiver_frame_size'],
                           configuration['receiver_frames_per_block'],
                           configuration['receiver_nof_blocks']) != Result.Success.value:
        print "Failed to start receiver"

    # Set receiver ports
    for port in configuration['receiver_ports']:
        if call_add_receiver_port(port) != Result.Success.value:
            print "Failed to set receiver port %d" % port

    # Start raw data consumer
    if call_start_raw_consumer(configuration['nof_raw_samples']) != Result.Success.value:
        print "Failed to start raw data consumer"

    # Start channel data consumer
    if call_start_channel_consumer(configuration['nof_channel_samples'],
                                   configuration['channel_channels_per_packet'],
                                   configuration['channel_antennas_per_packet'],
                                   configuration['channel_samples_per_packet']) != Result.Success.value:
        print "Failed to start channel data consumer"

    # Start beam data consumer
    if call_start_beam_consumer(configuration['nof_beam_samples'],
                                configuration['beam_samples_per_packet']) != Result.Success.value:
        print "Failed to start beam data consumer"

    # Set raw data consumer callback
  #  if call_set_raw_consumer_callback(DATACALLBACK_RAW(raw_data_callback)) != Result.Success.value:
  #      print "Failed to set raw data consumer callback"

    # Set channel data consumer callback
    if call_set_channel_consumer_callback(DATACALLBACK_CHANNEL(channel_data_callback)) != Result.Success.value:
        print "Failed to set channel data consumer callback"

    # # Set beam data consumer callback
  #  if call_set_beam_consumer_callback(DATACALLBACK_BEAM(beam_data_callback)) != Result.Success.value:
  #      print "Failed to set beam data consumer callback"

    # Loop forever
    print "Ready to receive data"
    sleep(1000)

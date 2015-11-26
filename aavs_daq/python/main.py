from time import sleep

from persisters import *
from interface import *
import numpy as np
import logging

# DAQ configuration, set with optparser
conf = { }

# Global HDF5 persisters handles
persisters = { }

# Custom numpy type for creating complex signed 8-bit data
complex_8t = numpy.dtype([('real', numpy.int8), ('imag', numpy.int8)])

def raw_data_callback(data, timestamp):
    # Extract data sent by DAQ
    logging.info("Raw data callback")
    nof_values = conf.nof_antennas * conf.nof_polarisations * conf.nof_raw_samples
    values_ptr = ctypes.cast(data, ctypes.POINTER(ctypes.c_int8))
    values     = np.array([values_ptr[i] for i in range(nof_values)])

    # Persist extracted data to file
    persisters['RAW_DATA'].ingest_data(data_ptr = values, timestamp = timestamp)

def channel_data_callback(data, timestamp, continuous = False):
    # Extract data sent by DAQ
    if continuous:
        logging.info("(Continuous) Channel data callback")
        nof_values = conf.nof_antennas * conf.nof_polarisations * conf.nof_channel_samples

    else:
        logging.info("(Burst) Channel data callback")
        nof_values = conf.nof_antennas * conf.nof_polarisations * \
                     conf.nof_channel_samples * conf.nof_channels
    values_ptr = ctypes.cast(data, ctypes.POINTER(ctypes.c_int8))
    values     = np.array([values_ptr[i] for i in range(nof_values * 2)], dtype=numpy.int8)

    # data = np.empty(nof_values, numpy.dtype([('real', numpy.int8), ('imag', numpy.int8)]))
    # for i, (real, imag)in enumerate(zip(values[::2], values[1::2])):
    #     data[i][0] = real
    #     data[i][1] = imag

    # Persist extracted data to file
    if continuous:
        persisters['CHANNEL_DATA'].ingest_data(data_ptr = values, timestamp = timestamp, append=True)
    else:
        persisters['CHANNEL_DATA'].ingest_data(data_ptr = values, timestamp = timestamp)

    logging.info("Persister ready")

def channel_burst_data_callback(data, timestamp):
    # Channel callback wrapper for burst data mode
    channel_data_callback(data, timestamp)

def channel_continuous_data_callback(data, timestamp):
    # Channel callback wrapper for continuous data mode
    channel_data_callback(data, timestamp, True)

def continuous_channel_data_callback(data, timestamp):
    # Extract data sent by DAQ
    logging.info("Channel data callback")
    nof_values = conf.nof_antennas * conf.nof_polarisations * conf.nof_channel_samples
    values_ptr = ctypes.cast(data, ctypes.POINTER(ctypes.c_int8))
    values     = np.array([values_ptr[i] for i in range(nof_values * 2)], dtype='float')
    values     = values[::2] + values[1::2] * 1j

    # Persist extracted data to file
    persisters['CHANNEL_DATA'].ingest_data(data_ptr = values, timestamp = timestamp)

def beam_data_callback(data, timestamp):
    # Extract data sent by DAQ
    logging.info("Beam data callback")
    nof_values = conf.nof_beams * conf.nof_polarisations * \
                 conf.nof_beam_samples * conf.nof_channels
    values_ptr = ctypes.cast(data, ctypes.POINTER(ctypes.c_int8))
    values     = np.array([values_ptr[i] for i in range(nof_values * 2)], dtype='float')
    values     = values[::2] + values[1::2] + 1j

    # Persist extracted data to file
    persisters['BEAM_DATA'].ingest_data(data_ptr = values, timestamp = timestamp)

# ----------------------------------------- Script Body ------------------------------------------------

# Script main entry point
if __name__ == "__main__":

    # Use OptionParse to get command-line arguments
    from optparse import OptionParser
    from sys import argv, stdout

    parser = OptionParser(usage="usage: %aavs_daq_receiver [options]")

    parser.add_option("-a", "--nof_antennas", action="store", dest="nof_antennas",
                      type="int", default=16, help="Number of antennas [default: 16]")
    parser.add_option("-c", "--nof_channels", action="store", dest="nof_channels",
                      type="int", default=512, help="Number of channels [default: 512]")
    parser.add_option("-b", "--nof_beams", action="store", dest="nof_beams",
                      type="int", default=1, help="Number of beams [default: 1]")
    parser.add_option("-p", "--nof_pols", action="store", dest="nof_polarisations",
                      type="int", default=2, help="Number of polarisations [default: 2]")
    parser.add_option("-t", "--tiles_per_stations", action="store", dest="tiles_per_station",
                      type="int", default=1, help="Number of tiles per station [default: 1]")
    parser.add_option("-s", "--nof_stations", action="store", dest="nof_stations",
                      type="int", default=1, help="Number of stations [default: 1]")
    parser.add_option("-S", "--start_station_id", action="store", dest="start_station_id",
                      type="int", default=0, help="Start station ID [default: 0]")
    parser.add_option("", "--raw_samples", action="store", dest="nof_raw_samples",
                      type="int", default=65536, help="Number of raw antennas samples per buffer (requires different firmware to "
                                          "change [default: 65536]")
    parser.add_option("", "--channel_samples", action="store", dest="nof_channel_samples",
                      type="int", default=128, help="Number of channelised spectra per buffer [default: 128]")
    parser.add_option("", "--beam_samples", action="store", dest="nof_beam_samples",
                      type="int", default=64, help="Number of beam samples per buffer (requires different firmware to " \
                                        "change [default: 64]")
    parser.add_option("-P", "--receiver_ports", action="store", dest="receiver_ports",
                      default="4660,4661", help="Comma seperated UDP ports to listen on [default: 4660,4661]")
    parser.add_option("-i", "--receiver_interface", action="store", dest="receiver_interface",
                      default="eth1", help="Receiver interface [default: eth1]")
    parser.add_option("", "--channel_channel_per_packet", action="store", dest="channel_channels_per_packet",
                      type="int", default=1, help="Number of channels in a channelised data packet [default: 1]")
    parser.add_option("", "--channel_antenna_per_packet", action="store", dest="channel_antennas_per_packet",
                      type="int", default=16, help="Number of antennas per channelised data packet [default: 16]")
    parser.add_option("", "--channel_samples_per_packet", action="store", dest="channel_samples_per_packet",
                      type="int", default=32, help="Number of samples per channelised data packet [default: 32]")
    parser.add_option("", "--beam_samples_per_packet", action="store", dest="beam_samples_per_packet",
                      type="int", default=1, help="Number of samples per channelised data packet [default: 1]")
    parser.add_option("", "--receiver_frame_size", action="store", dest="receiver_frame_size",
                      type="int", default=2048, help="Receiver frame size [default: 2048]")
    parser.add_option("", "--receiver_frames_per_block", action="store", dest="receiver_frames_per_block",
                      type="int", default=32, help="Receiver frame size [default: 32]")
    parser.add_option("", "--receiver_nof_blocks", action="store", dest="receiver_nof_blocks",
                      type="int", default=256, help="Receiver frame size [default: 256]")

    # Operation modes
    parser.add_option("-X", "--continuous_channel_enable", action="store_true", dest="continuous_channel",
                      default=False, help="Continuous channel mode [default: False]")
    parser.add_option("-B", "--read_beam_data", action="store_true", dest="read_beam_data",
                      default=False, help="Read beam data [default: False]")
    parser.add_option("-C", "--read_channel_data", action="store_true", dest="read_channel_data",
                      default=False, help="Read channelised data [default: False]")
    parser.add_option("-R", "--read_raw_data", action="store_true", dest="read_raw_data",
                      default=False, help="Read raw data [default: False]")

    (conf, args) = parser.parse_args(argv[1:])

    # Extract port string and create list of ports
    conf.receiver_ports = [int(x) for x in conf.receiver_ports.split(',')]

    # Set logging
    log = logging.getLogger('')
    log.setLevel(logging.DEBUG)
    format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    ch = logging.StreamHandler(stdout)
    ch.setFormatter(format)
    log.addHandler(ch)

    # Check if any mode was chosen
    if not any([conf.read_beam_data, conf.read_channel_data, conf.read_raw_data, conf.continuous_channel]):
        logging.error("No DAQ mode was set. Exiting")
        exit(0)

    # Initialise AAVS DAQ library
    initialise_library("/usr/local/lib/libaavsdaq")

    # ---------------------------- Receiver Configuration ---------------------------------------

    # Configure receiver
    call_set_receiver_configuration(conf.nof_antennas,
                                    conf.nof_channels,
                                    conf.nof_beams,
                                    conf.tiles_per_station,
                                    conf.nof_stations,
                                    conf.nof_polarisations,
                                    conf.start_station_id)

    # ---------------------------- Start network receiver ---------------------------------------
    # Start receiver
    if call_start_receiver(conf.receiver_interface,
                           conf.receiver_frame_size,
                           conf.receiver_frames_per_block,
                           conf.receiver_nof_blocks) != Result.Success.value:
        logging.error("Failed to start receiver")
        exit(-1)

    # Set receiver ports
    for port in conf.receiver_ports:
        if call_add_receiver_port(port) != Result.Success.value:
            logging.error("Failed to set receiver port %d" % port)
            exit(-1)

    # ------------------------------- Raw data consumer ------------------------------------------
    if conf.read_raw_data:
        # Start raw data consumer
        if call_start_raw_consumer(conf.nof_raw_samples) != Result.Success.value:
            logging.error("Failed to start raw data consumer")

        logging.info("Started raw data consumer")
        # Set raw data consumer callback  #  if call_set_raw_consumer_callback(DATACALLBACK_RAW(raw_data_callback)) != Result.Success.value:
        #      print "Failed to set raw data consumer callback"

        # Create data persister
        raw_file = RawFormatFileManager(root_path = ".", mode = FileModes.Write)
        raw_file.set_metadata(n_antennas = conf.nof_antennas,
                              n_pols     = conf.nof_polarisations,
                              n_samples  = conf.nof_raw_samples)
        persisters['RAW_DATA'] = raw_file

    # ----------------------------- Channel data consumer ----------------------------------------
    # Channel consumer can either run in continuous or burst mode, but not both
    if conf.continuous_channel or conf.read_channel_data:

        # Start channel data consumer
        if call_start_channel_consumer(conf.nof_channel_samples,
                                       conf.channel_channels_per_packet,
                                       conf.channel_antennas_per_packet,
                                       conf.channel_samples_per_packet) != Result.Success.value:
            logging.error("Failed to start continuous channel data consumer")

            logging.info("Started channel data consumer")

        if not conf.continuous_channel:
            # Set channel data consumer callback
            if call_set_channel_consumer_callback(DATACALLBACK_CHANNEL(channel_burst_data_callback)) != Result.Success.value:
                 logging.error("Failed to set channel data consumer callback")

            # Create data persister
            channel_file = ChannelFormatFileManager(root_path=".", mode=FileModes.Write)

            channel_file.set_metadata(n_chans    = conf.nof_channels,
                                      n_antennas = conf.nof_antennas,
                                      n_pols     = conf.nof_polarisations,
                                      n_samples  = conf.nof_channel_samples)
            persisters['CHANNEL_DATA'] = channel_file

        else:
            # Set channel data consumer callback
            if call_set_channel_consumer_callback(DATACALLBACK_CHANNEL(channel_continuous_data_callback)) != Result.Success.value:
                logging.error("Failed to set channel data consumer callback")

            # Create data persister
            channel_file = ChannelFormatFileManager(root_path=".", mode=FileModes.Write)
            channel_file.set_metadata(n_chans    = 1,
                                      n_antennas = conf.nof_antennas,
                                      n_pols     = conf.nof_polarisations,
                                      n_samples  = conf.nof_channel_samples)
            persisters['CHANNEL_DATA'] = channel_file

    # ------------------------------- Beam data consumer -----------------------------------------
    if conf.read_beam_data:
        # Start beam data consumer
        if call_start_beam_consumer(conf.nof_beam_samples,
                                    conf.beam_samples_per_packet) != Result.Success.value:
             logging.error("Failed to start beam data consumer")

        logging.info("Started beam data consumer")

        # # Set beam data consumer callback
        if call_set_beam_consumer_callback(DATACALLBACK_BEAM(beam_data_callback)) != Result.Success.value:
            logging.error("Faile to set beam data consumer callback")

        # Create data persister
        beam_file = BeamFormatFileManager(root_path=".", mode = FileModes.Write)
        beam_file.set_metadata(n_chans   = conf.nof_channels,
                               n_pols    = conf.nof_polarisations,
                               n_samples = conf.nof_beam_samples)
        persisters['BEAM_DATA'] = beam_file


    # Wait forever
    logging.info("Ready to receive data")
    sleep(1000)
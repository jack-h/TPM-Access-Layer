from enum import Enum
import ctypes

# ------------------------------ Enumerations --------------------------------


class DataType(Enum):
    """ DataType enumeration """
    RawData = 1
    ChannelisedData = 2
    BeamData = 3


class Result(Enum):
    """ Result enumeration """
    Success = 0
    Failure = -1
    ReceiverUninitialised = -2
    ConsumerAlreadyInitialised = -3

# ---------------------------- Wrap library calls ----------------------------

# Global store for interface object
library = None

# Define consumer data callback wrapper
DATACALLBACK_RAW = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_int8), ctypes.c_double)
DATACALLBACK_BEAM = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_int8), ctypes.c_double)
DATACALLBACK_CHANNEL = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_int8), ctypes.c_double)

def initialise_library(filepath = None):
    """ Wrap AAVS DAQ shared library functionality in ctypes
    :param filepath: Path to library path
    """
    global library

    # This only need to be done once
    if library is not None:
        return

    # Load AAVS DAQ shared library
    if filepath is None:
        _library = "libaavsdaq"
    else:
        _library = filepath

    # Load library
    library = ctypes.CDLL(_library + ".so")

    # Define setReceiverConfiguration function
    library.setReceiverConfiguration.argtypes = [ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint8, ctypes.c_uint8,
                                                 ctypes.c_uint16, ctypes.c_uint8, ctypes.c_uint16]
    library.setReceiverConfiguration.restype = None

    # Define startReceiver function
    library.startReceiver.argtypes = [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
    library.startReceiver.restype = ctypes.c_int

    # Define addReceiverPort function
    library.addReceiverPort.argtypes = [ctypes.c_uint16]
    library.addReceiverPort.restype = ctypes.c_int

    # Define startRawConsumer function
    library.startRawConsumer.argtypes = [ctypes.c_uint32]
    library.startRawConsumer.restype = ctypes.c_int

    # Define startChannelConsumer function
    library.startChannelConsumer.argtypes = [ctypes.c_uint32, ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint16]
    library.startChannelConsumer.restype = ctypes.c_int

    # Define startBeamConsumer function
    library.startBeamConsumer.argtypes = [ctypes.c_uint32, ctypes.c_uint16]
    library.startBeamConsumer.restype = ctypes.c_int

    # Define setRawConsumerCallback function
    library.setRawConsumerCallback.argtypes = [DATACALLBACK_RAW]
    library.setRawConsumerCallback.restype = ctypes.c_int

    # Define setChannelConsumerCallback function
    library.setChannelConsumerCallback.argtypes = [DATACALLBACK_CHANNEL]
    library.setChannelConsumerCallback.restype = ctypes.c_int

    # Define setBeamConsumerCallback function
    library.setBeamConsumerCallback.argtypes = [DATACALLBACK_BEAM]
    library.setBeamConsumerCallback.restype = ctypes.c_int

# ------------- Function wrappers to library ---------------------------


def call_set_receiver_configuration(nof_antennas, nof_channels, nof_beams, tiles_per_station,
                                    nof_stations, nof_polarisations, start_station_id):
    """ Set receiver configuration
    :param nof_antennas: Number of antennas
    :param nof_channels: Number of channels
    :param nof_beams: Number of beams
    :param tiles_per_station: Tiles per station
    :param nof_stations: Number of stations
    :param nof_polarisations: Number of polarisations
    :param start_station_id: Start station ID
    :return: Return code
    """
    global library
    return library.setReceiverConfiguration(nof_antennas, nof_channels, nof_beams, tiles_per_station,
                                            nof_stations, nof_polarisations, start_station_id)


def call_start_receiver(interface, frame_size, frames_per_block, nof_blocks):
    """ Start network receiver thread
    :param interface: Interface name
    :param frame_size: Maximum frame size
    :param frames_per_block: Frames per block
    :param nof_blocks: Number of blocks
    :return: Return code
    """
    global library
    return library.startReceiver(interface, frame_size, frames_per_block, nof_blocks)


def call_add_receiver_port(port):
    """ Add receive port to receiver
    :param port: Port number
    :return: Return code
    """
    global library
    return library.addReceiverPort(port)


def call_start_raw_consumer(samples_per_buffer):
    """ Start raw data consumer
    :return: Return code
    :param samples_per_buffer: Total number of samples to buffer
    """
    global library
    return library.startRawConsumer(samples_per_buffer)


def call_start_channel_consumer(nof_samples, channels_per_packet, antennas_per_packet, samples_per_packet):
    """ Start channel data consumer
    :param nof_samples: Total number of (time) samples to buffer
    :param channels_per_packet: Number of channels per packet
    :param antennas_per_packet: Number of antennas per packet
    :param samples_per_packet: Number of (time) samples per packet
    :return: Return code
    """
    global library
    return library.startChannelConsumer(nof_samples, channels_per_packet, antennas_per_packet, samples_per_packet)


def call_start_beam_consumer(nof_samples, samples_per_packet):
    """ Start beam data consumer
    :param nof_samples: Number of samples to buffer
    :param samples_per_packet: Number of samples in packet
    :return: Return code
    """
    global library
    return library.startBeamConsumer(nof_samples, samples_per_packet)


def call_set_raw_consumer_callback(callback):
    """ Set raw data consumer callback function
    :param callback: Callback function
    :return: Return code
    """
    global library
    return library.setRawConsumerCallback(callback)


def call_set_channel_consumer_callback(callback):
    """ Set channel data consumer callback function
    :param callback: Callback function
    :return: Return code
    """
    global library
    return library.setChannelConsumerCallback(callback)


def call_set_beam_consumer_callback(callback):
    """ Set beam data consumer callback function
    :param callback: Callback function
    :return: Return code
    """
    global library
    return library.setBeamConsumerCallback(callback)

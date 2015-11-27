//
// Created by Alessio Magro on 17/11/2015.
//

// Includes and namespaces

#include "Daq.h"

#include <map>

using namespace std;

// --------------------------- DEFINE GLOBALS ------------------------------

// The global consumers map, which keeps track of the initialised and running consumers
// Only one instance per consumer type can be initialised
map<DATA_TYPE, DataConsumer *> consumers;

// Global network receiver instance
NetworkReceiver *receiver = NULL;

// Receiver configuration
RECEIVER_CONFIGURATION configuration = { 0 };

// ------------------------ LAYER FUNCTIONS ------------------------------

// set global parameters / telescope setup
void setReceiverConfiguration(uint16_t  nof_antennas,
                              uint16_t  nof_channels,
                              uint8_t   nof_beams,
                              uint8_t   tile_per_station,
                              uint16_t  nof_stations,
                              uint8_t   nof_polarisations,
                              uint16_t  start_station_id)
{
    configuration.nof_antennas      = nof_antennas;
    configuration.nof_channels      = nof_channels;
    configuration.nof_beams         = nof_beams;
    configuration.nof_polarisations = nof_polarisations;
    configuration.nof_stations      = nof_stations;
    configuration.tile_per_station  = tile_per_station;
    configuration.start_station_id  = start_station_id;
}

// Start network receiver
RESULT startReceiver(const char *interface, unsigned frame_size,
                      unsigned frames_per_block, unsigned nof_blocks)
{

    // Check if telescope is initialised
    if (configuration.nof_antennas == 0)
        return FAILURE;

    // Create network thread instance
    struct recv_params params;
    params.frame_size       = frame_size;
    params.frames_per_block = frames_per_block;
    params.nofblocks        = nof_blocks;

    // Copy interface name
    char hw_interface[6];
    strcpy(hw_interface, interface);

    // Create and initialise network receiver;
    try {
        receiver = new NetworkReceiver(hw_interface, params);
        receiver -> startThread();
    }
    catch (...)
    {
        return FAILURE;
    }

    return SUCCESS;
}

// Add receiver port
RESULT addReceiverPort(unsigned short port)
{
    if (receiver != NULL)
    {
        receiver->addPort(port);
        return SUCCESS;
    }
    else
        return RECEIVER_UNINITIALISED;
}

// Add and start raw data consumer
RESULT startRawConsumer(uint32_t samples_per_buffer)
{
    // Check if receiver is initialised
    if (receiver == NULL)
        return RECEIVER_UNINITIALISED;

    // Check if an antenna data consumer was already initialised
    map<DATA_TYPE, DataConsumer *>::iterator it;
    it = consumers.find(RAW_DATA);
    if (it != consumers.end())
        return CONSUMER_ALREADY_INITIALISED;

    try {
        // Create consumer instance
        AntennaData *antenna_data = new AntennaData(configuration.nof_antennas,
                                                    samples_per_buffer,
                                                    configuration.tile_per_station,
                                                    configuration.nof_stations,
                                                    configuration.nof_polarisations,
                                                    configuration.start_station_id);

        // Set receive thread to consumer
        antenna_data -> setReceiver(receiver);

        // Start consumer
        antenna_data -> startThread();

        // Add consumer to consumers map
        consumers[RAW_DATA] = antenna_data;
    }
    catch(...) {
        return FAILURE;
    }

    return SUCCESS;
}

// Add and start channel data consumer
RESULT startChannelConsumer(uint32_t nof_samples, uint16_t channels_per_packet,
                            uint16_t antennas_per_packet, uint16_t samples_per_packet,
                            uint8_t  continuous_mode)
{
    // Check if receiver is initialised
    if (receiver == NULL)
        return RECEIVER_UNINITIALISED;

    // Check if an antenna data consumer was already initialised
    map<DATA_TYPE, DataConsumer *>::iterator it;
    it = consumers.find(CHANNELISED_DATA);
    if (it != consumers.end())
        return CONSUMER_ALREADY_INITIALISED;

    try {
        // Create consumer instance
        ChannelisedData *channel_data = new ChannelisedData(configuration.nof_stations,
                                                            configuration.tile_per_station,
                                                            configuration.nof_channels,
                                                            nof_samples,
                                                            configuration.nof_antennas,
                                                            configuration.nof_polarisations,
                                                            channels_per_packet,
                                                            antennas_per_packet,
                                                            samples_per_packet,
                                                            configuration.start_station_id,
                                                            continuous_mode);

        // Set receive thread to consumer
        channel_data -> setReceiver(receiver);

        // Start consumer
        channel_data -> startThread();

        // Add consumer to consumers map
        consumers[CHANNELISED_DATA] = channel_data;
    }
    catch(...) {
        return FAILURE;
    }

    return SUCCESS;
}

// And and start beam data consumer
RESULT startBeamConsumer(uint32_t nof_samples, uint16_t samples_per_packet)
{
    // Check if receiver is initialised
    if (receiver == NULL)
        return RECEIVER_UNINITIALISED;

    // Check if an antenna data consumer was already initialised
    map<DATA_TYPE, DataConsumer *>::iterator it;
    it = consumers.find(BEAMFORMED_DATA);
    if (it != consumers.end())
        return CONSUMER_ALREADY_INITIALISED;

    try {
        // Create consumer instance
        BeamformedData *beam_data = new BeamformedData(configuration.tile_per_station * configuration.nof_stations,
                                                       configuration.nof_channels,
                                                       nof_samples,
                                                       configuration.nof_beams,
                                                       configuration.nof_polarisations,
                                                       samples_per_packet,
                                                       configuration.start_station_id,
                                                       configuration.tile_per_station);

        // Set receive thread to consumer
        beam_data -> setReceiver(receiver);

        // Start consumer
        beam_data -> startThread();

        // Add consumer to consumers map
        consumers[BEAMFORMED_DATA] = beam_data;
    }
    catch(...) {
        return FAILURE;
    }

    return SUCCESS;
}

// Set raw consumer callback
RESULT setRawConsumerCallback(DataCallback callback)
{
    // Check if receiver is initialised
    if (receiver == NULL)
        return RECEIVER_UNINITIALISED;

    // Check if an antenna data consumer was already initialised
    map<DATA_TYPE, DataConsumer *>::iterator it;
    it = consumers.find(RAW_DATA);
    if (it == consumers.end())
        return CONSUMER_NOT_INITIALISED;

    // Get consumer pointer
    DataConsumer *consumer = it -> second;

    // Try to set callback
    try  {
        consumer->setCallback(callback);
    }
    catch(...)     {
        return FAILURE;
    }

    return SUCCESS;
}

// Set channel consumer callback
RESULT setChannelConsumerCallback(DataCallback callback)
{
    // Check if receiver is initialised
    if (receiver == NULL)
        return RECEIVER_UNINITIALISED;

    // Check if an antenna data consumer was already initialised
    map<DATA_TYPE, DataConsumer *>::iterator it;
    it = consumers.find(CHANNELISED_DATA);
    if (it == consumers.end())
        return CONSUMER_NOT_INITIALISED;

    // Get consumer pointer
    DataConsumer *consumer = it -> second;

    // Try to set callback
    try  {
        consumer->setCallback(callback);
    }
    catch(...)     {
        return FAILURE;
    }

    return SUCCESS;
}

// Set beam consumer callback
RESULT setBeamConsumerCallback(DataCallback callback)
{
    // Check if receiver is initialised
    if (receiver == NULL)
        return RECEIVER_UNINITIALISED;

    // Check if an antenna data consumer was already initialised
    map<DATA_TYPE, DataConsumer *>::iterator it;
    it = consumers.find(BEAMFORMED_DATA);
    if (it == consumers.end())
        return CONSUMER_NOT_INITIALISED;

    // Get consumer pointer
    DataConsumer *consumer = it -> second;

    // Try to set callback
    try  {
        consumer->setCallback(callback);
    }
    catch(...)     {
        return FAILURE;
    }

    return SUCCESS;
}

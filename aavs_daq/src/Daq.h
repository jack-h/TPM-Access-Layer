//
// Created by Alessio Magro on 05/11/2015.
//

#ifndef DAQ_API_H
#define DAQ_API_H

#include "NetworkReceiver.h"
#include "AntennaData.h"
#include "ChannelisedData.h"
#include "BeamformedData.h"

#include <stdint.h>

// Enumeration to defined data types
typedef enum {
    RAW_DATA = 1, CHANNELISED_DATA = 2, BEAMFORMED_DATA = 3
} DATA_TYPE;

// Return type for most of the function calls, specifying whether the call
// succeeded or failed
typedef enum {
    SUCCESS = 0, FAILURE = -1,
    RECEIVER_UNINITIALISED = -2,
    CONSUMER_ALREADY_INITIALISED = -3,
    CONSUMER_NOT_INITIALISED = -4
} RESULT;

// Structure defining telescope configuration
typedef struct RECEIVER_CONFIGURATION {
    uint16_t nof_antennas;
    uint16_t nof_channels;
    uint8_t nof_beams;
    uint8_t tile_per_station;
    uint16_t nof_stations;
    uint8_t nof_polarisations;
    uint16_t start_station_id;
} RECEIVER_CONFIGURATION;

extern "C" {

// set global parameters / telescope setup
void setReceiverConfiguration(uint16_t nof_antennas,
                              uint16_t nof_channels,
                              uint8_t nof_beams,
                              uint8_t tile_per_station,
                              uint16_t nof_stations,
                              uint8_t nof_polarisations,
                              uint16_t start_station_id);

// Start network receiver
RESULT startReceiver(const char *interface, uint32_t frame_size,
                     uint32_t frames_per_block, uint32_t nof_blocks);

// Add destination port to receiver thread
RESULT addReceiverPort(unsigned short port);

// Create and start raw data consumer
RESULT startRawConsumer(uint32_t samples_per_buffer);

// Create and start channel data consumer
RESULT startChannelConsumer(uint32_t nof_samples,
                            uint16_t channels_per_packet,
                            uint16_t antennas_per_packet,
                            uint16_t samples_per_packet,
                            uint8_t  continuous_mode = 0);

// Create and start bram data consumer
RESULT startBeamConsumer(uint32_t nof_samples, uint16_t samples_per_packet);

// Set raw consumer callback
RESULT setRawConsumerCallback(DataCallback callback);

// Set channel consumer callback
RESULT setChannelConsumerCallback(DataCallback callback);

// Set beam consumer callback
RESULT setBeamConsumerCallback(DataCallback callback);

}

#endif //DAQ_API_H

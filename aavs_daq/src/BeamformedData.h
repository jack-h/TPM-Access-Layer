//
// Created by Alessio Magro on 10/11/2015.
//

#ifndef BEAMFORMEDDATA_H
#define BEAMFORMEDDATA_H

#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>

#include "DataConsumer.h"

// ----------------------- Antenna Data Container and Helpers ---------------------------------
struct BeamInfo
{
    double   timestamp;
    uint32_t first_sample_index;
};

// Class which will hold the raw antenna data
template <class T> class BeamDataContainer
{
public:
    // Class constructor
    BeamDataContainer(uint16_t nof_tiles,
                      uint32_t nof_samples, uint16_t nof_channels,
                      uint8_t nof_pols)
    {
        // Set local variables
        this -> nof_samples  = nof_samples;
        this -> nof_tiles    = nof_tiles;
        this -> nof_channels = nof_channels;
        this -> nof_pols     = nof_pols;

        // Allocate buffer
        buffer_ptr = (T *) malloc(nof_tiles * nof_samples * nof_channels * nof_pols * sizeof(T));

        buffer = (T **) malloc(nof_tiles * nof_pols * sizeof(T*));
        for(unsigned i = 0; i < nof_tiles * nof_pols; i++)
            buffer[i] = buffer_ptr + i * nof_samples * nof_channels;

        // Set up antenna information
        beam_info = (struct BeamInfo *) malloc(nof_tiles * nof_pols * sizeof(struct BeamInfo));

        // Reset antenna information
        clear();

        // Create output file
        // TODO: Make this proper
        output_fd = open("beam_output.dat", O_WRONLY | O_CREAT | O_SYNC | O_TRUNC, S_IRUSR | S_IRGRP | S_IROTH);

        if (output_fd < 0)
        {
            perror("Could not create file\n");
            return;
        }
    }

public:
    // Set callback function
    void setCallback(DataCallback callback)
    {
        this -> callback = callback;
    }

    // Add data to buffer
    void add_data(uint16_t tile, uint8_t pol, uint32_t start_sample_index, T* data_ptr, double timestamp)
    {
        // Get pointer to buffer location where data will be placed
        T* ptr = buffer[tile * nof_pols + pol] + start_sample_index * nof_channels;

        // Copy data to buffer
        memcpy(ptr, data_ptr, nof_channels * sizeof(T));

        // Update timing
        if (beam_info[tile].first_sample_index > start_sample_index)
        {
            beam_info[tile].timestamp = timestamp;
            beam_info[tile].first_sample_index = start_sample_index;
        }
    }

    //  Clear buffer and antenna information
    void clear()
    {
        // Clear buffer, set all content to 0
        memset(buffer_ptr, 0, nof_tiles * nof_pols * nof_channels * nof_samples * sizeof(T));

        // Clear AntennaInfo
        for(unsigned i = 0; i < nof_tiles * nof_pols; i++)
        {
            beam_info[i].first_sample_index = UINT32_MAX;
            beam_info[i].timestamp = 0;
        }
    }

    // Save data to disk
    void persist_container()
    {
        // If a callback is defined, call it and return
        if (this->callback != NULL)
        {
            callback((int8_t *) buffer_ptr, beam_info[0].timestamp);
            clear();
            return;
        }

        write(output_fd, buffer_ptr, sizeof(T) * nof_channels * nof_samples * nof_tiles * nof_pols);
        fsync(output_fd);

        printf("Written beam to file\n");

        // Clear container after persisting
        clear();
    }


private:
    // Parameters
    uint16_t nof_tiles;
    uint32_t nof_samples;
    uint16_t nof_channels;
    uint8_t  nof_pols;

    // Data container
    T *buffer_ptr;
    T **buffer;

    // Callback function
    DataCallback callback;

    // Timestamps for each beam
    BeamInfo *beam_info;

    // File descriptor
    int output_fd;
};

/* This class is responsible for consuming beam SPEAD packets coming out of TPMs
 * The consumer is responsible of creating the ring buffer to which the data
 * will be pushed by the network thread.
 */

class BeamformedData : public DataConsumer
{
public:
    // Empty class constructor
    BeamformedData();

    // Parametrised class constructor
    BeamformedData(uint16_t nof_tiles,
                   uint16_t nof_channels,
                   uint32_t nof_samples,
                   uint16_t nof_beams,
                   uint8_t  nof_pols,
                   uint16_t samples_per_packet,
                   uint16_t start_station_id,
                   uint16_t tiles_per_station);

    // Class destructor
    ~BeamformedData();

protected:
    // Packet filtering function to be passed to network thread
    static inline bool packetFilter(unsigned char* udp_packet);

    // Main thread event loop
    void threadEntry();

private:
    // Initialise ring buffer
    void initialiseRingBuffer(size_t packet_size, size_t nofcells);

    // Grab SPEAD packet from buffer and process
    bool getPacket();

    // Override setDataCallback
    void setCallback(DataCallback callback);

private:

    // AntennaInformation object
    BeamDataContainer<complex_8t> *container;

    // Two conditions will result in the buffering process exiting:
    // 1. Ring buffer timeout, which means that we reached the end of the data stream
    // 2. Packet index of this packet is greater than the number of samples in the buffer
    double reference_time = 0;
    uint32_t current_packet_index = 0;
};

#endif // BEAMFORMEDDATA_H

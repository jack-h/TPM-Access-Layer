//
// Created by Alessio Magro on 28/08/2015.
//

#ifndef CHANNELISED_DATA_H
#define CHANNELISED_DATA_H

#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>

#include "DataConsumer.h"

// ----------------------- Antenna Data Container and Helpers ---------------------------------
struct ChannelInfo
{
    double   timestamp;
    uint32_t first_sample_index;
};

// Class which will hold the raw antenna data
template <class T> class ChannelDataContainer
{
public:
    // Class constructor
    ChannelDataContainer(uint16_t nof_stations, uint16_t nof_tiles, uint16_t nof_antennas,
                         uint32_t nof_samples, uint16_t nof_channels, uint8_t nof_pols)
    {
        // Set local variables
        this -> nof_antennas = nof_antennas;
        this -> nof_stations = nof_stations;
        this -> nof_samples  = nof_samples;
        this -> nof_tiles    = nof_tiles;
        this -> nof_pols     = nof_pols;
        this -> nof_channels = nof_channels;

        // Allocate buffer
        buffer_ptr = (T *) malloc(nof_stations * nof_tiles * nof_channels * nof_samples * nof_antennas * nof_pols * sizeof(T));

        buffer = (T ****) malloc(nof_stations * sizeof(T***));
        for(unsigned i = 0; i < nof_stations; i++)
        {
            buffer[i] = (T***) malloc(nof_tiles * sizeof(T**));
            for (unsigned j = 0; j < nof_tiles; j++)
                buffer[i][j] = (T**) malloc(nof_channels * sizeof(T*));
        }

        // Set up buffer pointers
        for (unsigned i = 0; i < nof_stations; i++)
            for(unsigned j = 0; j < nof_tiles; j++)
                for(unsigned k = 0; k < nof_channels; k++)
                    buffer[i][j][k] = buffer_ptr + (i * (nof_tiles * nof_channels) +
                                                    j * nof_channels + k) * nof_samples * nof_antennas * nof_pols;

        // Set up antenna information
        channel_info = (struct ChannelInfo ***) malloc(nof_stations * sizeof(struct ChannelInfo **));
        for(unsigned i = 0; i < nof_stations; i++)
        {
            channel_info[i] = (struct ChannelInfo **) malloc(nof_tiles * sizeof(struct ChannelInfo *));
            for(unsigned j = 0; j < nof_tiles; j++)
                channel_info[i][j] = (struct ChannelInfo *) malloc(nof_channels * sizeof(struct ChannelInfo));
        }

        // Reset antenna information
        clear();
    }

public:

    // Set callback function
    void setCallback(DataCallback callback)
    {
        this -> callback = callback;
    }

    // Add data to buffer
    void add_data(uint16_t station, uint16_t tile, uint16_t channel, uint32_t start_sample_index,
                  uint32_t nof_samples, uint8_t pol_id, T *data_ptr, double timestamp)
    {
        // Get pointer to buffer location where data will be placed
        T* ptr = buffer[station][tile][channel] + start_sample_index * nof_pols * nof_antennas;

        // Copy data to buffer
//        memcpy(ptr, data_ptr, nof_samples * nof_antennas * nof_pols * sizeof(T));

        // TEMPORARY: For AAVS0.5, X and Y pols will be received from separate FPGAs, so we have to
        //            interleave them for now
        for(unsigned i = 0; i < nof_samples * nof_antennas; i++)
        {
            ptr[i * 2 + pol_id] = data_ptr[i];
        }

        // Update timing
        if (channel_info[station][tile][channel].first_sample_index > start_sample_index)
        {
            channel_info[station][tile][channel].timestamp = timestamp;
            channel_info[station][tile][channel].first_sample_index = start_sample_index;
        }
    }

    //  Clear buffer and antenna information
    void clear()
    {
        // Clear buffer, set all content to 0
        memset(buffer_ptr, 0, nof_stations * nof_tiles * nof_channels * nof_samples * nof_antennas * nof_pols * sizeof(T));

        // Clear AntennaInfo
        for(unsigned i = 0; i < nof_stations; i++)
            for(unsigned j = 0; j < nof_tiles; j++)
                for(unsigned k = 0; k < nof_channels; k++)
                {
                    channel_info[i][j][k].first_sample_index = UINT32_MAX;
                    channel_info[i][j][k].timestamp = 0;
                }
    }

    // Save data to disk
    void persist_container()
    {
        // If a callback is defined, call it and return
        if (this->callback != NULL)
        {
            callback((int8_t *) buffer_ptr, channel_info[0][0][0].timestamp);
            return;
        }

        // TODO: Make this proper
        int fd = open("channel_output.dat", O_RDWR | O_CREAT | O_SYNC, S_IRUSR | S_IRGRP | S_IROTH);

        if (fd < 0)
        {
            perror("Could not create file\n");
            return;
        }

        write(fd, buffer_ptr, nof_stations * nof_tiles * nof_channels * nof_samples * nof_antennas * nof_pols * sizeof(T));
        fsync(fd);
        close(fd);

        printf("Written to file (%ld bytes)\n", nof_stations * nof_tiles * nof_channels * nof_samples * nof_antennas * nof_pols * sizeof(T));
    }


private:
    // Parameters
    uint16_t nof_stations;
    uint16_t nof_tiles;
    uint16_t nof_antennas;
    uint32_t nof_samples;
    uint16_t nof_channels;
    uint8_t  nof_pols;

    // Data container
    T *buffer_ptr;
    T ****buffer;

    // Callback function
    DataCallback callback;

    // Timestamps for each station/tile/antenna
    ChannelInfo ***channel_info;
};

/* This class is responsible for consuming channel SPEAD packets coming out of TPMs to be used
 * for calibration. The consumer is responsible of creating the ring buffer to which the data
 * will be pushed by the network thread.
 */

class ChannelisedData : public DataConsumer
{
public:
    // Empty class constructor
    ChannelisedData();

    // Parametrised class constructor
    ChannelisedData(uint16_t nof_stations, uint16_t nof_tiles, uint16_t nof_channels,
                    uint32_t nof_samples, uint16_t nof_antennas, uint8_t nof_pols,
                    uint16_t channels_per_packet, uint16_t antennas_per_packet,
                    uint16_t samples_per_packet, uint16_t start_station_id);

    // Class destructor
    ~ChannelisedData();


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
    ChannelDataContainer<complex_8t> *container;
};


#endif // CHANNELISED_DATA_H

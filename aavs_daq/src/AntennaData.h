//
// Created by Alessio Magro on 01/10/2015.
//

#ifndef ANTENNADATA_H
#define ANTENNADATA_H

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <float.h>
#include <unistd.h>
#include "NetworkReceiver.h"
#include "RealTimeThread.h"
#include "DataConsumer.h"

// ----------------------- Antenna Data Container and Helpers ---------------------------------
struct AntennaInfo
{
    double   timestamp;
    uint32_t first_sample_index;
};

// Class which will hold the raw antenna data
template <class T> class AntennaDataContainer
{
public:
    // Class constructor
    AntennaDataContainer(uint16_t nof_stations, uint16_t nof_tiles, uint16_t nof_antennas,
                         uint32_t nof_samples, uint8_t nof_pols)
    {
        // Set local variables
        this -> nof_antennas = nof_antennas;
        this -> nof_stations = nof_stations;
        this -> nof_samples  = nof_samples;
        this -> nof_tiles    = nof_tiles;
        this -> nof_pols     = nof_pols;

        // Allocate buffer
        buffer_ptr = (T *) malloc(nof_stations * nof_tiles * nof_antennas * nof_samples * nof_pols * sizeof(T));

        buffer = (T ****) malloc(nof_stations * sizeof(T***));
        for(unsigned i = 0; i < nof_stations; i++)
        {
            buffer[i] = (T***) malloc(nof_tiles * sizeof(T**));
            for(unsigned j = 0; j < nof_tiles; j++)
                buffer[i][j] = (T**) malloc(nof_antennas * sizeof(T*));
        }

        // Set up buffer pointers
        for (unsigned i = 0; i < nof_stations; i++)
            for(unsigned j = 0; j < nof_tiles; j++)
                for(unsigned k = 0; k < nof_antennas; k++)
                    buffer[i][j][k] = buffer_ptr + (i * (nof_tiles * nof_antennas * nof_samples) +
                                                    j * (nof_antennas * nof_samples) +
                                                    k * nof_samples) * nof_pols;

        // Set up antenna information
        antenna_info = (struct AntennaInfo ***) malloc(nof_stations * sizeof(struct AntennaInfo **));
        for(unsigned i = 0; i < nof_stations; i++)
        {
            antenna_info[i] = (struct AntennaInfo **) malloc(nof_tiles * sizeof(struct AntennaInfo *));
            for(unsigned j = 0; j < nof_tiles; j++)
                antenna_info[i][j] = (struct AntennaInfo *) malloc(nof_antennas * sizeof(struct AntennaInfo));
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
    void add_data(uint16_t station, uint16_t tile, uint16_t antenna, uint32_t start_sample_index,
                  uint32_t nof_samples, uint8_t pol_id, T *data_ptr, double timestamp)
    {
        // Get pointer to buffer location where data will be placed
        T* ptr = buffer[station][tile][antenna] + start_sample_index * nof_pols;

        // Copy data to buffer
        // memcpy(ptr, data_ptr, nof_samples * nof_pols * sizeof(T));

        // TEMPORARY: For AAVS0.5, X and Y pols will be received from separate FPGAs, so we have to
        //            interleave them for now
        for(unsigned i = 0; i < nof_samples; i++)
            ptr[i * 2 + pol_id] = data_ptr[i];

        // Update timing
        if (antenna_info[station][tile][antenna].first_sample_index > start_sample_index)
        {
            antenna_info[station][tile][antenna].timestamp = timestamp;
            antenna_info[station][tile][antenna].first_sample_index = start_sample_index;
        }

    }

    //  Clear buffer and antenna information
    void clear()
    {
        // Clear buffer, set all content to 0
        memset(buffer_ptr, 0, nof_stations * nof_tiles * nof_antennas * nof_samples * nof_pols * sizeof(T));

        // Clear AntennaInfo
        for(unsigned i = 0; i < nof_stations; i++)
            for(unsigned j = 0; j < nof_tiles; j++)
                for(unsigned k = 0; k < nof_antennas; k++)
                {
                    antenna_info[i][j][k].first_sample_index = UINT32_MAX;
                    antenna_info[i][j][k].timestamp = 0;
                }
    }

    // Save data to disk
    void persist_container()
    {
        // If a callback is defined, call it and return
        if (this->callback != NULL)
        {
            callback((int8_t *) buffer_ptr, antenna_info[0][0][0].timestamp);
            clear();
            return;
        }

        // TODO: Make this proper
        int fd = open("antenna_output.dat", O_WRONLY | O_CREAT | O_SYNC | O_TRUNC, S_IRUSR | S_IRGRP | S_IROTH);

        if (fd < 0)
        {
            perror("Could not create file\n");
            return;
        }

        write(fd, buffer_ptr, sizeof(T) * nof_stations * nof_antennas * nof_samples * nof_pols * nof_tiles);
        fsync(fd);
        close(fd);

        printf("Written antenna to file\n");
    }


private:
    // Parameters
    uint16_t nof_stations;
    uint16_t nof_tiles;
    uint16_t nof_antennas;
    uint32_t nof_samples;
    uint8_t  nof_pols;

    // Data container
    T *buffer_ptr;
    T ****buffer;

    // Callback
    DataCallback callback = NULL;

    // Timestamps for each station/tile/antenna
    AntennaInfo ***antenna_info;
};

/* This class is responsible for consuming raw antenna SPEAD packets coming out of TPMs.
 * The consumer is responsible of creating the ring buffer to which the data
 * will be pushed by the network thread.
 */
class AntennaData: public DataConsumer
{

public:
    // Empty class constructor
    AntennaData();

    // Parametrised class constructor
    AntennaData(uint16_t nof_antennas,
                uint32_t samples_per_buffer,
                uint8_t  tiles_per_station,
                uint16_t  nof_stations,
                uint8_t  nof_pols,
                uint16_t start_station_id);

    // Class destructor
    ~AntennaData();

    // Override setDataCallback
    void setCallback(DataCallback callback);

protected:
    // Packet filtering function to be passed to network thread
    static inline bool packetFilter(unsigned char* udp_packet);

    // Main thread event loop
    void threadEntry();

protected:
    // Initialise ring buffer
    void initialiseRingBuffer(size_t packet_size, size_t nofcells);

    // Grab SPEAD packet from buffer and process
    bool getPacket();

private:

    // AntennaInformation object
    AntennaDataContainer<uint8_t> *container;
};

#endif // ANTENNADATA_H

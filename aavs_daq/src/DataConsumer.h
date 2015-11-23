//
// Created by lessju on 10/11/2015.
//

#include "RealTimeThread.h"
#include "NetworkReceiver.h"

#ifndef DATACONSUMER_H
#define DATACONSUMER_H

// Structure representing complex 8-bit values
struct complex_8t
{
    signed char x;
    signed char y;
};

// Define function pointer template for callbacks
// First parameter is pointer to data type
// Second parameter is the timestamp of the first sample in the buffer
typedef void (*DataCallback)(int8_t * data, double timestamp);

// Data Consumer abstract class
class DataConsumer: public RealTimeThread
{

public:
    // Set network receiver
    void setReceiver(NetworkReceiver *receiver) {this -> receiver = receiver;}

    // --------------------- Getters -----------------------------
public:
    // Get number of antenna per packet
    uint16_t getNumberOfAntennas() { return nof_antennas; }

    // Get number of antenna per packet
    uint32_t getSamplesPerBuffer() { return samples_per_buffer; }

    // Get number of antenna per packet
    uint32_t getTilesPerStation() { return tiles_per_station; }

    // Get number of antenna per packet
    uint16_t getNumberOfStations() { return nof_stations; }

    // Get number of beams
    uint16_t getNumberOfBeams() { return nof_beams; }

    // Get number of antenna per packet
    uint16_t getStartStationId() { return start_station_id; }

    // Get number of antenna per packet
    uint16_t getAntennasPerPacket() { return nof_antennas; }

    // Get number of antenna per packet
    uint16_t getChannelsPerPacket() { return channels_per_packet; }

    // Get number of antenna per packet
    uint32_t getSamplesPerPacket() { return samples_per_packet; }

    // Get number of antenna per packet
    uint16_t getPolsPerPacket() { return nof_pols; }

    // Get number of antenna per packet
    uint32_t setSamplesPerSecond() { return nof_samples; }

    // --------------------- Setters -----------------------------
public:
    // Set number of antenna per packet
    void setNumberOfAntennas(uint16_t value) { nof_antennas = value; }

    // Set number of beams
    void setNumberOfBeams(uint16_t value) {nof_beams = value; }

    // Set number of antenna per packet
    void setSamplesPerBuffer(uint16_t value) { samples_per_buffer = value; }

    // Set number of antenna per packet
    void setTilesPerStation(uint16_t value) { tiles_per_station= value; }

    // Set number of antenna per packet
    void setPolsPerPacket(uint8_t value) { nof_stations = value; }

    // Set number of antenna per packet
    void setStartStationId(uint8_t value) { start_station_id = value; }

    // Set number of antenna per packet
    void setAntennasPerPacket(uint16_t value) { nof_antennas = value; }

    // Set number of antenna per packet
    void setChannelsPerPacket(uint16_t value) { channels_per_packet = value; }

    // Set number of antenna per packet
    void setSamplesPerPacket(uint16_t value) { samples_per_packet= value; }

    // Set number of samples per second
    void setSamplesPerSecond(uint16_t value) { nof_samples = value; }

protected:
    // Initialise ring buffer
    virtual void initialiseRingBuffer(size_t packet_size, size_t nofcells) = 0;

    // Grab SPEAD packet from buffer and process
    virtual bool getPacket() = 0;

    virtual void threadEntry() = 0;

public:
    virtual void setCallback(DataCallback callback) = 0;

protected:
    // Pointer to ring buffer
    RingBuffer *ring_buffer;

    // Local packet container
    uint8_t *packet;

    // Pointer to network receiver
    NetworkReceiver *receiver;

    // Packet content information
    uint16_t nof_antennas;        // Number of antennas per tile
    uint32_t samples_per_buffer;  // Number of samples per buffer
    uint16_t tiles_per_station;   // Number of tiles per station
    uint16_t nof_stations;        // Number of stations
    uint8_t  nof_pols;            // Number of polarisations
    uint16_t nof_beams;           // Number of beams
    uint16_t start_station_id;    // Start station id
    uint16_t nof_tiles;           // Number of tiles
    uint16_t nof_channels;        // Number of channels
    uint16_t channels_per_packet; // Number of channels per packet
    uint16_t samples_per_packet;  // Number of time samples per packet
    uint32_t nof_samples;         // Number of time samples per second
    uint16_t antennas_per_packet; // Antennas per packet
};

#endif // DATACONSUMER_H

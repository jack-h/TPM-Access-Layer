//
// Created by Alessio Magro on 01/10/2015.
//

#include "AntennaData.h"
#include "Utils.h"

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

// Class constructor
AntennaData::AntennaData()
{
    // Initialise ring buffer (use default values, assume jumbo frames)
    initialiseRingBuffer(SPEAD_MAX_PACKET_LEN, (size_t) 128e6 / SPEAD_MAX_PACKET_LEN);
}

// Class constructor with parameters
AntennaData::AntennaData(uint16_t nof_antennas, uint32_t samples_per_buffer,
                         uint8_t tiles_per_station, uint16_t nof_stations,
                         uint8_t nof_pols, uint16_t start_station_id)
{
    // Set local values
    this -> nof_antennas       = nof_antennas;
    this -> samples_per_buffer = samples_per_buffer;
    this -> tiles_per_station  = tiles_per_station;
    this -> nof_stations       = nof_stations;
    this -> nof_pols           = nof_pols;
    this -> start_station_id   = start_station_id;

    // Calculate packet size and approximate required number of cells in ring buffer
    // TODO: This needs to be calculated properly, has hardcoded values for current firmware iteration
    size_t packet_size = (size_t) 1024 + (16 + 10 * 8 + 8) * 2;

    // Create ring buffer
    initialiseRingBuffer(packet_size, (size_t) 128e6 / packet_size);

    // Create antenna container
    container = new AntennaDataContainer<uint8_t>(nof_stations, tiles_per_station, nof_antennas,
                                                  samples_per_buffer, nof_pols);
}

// Class destructor
AntennaData::~AntennaData()
{
    delete ring_buffer;
}

// Initialise ring buffer
void AntennaData::initialiseRingBuffer(size_t packet_size, size_t nofcells)
{
    // Create ring buffer
    // TODO: Calculate size of ring buffer by getting cache size and assigning it to a multiple of it
    ring_buffer = new RingBuffer(packet_size, nofcells);

    // Set receiver to NULL
    receiver = NULL;
}

// Set callback
void AntennaData::setCallback(DataCallback callback)
{
    this -> container -> setCallback(callback);
}

// Packet filter
// TODO: Implement proper filter
bool AntennaData::packetFilter(unsigned char *udp_packet)
{
    // Unpack SPEAD Header (or try to)
    uint64_t hdr = SPEAD_HEADER(udp_packet);

    // Check that this is in fact a SPEAD packet and that the correct
    // version is being used
    if ((SPEAD_GET_MAGIC(hdr) != SPEAD_MAGIC) ||
        (SPEAD_GET_VERSION(hdr) != SPEAD_VERSION) ||
        (SPEAD_GET_ITEMSIZE(hdr) != SPEAD_ITEM_PTR_WIDTH) ||
        (SPEAD_GET_ADDRSIZE(hdr) != SPEAD_HEAP_ADDR_WIDTH))
        return false;

    // Check whether the SPEAD packet contains antenna information
    return (SPEAD_ITEM_ID(SPEAD_ITEM(udp_packet, 8)) == 0x2000);
}

// Main event loop
void AntennaData::threadEntry()
{
    // Assign filtering function and ring buffer instance to network receiver
    // Receiver can be NULL for testing
    if (receiver != NULL)
        receiver->registerConsumer(ring_buffer, AntennaData::packetFilter);

    // Get L1 cacheline size
#ifdef _SC_LEVEL1_DCACHE_LINESIZE
    long cacheline_size = sysconf(_SC_LEVEL1_DCACHE_LINESIZE);
#else
    long cacheline_size = return 64;
#endif

    // Allocate buffer for incoming packet (size if maximum SPEAD packet length)
    // TODO: Perform checks on posix_memalign
    if (posix_memalign((void **) &packet, (size_t) cacheline_size, SPEAD_MAX_PACKET_LEN) < 0)
        packet = (uint8_t *) malloc(SPEAD_MAX_PACKET_LEN);

    // Infinite loop: process antenna data whenever it arrives
    while(1)
    {
        bool started_processing = false;
        // Continue processing packets until ring buffer times out
        while (1)
        {
            if (getPacket())
                started_processing = true;
            else if (started_processing)
            {
           //     printf("Finished processing raw data\n");
                break;
            }
        }

        // Finished receiving data, save buffer to disk
        container -> persist_container();
    }
}

bool AntennaData::getPacket()
{
    // Get next packet to process
    size_t packet_size = ring_buffer -> pull_timeout(packet, 2);

    // Check if the request timed out
    if (packet_size == SIZE_MAX)
        // Request timed out
        return false;

    printf("acquired packet\n");

    // This packet is a SPEAD packet, since otherwise it would not have
    // passed through the filter
    uint64_t hdr = SPEAD_HEADER(packet);

    uint32_t packet_index   = 0;
    uint32_t packet_counter = 0;
    uint64_t heap_offset = 0;
    uint64_t payload_length = 0;
    uint64_t sync_time = 0;
    uint64_t timestamp = 0;
    uint64_t timestamp_scale_offset = 0;
    uint64_t center_frequency_offset = 0;
    uint16_t start_antenna_id = 0;
    uint16_t nof_antennas = 0;
    uint16_t tile_id = 0;
    uint16_t station_id = 0;
    uint8_t  pol_id     = 0;
    uint32_t payload_offset = 0;

    // Get the number of items and get a pointer to the packet payload
    unsigned short nofitems = (unsigned short) SPEAD_GET_NITEMS(hdr);
    uint8_t *payload = packet + SPEAD_HEADERLEN + nofitems * SPEAD_ITEMLEN;

    // Loop over items to extract values
    for(unsigned i = 1; i <= nofitems; i++)
    {
        uint64_t item = SPEAD_ITEM(packet, i);
        switch (SPEAD_ITEM_ID(item))
        {
            case 0x0001:  // Heap counter
            {
                packet_counter = (uint32_t) (SPEAD_ITEM_ADDR(item) & 0xFFFFFF);       // 24-bits
                packet_index   = (uint32_t) ((SPEAD_ITEM_ADDR(item) >> 24) & 0xFFFF); // 16-bits
                break;
            }
            case 0x0003: // Heap offset
            {
                heap_offset = SPEAD_ITEM_ADDR(item);
                break;
            }
            case 0x0004: // Payload length
            {
                payload_length = SPEAD_ITEM_ADDR(item);
                break;
            }
            case 0x1027: // Sync time
            {
                sync_time = SPEAD_ITEM_ADDR(item);
                break;
            }
            case 0x1600: // Timestamp
            {
                timestamp = SPEAD_ITEM_ADDR(item);
                break;
            }
            case 0x1046: // Timestamp scale
            {
                timestamp_scale_offset = SPEAD_ITEM_ADDR(item);
                break;
            }
            case 0x1011: // Center frequency
            {
                center_frequency_offset = SPEAD_ITEM_ADDR(item);
                break;
            }
            case 0x2000: // Antenna information
            {
                uint64_t val = SPEAD_ITEM_ADDR(item);
                start_antenna_id = (uint16_t) ((val >> 8) & 0xFF);
                nof_antennas     = (uint16_t) (val & 0xFF);
                break;
            }
            case 0x2001: // Tile information
            {
                uint64_t val = SPEAD_ITEM_ADDR(item);
                station_id = (uint16_t) ((val >> 16) & 0xFFFF);
                tile_id    = (uint16_t) ((val >> 32) & 0xFF);
                pol_id     = (uint8_t)   (val & 0xFF);
                break;
            }
            case 0x3300: // Payload offset
            {
                payload_offset = (uint32_t) SPEAD_ITEM_ADDR(item);
                break;
            }
            default:
                printf("Unknown item 0x%#08x (%d of %d) \n", SPEAD_ITEM_ID(item), i, nofitems);
        }
    }

    // Read timestamp scale value
    double timestamp_scale = *((double *) (payload + timestamp_scale_offset));

    // Read center frequency
    double center_frequency = *((double *) payload + center_frequency_offset);

    // TODO: Remove this
    station_id = 0;
    tile_id    = 0;

    // Calculate number of samples in packet
    uint32_t nof_samples = (uint32_t) (payload_length - payload_offset);

    // We have processed the packet items, now comes the data
    container -> add_data(station_id - start_station_id, tile_id, start_antenna_id, packet_index * nof_samples,
                          nof_samples, pol_id, payload + payload_offset, sync_time + timestamp * timestamp_scale);

    // All done, return
    return true;
}



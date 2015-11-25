//
// Created by Alessio Magro on 10/11/2015.
//

#include "BeamformedData.h"
#include "Utils.h"


// Class constructor
BeamformedData::BeamformedData()
{
    // Initialise ring buffer (use default values, assume jumbo frames)
    initialiseRingBuffer(SPEAD_MAX_PACKET_LEN, (size_t) 128e6 / SPEAD_MAX_PACKET_LEN);
}

// Class constructor with parameters
BeamformedData::BeamformedData(uint16_t nof_tiles, uint16_t nof_channels, uint32_t nof_samples, uint16_t nof_beams,
                               uint8_t  nof_pols, uint16_t samples_per_packet, uint16_t start_station_id,
                               uint16_t tiles_per_station)
{
    // Set local values
    this -> nof_tiles          = nof_tiles;
    this -> nof_channels       = nof_channels;
    this -> nof_samples        = nof_samples;
    this -> nof_beams          = nof_beams;
    this -> nof_pols           = nof_pols;
    this -> samples_per_packet = samples_per_packet;
    this -> start_station_id   = start_station_id;
    this -> tiles_per_station  = tiles_per_station;

    // Calculate packet size and approximate required number of cells in ring buffer
    // Note that this assumes complex values with 8-bit components
    // TODO: This needs to be calculated properly, has hardcoded values for current firmware iteration
    size_t packet_size = (size_t) nof_channels * sizeof(complex_8t) + 16 + 10 * 8 + 8;;

    // Create ring buffer
    initialiseRingBuffer(packet_size, (size_t) 128e6 / packet_size);

    // Create channel container
    container = new BeamDataContainer<complex_8t>(nof_tiles, nof_samples, nof_channels, nof_pols);
}

// Class destructor
BeamformedData::~BeamformedData()
{
    delete ring_buffer;
}

// Initialise ring buffer
void BeamformedData::initialiseRingBuffer(size_t packet_size, size_t nofcells)
{
    // Create ring buffer
    // TODO: Calculate size of ring buffer by getting cache size and assigning it to a multiple of it
    ring_buffer = new RingBuffer(packet_size, nofcells);

    // Set receiver to NULL
    receiver = NULL;
}

// Set callback
void BeamformedData::setCallback(DataCallback callback)
{
    this -> container -> setCallback(callback);
}

// Packet filter
// TODO: Implement proper filter
bool BeamformedData::packetFilter(unsigned char *udp_packet)
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
    return (SPEAD_ITEM_ID(SPEAD_ITEM(udp_packet, 8)) == 0x3000);
}

// Main event loop
void BeamformedData::threadEntry()
{
    // Assign filtering function and ring buffer instance to network receiver
    // Receiver can be NULL for testing
    if (receiver != NULL)
        receiver->registerConsumer(ring_buffer, BeamformedData::packetFilter);

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
                printf("Finished processing beamformed data\n");
                break;
            }
        }

        // Finished receiving data, save buffer to disk
        container -> persist_container();
    }
}

bool BeamformedData::getPacket()
{
    // Get next packet to process
    size_t packet_size = ring_buffer -> pull_timeout(packet, 2);

    // Check if the request timed out
    if (packet_size == SIZE_MAX)
        // Request timed out
        return false;

    // This packet is a SPEAD packet, since otherwise it would not have
    // passed through the filter
    uint64_t hdr = SPEAD_HEADER(packet);

    uint32_t packet_index = 0;
    uint32_t packet_counter = 0;
    uint64_t heap_offset = 0;
    uint64_t payload_length = 0;
    uint64_t sync_time = 0;
    uint64_t timestamp = 0;
    uint64_t timestamp_scale_offset = 0;
    uint64_t center_frequency_offset = 0;
    uint16_t beam_id = 0;
    uint16_t frequency_id = 0;
    uint16_t tile_id = 0;
    uint16_t station_id = 0;
    uint16_t nof_included_antennas = 0;
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
                packet_counter  = (uint32_t) (SPEAD_ITEM_ADDR(item) & 0xFFFFFF);       // 24-bits
                packet_index    = (uint32_t) ((SPEAD_ITEM_ADDR(item) >> 24) & 0xFFFF); // 16-bits
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
            case 0x3000: // Beam and Frequency information
            {
                uint64_t val = SPEAD_ITEM_ADDR(item);
                beam_id      = (uint16_t) ((val >> 16) & 0xFFF);
                frequency_id = (uint16_t) (val & 0xFFF);
                break;
            }
            case 0x2003: // Tile and Station information
            {
                uint64_t val = SPEAD_ITEM_ADDR(item);
                tile_id    = (uint16_t) ((val >> 32) & 0xFF);
                station_id = (uint16_t) ((val >> 16) & 0xFFFF);
                nof_included_antennas = (uint16_t) (val & 0xFFFF);

                break;
            }
            case 0x3300: // Payload offset
            {
                payload_offset = (uint32_t) SPEAD_ITEM_ADDR(item);
                break;
            }
            default:
                printf("Unknown item %#010x (%d of %d) \n", SPEAD_ITEM_ID(item), i, nofitems);
        }
    }

    // Read timestamp scale value
    double timestamp_scale = *((double *) (payload + timestamp_scale_offset));

    // Read center frequency
    double center_frequency = *((double *) payload + center_frequency_offset);

    // TODO: Remove this
    station_id = 0;
    tile_id    = 0;

    double packet_time = sync_time + timestamp * timestamp_scale;

    // Check if packet belongs to current buffer
    if (reference_time == 0)
        reference_time = packet_time;

    if (packet_time < reference_time)
        // This packet belongs to the previous buffer, ignore
        return true;

    // Each packet contains one polarisations, all channels, one beam, one time sample

    // Check if packet index is smaller than stored packet index
    if (current_packet_index > 2 &&
        packet_index < (current_packet_index - 2))
    {
        // New buffer detected, persist current container
        container -> persist_container();

        // Update timestamp
        reference_time = packet_time;
    }

    // Update packet index
    current_packet_index = packet_index;


    // We have processed the packet items, now comes the data
    container -> add_data(nof_pols * ((station_id - start_station_id) * tiles_per_station + tile_id), beam_id,
                          packet_index, (complex_8t *) (payload + payload_offset), sync_time + timestamp * timestamp_scale);

    // All done, return
    return true;
}
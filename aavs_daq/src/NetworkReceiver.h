//
// Created by Alessio Magro on 26/08/2015.
//

#ifndef _NETWORKRECEIVER_H
#define _NETWORKRECEIVER_H

// Definitions to control network receiver execution
#define DEBUG
#define STATISTICS 
#define MAX_CONSUMERS 4

// Project includes
#include "RealTimeThread.h"
#include "RingBuffer.h"

// System includes
#include <linux/if_packet.h>
#include <linux/if_ether.h>

#include <stddef.h>
#include <stdint.h>

// ---------------------------------- Structure Definitions ---------------------------------

struct recv_params
{
    // These sizing fields should be initialized by the caller
    unsigned int frame_size;
    unsigned int frames_per_block;
    unsigned int nofblocks;
    unsigned int nofframes = 0;
};

struct ring
{
    struct iovec        *rd;
    uint8_t             *map;
    struct tpacket_req3 req;
};

struct block_desc
{
    uint32_t              version;
    uint32_t              offset_to_priv;
    struct tpacket_hdr_v1 h1;
};

// -------------------------------- Network Receiver Class ----------------------------------

class NetworkReceiver: public RealTimeThread
{
    public:
        // Default Network Receiver constructor
        // interface refers to the ethernet adapter to bind to
        // port specifies the port number to process packets from
        NetworkReceiver(char *interface, struct recv_params params);

        // Destructor
        ~NetworkReceiver();

        // Add a data consumer to the network receiver, together with a filtering function
        // which selects which packet to be pushed to the consumer (via an intermediary ring buffer)
        bool registerConsumer(RingBuffer *ring_buffer, bool (*filter)(unsigned char *udp_data));

        // Add a new port to receive from
        void addPort(unsigned short port) { this->ports[num_ports] = port; num_ports++; }

    protected:

        // Main thread event loop
        void threadEntry();

    private:
        // Initialise receiver
        void initialise();

    private:
        char               interface[6];    // Interface string name
        unsigned short     ports[16];       // Receive ports
        unsigned short     num_ports;       // Number of receive ports

        // Consumer variables (limited to 4 for now)
        uint8_t nof_consumers;
        RingBuffer *ring_buffers[MAX_CONSUMERS];
        bool (*filters[MAX_CONSUMERS])(unsigned char* udp_data);

        // Note: The receiver assumes that the
        int            sock = -1;       // Receive socket

        // Private definitions for packet_mmap
        struct recv_params params; // PACKET_MMAP parameters
        struct ring        ring;   // Structure containing ring buffer
};

#endif // _NETWORKRECEIVER_H

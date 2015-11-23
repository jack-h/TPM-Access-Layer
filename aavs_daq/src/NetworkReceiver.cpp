//
// Created by Alessio Magro on 26/08/2015.
/*
 * struct tpacket_req is defined in /usr/include/linux/if_packet.h and establishes a
 * circular buffer (ring) of unswappable memory. Being mapped in the capture process allows
 * reading the captured frames and related meta-information like timestamps without requiring a system call.
 *
 * Frames are grouped in blocks. Each block is a physically contiguous region of memory and holds
 * tp_block_size/tp_frame_size frames. The total number of blocks is tp_block_nr. Note that
 * tp_frame_nr is a redundant parameter because
 *     frames_per_block = tp_block_size/tp_frame_size
 * indeed, packet_set_ring checks that the following condition is true
 *     frames_per_block * tp_block_nr == tp_frame_nr
 *
 * Example
 *   tp_block_size= 4096
 *   tp_frame_size= 2048
 *   tp_block_nr  = 4
 *   tp_frame_nr  = 8
 * we will get the following buffer structure:
 *
 *        block #1                 block #2
 * +---------+---------+    +---------+---------+
 * | frame 1 | frame 2 |    | frame 3 | frame 4 |
 * +---------+---------+    +---------+---------+
 *
 * block #3                 block #4
 * +---------+---------+    +---------+---------+
 * | frame 5 | frame 6 |    | frame 7 | frame 8 |
 * +---------+---------+    +---------+---------+
 *
 * A frame can be of any size with the only condition it can fit in a block. A block can only hold an
 * integer number of frames, or in other words, a frame cannot be spawned across two blocks, so
 * there are some details you have to take into account when choosing the frame_size.
*/

// Project includes
#include "NetworkReceiver.h"
#include "Utils.h"

// System includes
#include <math.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <linux/ip.h>
#include <linux/udp.h>
#include <sys/poll.h>
#include <assert.h>
#include <netdb.h>

// Network Receiver constructor
NetworkReceiver::NetworkReceiver(char *interface, struct recv_params params)
{
    // Copy parameters to local variables
    strcpy(this->interface, interface);

    // Copy parameters
    this->params = params;
    this->num_ports = 0;

    // Initialise receiver
    initialise();

    // Initialise consumer-related variables
    for(unsigned i = 0; i < MAX_CONSUMERS; i++)
    {
        ring_buffers[i] = NULL;
        filters[i] = NULL;
    }
    nof_consumers = 0;
}

// NetworkReceiver Destructor
NetworkReceiver::~NetworkReceiver()
{
    // Check if socket is open, and if so close if
    if (sock != -1)
        close(sock);

    // Check if thread is running, and if so send signal to terminate and wait for thread to finish
    // munmap memory mapped region
    // free ring iovec
    // TODO
}

// Initialise network receiver
void NetworkReceiver::initialise()
{
    // Create raw socket
    if ((sock = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL))) < 0)
    {
#ifdef DEBUG
        perror("Could not create socket [requires root]");
        exit(-1);
#else
        // Use syslog
#endif
    }

    // Set socket packet version to use TPACKET_V3
    int v = TPACKET_V3;
    if (setsockopt(sock, SOL_PACKET, PACKET_VERSION, &v, sizeof(v)))
    {
#ifdef DEBUG
        perror("Could not set socket option for packet version");
        exit(-1);
#else
        // Use syslog
#endif
    }

    // Copy the interface name to ifreq structure
    struct ifreq s_ifr;
    strncpy(s_ifr.ifr_name, interface, sizeof(s_ifr.ifr_name));

    // Get interface index
    if (ioctl(sock, SIOCGIFINDEX, &s_ifr) < 0)
    {
#ifdef DEBUG
        perror("Couldn't get interface ID");
        exit(-1);
#else
        // Use syslog
#endif
    }

    // Fill sockaddr_ll struct to prepare for binding
    struct sockaddr_ll address;
    memset(&address, 0, sizeof(address));
    address.sll_family   = AF_PACKET;
    address.sll_protocol = 0x08;
    address.sll_ifindex  = s_ifr.ifr_ifindex;
    address.sll_hatype   = 0;
    address.sll_pkttype  = 0;
    address.sll_halen    = 0;

    // Bind socket to interface
    if(bind(sock, (struct sockaddr *) &address, sizeof(struct sockaddr_ll)) < 0)
    {
#ifdef DEBUG
        perror("bind()");
        exit(-1);
#else
        // use syslog
#endif
    }

    // Get page size (in bytes) to calculate tpacket_req parameters
#ifdef _SC_PAGESIZE
    long page_size = sysconf(_SC_PAGESIZE);
#else
    long page_size = 1024;
#endif

    // Set up PACKET_MMAP capturing mode. Parameters are set by caller
    memset(&ring.req, 0, sizeof(ring.req));
    ring.req.tp_frame_size = (unsigned int) ceil(params.frame_size / (double) page_size) * page_size;
    ring.req.tp_block_size = params.frames_per_block * ring.req.tp_frame_size;
    ring.req.tp_block_nr = params.nofblocks;
    ring.req.tp_frame_nr =  params.frames_per_block * params.nofblocks;
    ring.req.tp_retire_blk_tov = 60;
    ring.req.tp_feature_req_word = TP_FT_REQ_FILL_RXHASH;

    if (params.nofframes == 0)
        params.nofframes = ring.req.tp_frame_nr;

    // Set ring buffer on socket
    if (setsockopt(sock, SOL_PACKET, PACKET_RX_RING, &ring.req, sizeof(ring.req)) < 0)
    {
        close(sock);
#ifdef DEBUG
        perror("setsockopt()");
        exit(-1);
#else
        // use syslog
#endif
    }

    // Map kernel buffer to user space using mmap
    ring.map = (uint8_t*)  mmap(NULL, ring.req.tp_block_nr * ring.req.tp_block_size,
                                PROT_READ | PROT_WRITE, MAP_SHARED | MAP_LOCKED, sock, 0);
    if (ring.map == MAP_FAILED)
    {
        close(sock);
#ifdef DEBUG
        perror("Dammit mmap()");
        exit(-1);
#else
        // use syslog
#endif
    }

    // Allocate and prepare ring buffer
    ring.rd = (iovec *) malloc(ring.req.tp_block_nr * sizeof(*ring.rd));
    assert(ring.rd);
    for (unsigned i = 0; i < ring.req.tp_block_nr; ++i) {
        ring.rd[i].iov_base = ring.map + (i * ring.req.tp_block_size);
        ring.rd[i].iov_len = ring.req.tp_block_size;
    }

    // We are ready to start receiving data...
}

// Network Receiver main event loop
void NetworkReceiver::threadEntry()
{
    struct timespec tim, tim2;
    tim.tv_sec  = 0;
    tim.tv_nsec = 100;

#ifdef STATISTICS
    // When calculating statistics, we loop over a number of packets and calculate the required
    // metrics over this period
    struct timespec tps, tpe;
    long   processed_frames  = 0;
    long   processed_bytes   = 0;

    clock_gettime(CLOCK_REALTIME, &tps);
#endif

    // Run indefinitely
    for(unsigned i = 0;;)
    {
        // Fetch the next frame and check whether it is available for processing
        volatile struct block_desc *pbd = (struct block_desc *) ring.rd[i].iov_base;

        // Wait until data is available
        // For now just do a spin lock
        while((pbd->h1.block_status & TP_STATUS_USER) == 0)
        {
            nanosleep(&tim, &tim2); // Wait using nanosleep
        }

#ifdef DEBUG
	   if (pbd->h1.block_status & TP_STATUS_LOSING)
	   {
		    // Check if we are losing packets
        	struct tpacket_stats stats;
	        socklen_t size_sock = sizeof(tpacket_stats);
	        if (getsockopt(sock, SOL_PACKET, PACKET_STATISTICS, &stats, &size_sock) > -1)
	            printf("Dropped packets: [TP Drops: %d, TP packets: %d]\n", stats.tp_drops, stats.tp_packets);
	    }
#endif

        // With TPACKET version 3, the entire block is ready at this point, so we can process
        // multiple packets
        struct tpacket3_hdr *frame_header = (struct tpacket3_hdr *) ((uint8_t *) pbd + pbd->h1.offset_to_first_pkt);

        // Loop over all packets in block
        for(unsigned p = 0; p < pbd->h1.num_pkts; p++)
        {
            // Extract Ethernet Header
            struct ethhdr *eth_header  = (struct ethhdr *) ((uint8_t *) frame_header + frame_header ->tp_mac);

            // Extract IP Header
            struct iphdr  *ip_header   = (struct iphdr  *) ((uint8_t *) eth_header + ETH_HLEN);

            // Extract UDP header
            struct udphdr  *udp_header = (struct udphdr *) ((uint8_t *) ip_header + ip_header->ihl * 4);

            // Check whether this is a UDP packet and whether destination port is correct
            // Additional checks can be performed (eventually)
            unsigned port_index = 0;
            for(port_index = 0; port_index < this->num_ports; port_index++)
                if (ntohs(udp_header->dest) == this->ports[port_index])
                    break;

            if (ip_header->protocol != IPPROTO_UDP || port_index == this->num_ports)
            {
#ifdef DEBUG
//               printf("Invalid packet %d %d\n", ip_header->protocol, ntohs(udp_header->dest));
#endif
                // Proceed to next packet in block
                frame_header = (struct tpacket3_hdr *) ((uint8_t *) frame_header + frame_header->tp_next_offset);
                continue;
            }

            // Packet is UDP and correct destination port. Get UDP packet contents
            uint8_t *udp_packet = ((uint8_t *) udp_header) + sizeof(udphdr);

            // Go through consumers, if any
            bool processed = false;
            for(unsigned c = 0; c < nof_consumers; c++)
            {
                // Check if current consumer has a filtering function specified
                if ((filters[c] != NULL && filters[c](udp_packet)) || filters[c] == NULL)
                {
                    // Packet passed filtered, push to associated ring buffer
                    ring_buffers[c]->push(udp_packet, ntohs(udp_header->len) - sizeof(udphdr));
                    processed = true;  // Set packet as processed
                }
            }

            // Proceed to next packet
            frame_header = (struct tpacket3_hdr *) ((uint8_t *) frame_header + frame_header->tp_next_offset);

            // If c is equal to the number of consumer, then the packet was not suitable to any consumer
            // We exclude this from packet statistics
            if (!processed)
                continue;

#ifdef STATISTICS
            processed_frames++;
            processed_bytes += frame_header->tp_len;
#endif
        }

        // Tell kernel that the block has been processed and proceed to next block
        pbd->h1.block_status = TP_STATUS_KERNEL;
        i = (i + 1) % params.nofblocks;
#ifdef STATISTICS
        if (processed_frames > 1e5)
        {
            clock_gettime(CLOCK_REALTIME, &tpe);
            double duration = ((tpe.tv_sec - tps.tv_sec) + (tpe.tv_nsec - tps.tv_nsec) * 1e-9);
            printf("Frames per second: %.2lfk, data rate: %.2lfGb/s\n", (processed_frames * 1e-3) / duration,
                   (processed_bytes * 8 * 1e-9) / duration);

            // Reset statistics
            processed_frames = 0;
            processed_bytes  = 0;

            clock_gettime(CLOCK_REALTIME, &tps);
        }
#endif
    }
}

// Add a consumer to network receiver
bool NetworkReceiver::registerConsumer(RingBuffer *ring_buffer, bool (*filter)(unsigned char *))
{
    // NOTE: This section should be thread safe (in the rare case where more than a single consumer
    //       want to register at the same time
    // Check if the consumer limit has been reached
    if (nof_consumers >= MAX_CONSUMERS)
        return false;

    // Otherwise, add ring_buffer and associated filter function to network thread
    ring_buffers[nof_consumers] = ring_buffer;
    filters[nof_consumers] = filter;
    nof_consumers++;

    // All done, return
    return true;
}

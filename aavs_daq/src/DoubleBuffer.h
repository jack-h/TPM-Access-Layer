//
// Created by Alessio Magro on 04/09/2015.
//

#ifndef _DOUBLEBUFFER_H
#define _DOUBLEBUFFER_H

#include <stdint.h>
#include <cstddef>
#include <time.h>

// Define what data type to use
#ifdef USE_FLOAT
#define DSIZE sizeof(float) * 2
#else
#define DSIZE sizeof(uint8_t) * 2
#endif

/* This class implements a double buffering system between the correlator thread, which read SPEAD packets
 * from the ring buffer and the xGPU thread, which perform cross-correlation on the GPU. Locks are only required
 * at the buffer level, since writes are guaranteed to be non-conflicting (data is partitioned across packets)
 * and read will read in the entire buffer
 */

// Represents a single buffer in the double (or more) buffering system
struct buffer
{
    time_t   ref_time;  // The reference time of the second contained in the buffer
    bool     ready;     // Specifies whether the buffer is ready to be processed
    uint8_t  *data;     // Pointer to the buffer itself
};

class DoubleBuffer
{

public:
    // Default constructor
    DoubleBuffer(uint16_t nants, uint16_t nchans, uint32_t nsamp,
                 uint8_t npol, uint8_t nbuffers = 2);

private:
    // Allocate aligned
    bool allocate_aligned(void **ptr, size_t alignment, size_t size);

private:
    // The data structure which will hold the buffer elements
    buffer  *double_buffer;

    // Double buffer parameters
    uint16_t nants;   // Total number of antennas (or stations)
    uint16_t nchans;  // Total number of channels
    uint32_t nsamp;   // Total number of samples
    uint8_t  npol;    // Total number of polarisation
    uint8_t  nbuffers; // Number of buffers in buffering system

    // Producer and consumer pointers, specifying which buffer index to use
    // These are declared as volatile so tha they are not optimsed into registers
    volatile uint8_t producer;
    volatile uint8_t consumer;

    // Nanosleep
    struct timespec tim, tim2;

};


#endif // _DOUBLEBUFFER_H

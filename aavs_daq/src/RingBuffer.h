//
// Created by Alessio Magro on 27/08/2015.
//

/* This class is meant to be used as a mediator between a producer thread and a consumer thread.
 * Only one producer and one consumer are supported (at the moment). Priority is given to the
 * producer, such that if the consumer does not manage to consume the data at the rate which they're
 * being generated, the producer will overwrite data cells.
 *
 * This class is meant to provide a high performance ring buffer. The use of mutual exclusion locks
 * is avoided in favour of atomic operations.
 */

#ifndef _RINGBUFFER_H
#define _RINGBUFFER_H

#define DEBUG

#include <stdint.h>
#include <cstddef>
#include <time.h>

// --------------------------------- Structure Definitions -----------------------------------

// Represents a single cell in the ring buffer.
struct cell
{
    size_t   size;  // Size of data portion of cell
    uint8_t  *data; // Pointer to the data portion
};

// --------------------------------- Ring Buffer Class ---------------------------------------

class RingBuffer
{
public:
    // Class constructor
    RingBuffer(size_t cell_size, size_t nofcells);

    // Class destructor
    ~RingBuffer();

    // Consume an item from the ring buffer
    size_t pull(uint8_t* data);

    // Consume an item from the ring buffer with timeout
    size_t pull_timeout(uint8_t* data, uint8_t timeout_seconds);

    // Insert an new item into the ring buffer
    void push(uint8_t* data, size_t data_size);

private:
    // Allocate aligned
    bool allocate_aligned(void **ptr, size_t alignment, size_t size);

private:
    // The data structure which will hold the data elements.
    uint8_t  *memory;
    cell     *ring_buffer;

    // Ring buffer parameters
    size_t  cell_size;
    size_t  nofcells;

    // Producer and consumer pointers
    // These are declared as volatile so that they are not optimsed into registers
    volatile size_t producer;
    volatile size_t consumer;

    // Nanosleep
    struct timespec tim, tim2;
};


#endif //_RINGBUFFER_H

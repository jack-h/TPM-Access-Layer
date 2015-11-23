//
// Created by Alessio Magro on 27/08/2015.
//
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <math.h>
#include <sys/mman.h>
#include <string.h>
#include <sys/time.h>
#include "RingBuffer.h"

// RingBuffer constructor
RingBuffer::RingBuffer(size_t cell_size, size_t nofcells)
{
    // Get L1 cacheline size
#ifdef _SC_LEVEL1_DCACHE_LINESIZE
    long cacheline_size = sysconf(_SC_LEVEL1_DCACHE_LINESIZE);
#else
    long cacheline_size = 64;
#endif

    // The cell_size arguments refers to the data content of each cell.
    // Make sure that it's a multiple of cacheline_size
    cell_size = (size_t) (ceil(cell_size / (double) cacheline_size) * cacheline_size);

    // Make sure that nofcells is a power of 2
    nofcells = (size_t) pow(2, ceil(log2(nofcells)));

    // Get system page size
#ifdef _SC_PAGESIZE
    long page_size = sysconf(_SC_PAGESIZE);
#else
    long page_size = 1024;
#endif

    // Allocate memory store and align it to the system's page size
    allocate_aligned((void **) &memory, (size_t) page_size, cell_size * nofcells * sizeof(uint8_t));

    // Mark memory buffer as non-swappable
    // Note that for unprivileged users, the RLIMIT_MEMLOCK limit has to be set accordingly
//    if (!mlock(memory, cell_size * nofcells * sizeof(uint8_t)))
//    {
//#ifdef DEBUG
//        perror("Could not lock memory");
//#else
//        // Use syslog
//#endif
//    }

    // Allocate ring buffer cell pointers
    allocate_aligned((void **) &ring_buffer, (size_t) cacheline_size, nofcells * sizeof(cell));

    // Partition allocated memory into cells and update ring buffer cell pointers
    for(unsigned c = 0; c < nofcells; c++)
    {
        ring_buffer[c].size = 0;
        ring_buffer[c].data = memory + cell_size * c;
    }

    // Initialise producer and consumer
    producer = 0;
    consumer = 0;

    // Set local variables
    this->cell_size = cell_size;
    this->nofcells  = nofcells;
    
    // Set timing variables
    this->tim.tv_sec  = 0;
    this->tim.tv_nsec = 500;
}
// RingBuffer destructor
RingBuffer::~RingBuffer()
{
    // Free used memory
    free(memory);
    free(ring_buffer);
}

// Push a new item into the ring buffer
void RingBuffer::push(uint8_t *data, size_t data_size)
{
    // If producer and consumer are pointing to the same cell, we have to wait
    // for the consumer to finish reading the cell
    while (producer == consumer && ring_buffer[producer].size == SIZE_MAX)
        nanosleep(&tim, &tim2); // Wait using nanosleep

    // Producer is on a different cell than the consumer. If size is already set, then
    // set to zero to prevent consumer from reading the data while it's being updates
    ring_buffer[producer].size = 0;

    // Consumer cannot access cell, write data to cell
    memcpy(ring_buffer[producer].data, data, data_size);

    // Done writing data, assign size to cell
    ring_buffer[producer].size = data_size;

    // Finished processing cell, increment producer
    producer = (producer + 1) & (nofcells - 1);
}

size_t RingBuffer::pull_timeout(uint8_t *data, uint8_t timeout_seconds)
{
    struct timeval start, end;

    // If producer and consumer are pointing to the same cell, we have to wait
    // for producer to finish writing to the cell
    gettimeofday(&start, NULL);
    while (producer == consumer && ring_buffer[consumer].size == 0)
    {
        nanosleep(&tim, &tim2); // Wait using nanosleep
        gettimeofday(&end, NULL);
        if (end.tv_sec - start.tv_sec >= timeout_seconds)
            return SIZE_MAX;
    }

    // Take note of size and set size to SIZE_MAX, signifying that the data is being copied
    size_t data_size = ring_buffer[consumer].size;
    ring_buffer[consumer].size = SIZE_MAX;

    // Consumer and producer are on different cells. Since consumer is always trailing
    // the producer, then this should be guaranteed to contain data. Copy this data
    memcpy(data, ring_buffer[consumer].data, data_size);

    // Finished reading, reset cell size
    ring_buffer[consumer].size = 0;

    // All done, increment consumer
    consumer = (consumer + 1) & (nofcells - 1);

    // Return data size
    return data_size;
}

// Consumer an item from the ring buffer
size_t RingBuffer::pull(uint8_t *data)
{
    // If producer and consumer are pointing to the same cell, we have to wait
    // for producer to finish writing to the cell
    while (producer == consumer && ring_buffer[consumer].size == 0)
        nanosleep(&tim, &tim2); // Wait using nanosleep

    // Take note of size and set size to SIZE_MAX, signifying that the data is being copied
    size_t data_size = ring_buffer[consumer].size;
    ring_buffer[consumer].size = SIZE_MAX;

    // Consumer and producer are on different cells. Since consumer is always trailing
    // the producer, then this should be guaranteed to contain data. Copy this data
    memcpy(data, ring_buffer[consumer].data, data_size);

    // Finished reading, reset cell size
    ring_buffer[consumer].size = 0;

    // All done, increment consumer
    consumer = (consumer + 1) & (nofcells - 1);

    // Return data size
    return data_size;
}

// Try to allocate aligned memory, and default to normal malloc if that fails
bool RingBuffer::allocate_aligned(void **ptr, size_t alignment, size_t size)
{
    // Try allocating memory with posix_memalign
    if (posix_memalign(ptr, alignment, size) < 0)
    {
#ifdef DEBUG
        perror("Could not allocate memory with posix_memalign");
#else
        // Use syslog
#endif
        if ((*ptr = malloc(size)) == NULL)
        {
#ifdef DEBUG
            perror("Could not allocate memory");
#else
            // Use syslog
#endif
            return false;
        }
    }
    return true;
}
//
// Created by Alessio Magro on 04/09/2015.
//

#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <sys/mman.h>
#include <stdio.h>

#include "DoubleBuffer.h"

#define DEBUG

// Default double buffer constructor
DoubleBuffer::DoubleBuffer(uint16_t nants, uint16_t nchans,
                           uint32_t nsamp, uint8_t npol, uint8_t nbuffers) :
        nants(nants), nchans(nchans), nsamp(nsamp), npol(npol), nbuffers(nbuffers)
{
    // Get L1 cacheline size
#ifdef _SC_LEVEL1_DCACHE_LINESIZE
    long cacheline_size = sysconf(_SC_LEVEL1_DCACHE_LINESIZE);
#else
    long cacheline_size = 64;
#endif

    // Get system page size
#ifdef _SC_PAGESIZE
    long page_size = sysconf(_SC_PAGESIZE);
#else
    long page_size = 1024;
#endif

    // Make sure that nbuffers is a power of 2
    nbuffers = (uint8_t) pow(2, ceil(log2(nbuffers)));

    // Allocate the double buffer
    allocate_aligned((void **) &double_buffer, (size_t) cacheline_size, nbuffers * sizeof(buffer));

    // Initialise and allocate buffers in each struct instance
    for(unsigned i = 0; i < nbuffers; i++)
    {
        double_buffer[i].ref_time = 0;
        double_buffer[i].ready    = false;
        allocate_aligned((void **) &(double_buffer[i].data), (size_t) page_size,
        nants * nchans * npol * nsamp * sizeof(DSIZE));

        // Lock memory
        if (!mlock(double_buffer[i].data, nants * nchans * npol * nsamp * sizeof(DSIZE)))
        {
#ifdef DEBUG
            perror("Could not lock memory");
#else
            // Use syslog
#endif
        }
    }
}

// Try to allocate aligned memory, and default to normal malloc if that fails
bool DoubleBuffer::allocate_aligned(void **ptr, size_t alignment, size_t size)
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

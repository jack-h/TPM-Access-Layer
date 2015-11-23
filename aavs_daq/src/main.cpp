#include <iostream>
#include <unistd.h>

#include "NetworkReceiver.h"
#include "ChannelisedData.h"
#include "AntennaData.h"
#include "BeamformedData.h"
#include "Daq.h"

using namespace std;

void test_receiver()
{
    // Receiver parameters
    struct recv_params params;
    params.frame_size       = 8192;
    params.frames_per_block = 64;
    params.nofblocks        = 256;
    char interface[6]       = "eth3";

    // Assign port
    unsigned short port = 10000;

    // Create and initialise network receiver;
    NetworkReceiver receiver(interface, params);
    receiver.addPort(port);

    // Start receiver
    receiver.startThread();

    sleep(1000);
}

void test_buffer()
{
    struct timespec tps, tpe;
    size_t cell_size        = 8000;
    size_t ring_buffer_size = (size_t) 64e6 / 8000;
    ulong  iterations       = 100000000;

    RingBuffer ring_buffer(cell_size, ring_buffer_size);
    clock_gettime(CLOCK_REALTIME, &tps);

    uint8_t *data;
    posix_memalign((void **) &data, 128, cell_size * sizeof(uint8_t));
    for(unsigned i = 0; i < iterations; i++)
        ring_buffer.push(data, cell_size);

    clock_gettime(CLOCK_REALTIME, &tpe);
    double duration = ((tpe.tv_sec - tps.tv_sec) + (tpe.tv_nsec - tps.tv_nsec) * 1e-9) + 0.5;
    printf("Duration: %.2f s, data rate: %.2f Gb/s\n", duration,
           (iterations * cell_size * sizeof(uint8_t) * 8) * 1e-9 / duration);

    free(data);
}

void test_beam()
{
    // Create network thread instance
    struct recv_params params;
    params.frame_size       = 2048;
    params.frames_per_block = 32;
    params.nofblocks        = 128;
    char interface[6]       = "eth0";

    // Assign port
    unsigned short port1 = 4660;
    unsigned short port2 = 4661;

    // Telescope information
    uint16_t nsamp    = 64;
    uint8_t  ntiles   = 1;
    uint16_t nchans   = 512;
    uint16_t nbeams   = 2;
    uint8_t  npols    = 2;

    // Create and initialise network receiver;
    NetworkReceiver receiver(interface, params);
    receiver.addPort(port1);
    receiver.addPort(port2);

    // Create BeamformedData instance
    BeamformedData beamData(ntiles, nchans, nsamp, nbeams, npols, 1, 0, 1);

    // Assign receiver to correlator
    beamData.setReceiver(&receiver);

    // Start correlator. This will create a ring buffer and assign this buffer,
    // together with a filtering function to the network receiver
    beamData.startThread();

    // Start network thread
    receiver.startThread();

    sleep(1000);
}

void test_channelised()
{
    // Create network thread instance
    struct recv_params params;
    params.frame_size       = 2048;
    params.frames_per_block = 64;
    params.nofblocks        = 256;
    char interface[6]       = "eth0";

    // Assign port
    unsigned short port = 4660;

    // Telescope information
    uint16_t nant     = 16;
    uint16_t nsamp    = 128;
    uint8_t  ntiles   = 1;
    uint8_t  nstation = 1;
    uint16_t nchans   = 512;
    uint16_t samp_per_packet = 32;

    // Create and initialise network receiver;
    NetworkReceiver receiver(interface, params);
    receiver.addPort(port);

    // Create correlator instance
    ChannelisedData correlator(nstation, ntiles, nchans, nsamp, nant, 2, 1, 2, samp_per_packet, 0);

    // Assign receiver to correlator
    correlator.setReceiver(&receiver);

    // Start correlator. This will create a ring buffer and assign this buffer,
    // together with a filtering function to the network receiver
    correlator.startThread();

    // Start network thread
    receiver.startThread();

    sleep(1000);
}

void test_antenna_data()
{
    // Create network thread instance
    struct recv_params params;
    params.frame_size       = 2048;
    params.frames_per_block = 32;
    params.nofblocks        = 128;
    char interface[6]       = "eth0";

    // Assign port
    unsigned short port1 = 4660;
    unsigned short port2 = 4661;

    // Telescope information
    uint16_t nant     = 16;
    uint32_t nsamp    = (uint32_t) (64 * 1024);
    uint8_t  ntiles   = 1;
    uint8_t  nstation = 1;
    uint8_t  npol     = 2;

    // Create and initialise network receiver;
    NetworkReceiver receiver(interface, params);
    receiver.addPort(port1);
    receiver.addPort(port2);

    // Create correlator instance
    AntennaData antenna_data(nant, nsamp, ntiles, nstation, npol, 0);

    // Assign receiver to correlator
    antenna_data.setReceiver(&receiver);

    // Start correlator. This will create a ring buffer and assign this buffer,
    // together with a filtering function to the network receiver
    antenna_data.startThread();

    // Start network thread
    receiver.startThread();

    sleep(1000);
}

void daq_service()
{


    // Create network thread instance
    struct recv_params params;
    params.frame_size       = 2048;
    params.frames_per_block = 32;
    params.nofblocks        = 128;
    char interface[6]       = "eth0";

    // Assign port
    unsigned short port1 = 4660;
    unsigned short port2 = 4661;

    // Telescope information
    uint16_t nant     = 16;
    uint32_t nsamp    = (uint32_t) (64 * 1024);
    uint8_t  ntiles   = 1;
    uint8_t  nstation = 1;
    uint8_t  npols    = 2;
    uint16_t nchans   = 512;

    // Create and initialise network receiver;
    NetworkReceiver receiver(interface, params);
    receiver.addPort(port1);
    receiver.addPort(port2);

    // Create raw data instance and assign receiver
    AntennaData antenna_data(nant, nsamp, ntiles, nstation, npols, 0);
    antenna_data.setReceiver(&receiver);

    // Create channelised data instance and assign receiver
    uint16_t channel_samp_per_packet = 32;
    nsamp    = 128;
    ChannelisedData channel_data(nstation, ntiles, nchans, nsamp, nant, 2, 1, 2, channel_samp_per_packet, 0);
    channel_data.setReceiver(&receiver);

    // Create beam data instance and assign receiver
    uint16_t nbeams   = 1;
    nsamp             = 64;
    BeamformedData beam_data(ntiles, nchans, nsamp, nbeams, npols, 1, 0, 1);
    beam_data.setReceiver(&receiver);

    // Start consumers
    antenna_data.startThread();
    channel_data.startThread();
    beam_data.startThread();

    // Start network thread
    receiver.startThread();

    // Run indefinitely
    receiver.waitForThreadToExit();
}

void daq_service_library()
{
   // Telescope information
    uint16_t nant     = 16;
    uint32_t nsamp    = (uint32_t) (64 * 1024);
    uint8_t  ntiles   = 1;
    uint8_t  nstation = 1;
    uint8_t  npols    = 2;
    uint16_t nchans   = 512;
    uint8_t  nbeams   = 1;

    setReceiverConfiguration(nant, nchans, nbeams, npols, nstation, ntiles, 0);
    startReceiver("eth0", 2048, 32, 128);
    addReceiverPort(4660);
    addReceiverPort(4661);

    startRawConsumer(nsamp);
    startChannelConsumer(128, 1, 1, 32);
    startBeamConsumer(64, 1);

    sleep(1000);
}

int main()
{
//    test_beam();
//    test_channelised();
//    test_receiver();
//    test_antenna_data();
//    daq_service();
    daq_service_library();
}


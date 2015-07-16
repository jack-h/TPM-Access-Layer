#ifndef UNIBOARD_CLASS
#define UNIBOARD_CLASS

#include "Definitions.hpp"
#include "MemoryMap.hpp"
#include "Board.hpp"
#include "Utils.hpp"
#include "SPI.hpp"
#include "UCP.hpp"

#include <string.h>

class UCP;

// Board derived class representing a UniBoard
class UniBoard: public Board
{
    public:
        // UniBoard constructor
        UniBoard(const char *ip, unsigned short port);

    public:
        // Clear everything and remove connection
        void disconnect();

        // Get board status
        STATUS getStatus();

        // Get register list
        REGISTER_INFO *getRegisterList(UINT *num_registers, bool load_values);

        // Get register value
        VALUES readRegister(DEVICE device, REGISTER reg, UINT n = 1, UINT offset = 0);

        // Set register value
        RETURN writeRegister(DEVICE device, REGISTER reg, UINT *value, UINT n = 1, UINT offset = 0);

        // Read FIFO register capability
        VALUES readFifoRegister(DEVICE device, REGISTER reg, UINT n = 1);

        // Write FIFO register capability
        RETURN writeFifoRegister(DEVICE device, REGISTER reg, UINT *values, UINT n = 1);

        // Get address value
        VALUES readAddress(DEVICE device, UINT address, UINT n);

        // Set address value
        RETURN writeAddress(DEVICE device, UINT address, UINT *values, UINT n);

        // Get list of firmware from board
        FIRMWARE getFirmware(DEVICE device, UINT *num_firmware);

        // Asynchronously load firmware to FPGA.
        RETURN loadFirmware(DEVICE device, const char* bitstream);

        // Synchronously load firmware to FPGA
        RETURN loadFirmwareBlocking(DEVICE device, const char* bitstream);

        // Functions dealing with on-board devices (such as SPI devices)
        SPI_DEVICE_INFO *getDeviceList(UINT *num_devices);
        VALUES          readDevice(REGISTER device, UINT address);
        RETURN          writeDevice(REGISTER device, UINT address, UINT value);

    protected:
        // Populate register list
        RETURN populateRegisterList(DEVICE device);

    protected:
        // From Board base class, we will use the following variables as are:
        // id, ip, port, num_fpgas, status, memory_map

        // On the UniBoard, each node has it's own UCP implementation, and therefore
        // we need to create at most 8 UCP connections for each UniBoard. The base class
        // protocol variables is ignored, and instead an array of protocol instances is used
        UCP *connections[8];

        // Device map to translate between device number of DEVICE identifier
        DEVICE id_device_map[8] = { FPGA_1, FPGA_2, FPGA_3, FPGA_4, FPGA_5, FPGA_6, FPGA_7, FPGA_8 };
        map<DEVICE, int> device_id_map;

        // Mutex to lock loading of memory map
        pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

        // Firmware loaded on the UniBoard will store the register map as a string in ROM, which
        // can be accessed with the following
        UINT ROM_SYSTEM_INFO        = 0x1000;
        UINT ROM_SYSTEM_INFO_OFFSET = 1024+256;

        // The basic design also has standard information, which can be access with the following
        UINT PIO_SYSTEM_INFO        = 0x100;
        UINT PIO_SYSTEM_INFO_OFFSET = 128;
};

#endif // UNIBOARD_CLASS

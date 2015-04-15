#ifndef TPM_CLASS
#define TPM_CLASS

#include "Definitions.hpp"
#include "MemoryMap.hpp"
#include "Protocol.hpp"
#include "Board.hpp"
#include "Utils.hpp"
#include "SPI.hpp"  

#include <string.h>

// Board derived class representing a Tile Processing Modules
class TPM: public Board
{
    public:
        // TPM constructor
        TPM(const char *ip, unsigned short port);

    public:
        // Clear everything and remove connection
        void disconnect();

        // Get board status
        STATUS getStatus();

        // Get register list
        REGISTER_INFO* getRegisterList(UINT *num_registers);

        // Get register value
        VALUES readRegister(DEVICE device, REGISTER reg, UINT n = 1, UINT offset = 0);

        // Set register value
        RETURN writeRegister(DEVICE device, REGISTER reg, UINT *value, UINT n = 1, UINT offset = 0);

        // Get address value
        VALUES readAddress(UINT address, UINT n = 1);

        // Set address value
        RETURN writeAddress(UINT address, UINT *values, UINT n = 1);

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

};

#endif // TPM_CLASS

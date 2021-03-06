#ifndef ROACH_CLASS
#define ROACH_CLASS

#include "Definitions.hpp"
#include "KATCP.hpp"
#include "Board.hpp"
#include "Utils.hpp"
#include "SPI.hpp"  

#include <string.h>

class KATCP;

// Board derived class representing a ROACH
class ROACH: public Board
{
    public:
        // ROACH constructor
        ROACH(const char *ip, unsigned short port);

    public:
        // Clear everything and remove connection
        void disconnect();

        // Get board status
        STATUS getStatus();

        // Reset board
        RETURN reset(DEVICE device);

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

    // Synchronously load firmware to FPGA
        RETURN loadFirmware(DEVICE device, const char *bitstream, uint32_t base_address = 0);

        // Functions dealing with on-board devices (such as SPI devices)
        RETURN          loadSPIDevices(DEVICE device, const char *filepath);
        SPI_DEVICE_INFO *getDeviceList(UINT *num_devices);
        VALUES          readDevice(REGISTER device, UINT address);
        RETURN          writeDevice(REGISTER device, UINT address, UINT value);

    protected:

        KATCP   *katcp; 
};

#endif // ROACH_CLASS

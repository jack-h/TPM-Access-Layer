#ifndef BOARD_CLASS
#define BOARD_CLASS

#include "Definitions.hpp"
#include "MemoryMap.hpp"
#include "Protocol.hpp"
#include "Utils.hpp"
#include "SPI.hpp"  

#include <string.h>

using namespace std;

// Class representation of a digital board
// This can eventually be sub-classed to add functionality
// specific to a particular board
class Board
{
    public:
        // Board constructor
        Board(const char *ip, unsigned short port);

    // ---------- Public class functions --------
    public:

        // Clear everything and remove connection
        virtual void disconnect() = 0;

        // Get board status
        virtual STATUS getStatus() = 0;

        // Get register list
        virtual REGISTER_INFO* getRegisterList(UINT *num_registers) = 0;

        // Get register value
        virtual VALUES readRegister(DEVICE device, REGISTER reg, UINT n, UINT offset = 0) = 0;

        // Set register value
        virtual RETURN writeRegister(DEVICE device, REGISTER reg, UINT n, UINT *value, UINT offset = 0) = 0;

        // Get address value
        virtual VALUES readAddress(UINT address, UINT n) = 0;

        // Set address value
        virtual RETURN writeAddress(UINT address, UINT n, UINT *values) = 0;

        // Asynchronously load firmware to FPGA.
        virtual RETURN loadFirmware(DEVICE device, const char* bitstream) = 0;

        // Synchronously load firmware to FPGA
        virtual RETURN loadFirmwareBlocking(DEVICE device, const char* bitstream) = 0;

        // Functions dealing with on-board devices (such as SPI devices)
        virtual SPI_DEVICE_INFO *getDeviceList(UINT *num_devices) = 0;
        virtual VALUES          readDevice(REGISTER device, UINT address) = 0;
        virtual RETURN          writeDevice(REGISTER device, UINT address, UINT value) = 0;
        
    // ---------- Protected class functions ---------- 
    protected:

    // ---------- Protected class members ---------- 
    protected:

        unsigned int    id;   // Board identifier
        char            *ip;  // Board IP address
        unsigned short  port; // Port to communicate with board
        unsigned short  num_fpgas;  // Number of FPGAs on board
        STATUS          status; // Board status

        Protocol        *protocol;    // Protocol instance to communicate with board

        MemoryMap       *memory_map;  // Memory map instance

        SPI             *spi_devices; // SPI devices map

};

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
        VALUES readRegister(DEVICE device, REGISTER reg, UINT n, UINT offset = 0);

        // Set register value
        RETURN writeRegister(DEVICE device, REGISTER reg, UINT n, UINT *value, UINT offset = 0);

        // Get address value
        VALUES readAddress(UINT address, UINT n);

        // Set address value
        RETURN writeAddress(UINT address, UINT n, UINT *values);

        // Asynchronously load firmware to FPGA.
        RETURN loadFirmware(DEVICE device, const char* bitstream);

        // Synchronously load firmware to FPGA
        RETURN loadFirmwareBlocking(DEVICE device, const char* bitstream);

        // Functions dealing with on-board devices (such as SPI devices)
        SPI_DEVICE_INFO *getDeviceList(UINT *num_devices);
        VALUES          readDevice(REGISTER device, UINT address);
        RETURN          writeDevice(REGISTER device, UINT address, UINT value);

    protected:
};

#endif // BOARD

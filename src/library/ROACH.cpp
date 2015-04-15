#include "ROACH.hpp"

// Constructor
ROACH::ROACH(const char *ip, unsigned short port) : Board(ip, port)
{
    // Set number of FPGAs
    this -> num_fpgas = 1;

    // Create protocol instance
    protocol = new KATCP();

    // Get specific pointer to KATCP protocol for extended functionality
    katcp    = static_cast<KATCP *>(protocol);

    // Create socket and connect to ROACH
    RETURN ret = katcp -> createSocket(ip, port);

    // Check if address is valid
    if (ret == FAILURE)
    {
        DEBUG_PRINT("ROACH::ROACH. Could not connect to board.");
        status = NETWORK_ERROR;
        this -> disconnect();
    }
    else
        status = OK;
}

// Clear everything and remove connection
void ROACH::disconnect()
{
    katcp -> closeSocket();
    katcp = NULL;
}

// Get board status
STATUS ROACH::getStatus()
{
    // TODO: Get status from board
    return status;
}

// Get register list
REGISTER_INFO* ROACH::getRegisterList(UINT *num_registers)
{
    return katcp -> getRegisterList(num_registers);;
}

// Get register value
VALUES ROACH::readRegister(DEVICE device, REGISTER reg, UINT n, UINT offset)
{
    return {NULL, NOT_IMPLEMENTED};
}

// Set register value
RETURN ROACH::writeRegister(DEVICE device, REGISTER reg, UINT *value, UINT n, UINT offset)
{
    // Check if device is valid
    if (device != FPGA_1)
    {
        DEBUG_PRINT("ROACH::writeRegister. Invalid device specific, only FPGA_1 is valid for ROACH");
        return FAILURE;
    }

    // Check if register is in list of registers
    int index = katcp -> getRegisterIndex(reg);
    if (index == -1)
    {
        DEBUG_PRINT("ROACH::writeRegister. Register not found");
        return FAILURE;
    }
    
    // Register found, call KATCP write function
    return katcp -> writeRegister((UINT) index, value, n, offset);
}

// Get list of firmware from board
FIRMWARE ROACH::getFirmware(DEVICE device, UINT *num_firmware)
{
    // Check if device is valid
    if (device != FPGA_1)
    {
        DEBUG_PRINT("ROACH::getFirmware. Invalid device specific, only FPGA_1 is valid for ROACH");
        return NULL;
    }

    return katcp -> listFirmware(num_firmware);
}

// Asynchronously load firmware to FPGA.
RETURN ROACH::loadFirmware(DEVICE device, const char* bitstream)
{
    return NOT_IMPLEMENTED;
}

// Synchronously load firmware to FPGA
RETURN ROACH::loadFirmwareBlocking(DEVICE device, const char* bitstream)
{
    // Check if device is valid
    if (device != FPGA_1)
    {
        DEBUG_PRINT("ROACH::loadFirmwareBlocking. Invalid device specific, only FPGA_1 is valid for ROACH");
        return FAILURE;
    }

    // A new firmware needs to be loaded onto one of the FPGAs
    return katcp -> loadFirmwareBlocking(bitstream);    
}


// =========================== NOT IMPLEMENTED FOR ROACH ===========================

// Get address value. Not applicable to ROACH
VALUES ROACH::readAddress(UINT address, UINT n)
{ return {NULL, NOT_IMPLEMENTED}; }

// Set address value. Not applicable to ROACH
RETURN ROACH::writeAddress(UINT address, UINT *values, UINT n)
{ return NOT_IMPLEMENTED; }

// Functions dealing with on-board devices (such as SPI devices)
// NOTE: Not applicale to ROACH
SPI_DEVICE_INFO* ROACH::getDeviceList(UINT *num_devices)
{ return NULL; }

VALUES ROACH::readDevice(REGISTER device, UINT address)
{ return { NULL, NOT_IMPLEMENTED }; }

RETURN ROACH::writeDevice(REGISTER device, UINT address, UINT value)
{ return NOT_IMPLEMENTED; }

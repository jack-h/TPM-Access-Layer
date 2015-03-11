#include "Board.hpp"

#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdio.h>

// ------------------------ Board class implementation -----------------------

// Board constructor
Board::Board(const char *ip, unsigned short port)
{
    // Set default number of FPGAs
    this -> num_fpgas = 1;
}

// Board destructor
Board::~Board()
{
    // Free up ip
    free(this -> ip);
}

// ------------------------ TPM class implementation -----------------------

// TPM constructor
TPM::TPM(const char *ip, unsigned short port) : Board(ip, port)
{
    // Set number of FPGAs
    this -> num_fpgas = 2;

    // Create protocol instance
    protocol = new UCP();

    // Create socket and set up TPM address structure
    protocol -> createSocket(ip, port);
}

// TPM destructor
TPM::~TPM()
{
    protocol -> closeSocket();
}

// Disconnect from board
void TPM::disconnect()
{
    protocol -> closeSocket();
    protocol = NULL;
}

// Get board status
STATUS TPM::getStatus()
{
    return OK;
}

// Get register list from memory map
REGISTER_INFO* TPM::getRegisterList(UINT *num_registers)
{
    return memory_map -> getRegisterList(num_registers);
}

// Get register value
VALUES TPM::readRegister(DEVICE device, REGISTER reg, UINT n)
{  
    // Get register address from 
    int address = memory_map -> getRegisterAddress(device, reg);

    // If register was not found, return error
    if (address == -1)
    {
        DEBUG_PRINT("TPM::readRegister. Register" << reg << " on device " << device << " not found in memory map");
        return {0, FAILURE};
    }

    // Otherwise, send request through protocol
    return protocol -> readRegister(address, n);
}

// Get register value
ERROR TPM::writeRegister(DEVICE device, REGISTER reg, UINT n, UINT *values)
{  
    // Get register address from 
    int address = memory_map -> getRegisterAddress(device, reg);

    // If register was not found, return error
    if (address == -1)
    {
        DEBUG_PRINT("TPM::writeRegister. Register" << reg << " on device " << device << " not found in memory map");
        return FAILURE;
    }

    // Get register bitmask
    UINT bitmask = memory_map -> getRegisterBitMask(device, reg);

    // Loop over all values and apply bitmask
    for(unsigned i = 0; i < n; i++)
        values[i] = values[i] & bitmask;

    // Finished pre-processing, write values to register
    return protocol -> writeRegister(address, n, values);
}

// Asynchronously load firmware to FPGA.
ERROR TPM::loadFirmware(DEVICE device, const char* bitstream)
{
    return FAILURE;
}

// Synchronously load firmware to FPGA
ERROR TPM::loadFirmwareBlocking(DEVICE device, const char* bitstream)
{
    // A new firmware needs to be loaded onto one of the FPGAs
    // NOTE: It is assumed that the new XML mapping contains all the
    // mappings (for CPLD, FPGA 1 and FPGA 2), so we just need to reload
    // the memory map

    // Get XML file and re-create the memory map
    char *xml_file = extractXMLFile(bitstream);

    // Create new memory map
    memory_map = new MemoryMap(xml_file);    

    return SUCCESS;
}

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

    // TODO: Make this better
    // Simple test to check whether remote IP/port are reachable
    VALUES vals = protocol -> readRegister(0x0, 1);
    if (vals.error == FAILURE)
    {
        DEBUG_PRINT("TPM::TPM. Error during IP check.");
        status = NETWORK_ERROR;
        this -> disconnect();
    }
    else   
        status = OK;
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
    return status;
}

// Get register list from memory map
REGISTER_INFO* TPM::getRegisterList(UINT *num_registers)
{
    return memory_map -> getRegisterList(num_registers);
}

// Get register value
VALUES TPM::readRegister(DEVICE device, REGISTER reg, UINT n, UINT offset)
{  
    // Get register address from 
    MemoryMap::RegisterInfo *info = memory_map -> getRegisterInfo(device, reg);

    // If register was not found, return error
    if (info == NULL)
    {
        DEBUG_PRINT("TPM::readRegister. Register " << reg << " on device " << device << " not found in memory map");
        return {0, FAILURE};
    }

    // Check if offset exceeds address area
    if (offset + n * sizeof(UINT) > info -> address + info -> size * sizeof(UINT))
    {
        DEBUG_PRINT("TPM::readRegister. Offset and n exceed allocated address range for register " << reg);
        return {0, FAILURE};
    }

    // Otherwise, send request through protocol
    VALUES vals = protocol -> readRegister(info -> address, n, offset);

    // If failed, return
    if (vals.error == FAILURE)
        return vals;

    // Otherwise, loop through all values, apply bitmaks and shift
    for(unsigned i = 0; i < n; i++)
        vals.values[i] = (vals.values[i] & info -> bitmask) >> info -> shift;

    return vals;
}

// Get register value
ERROR TPM::writeRegister(DEVICE device, REGISTER reg, UINT n, UINT *values, UINT offset)
{  
    // Get register address from 
    MemoryMap::RegisterInfo *info = memory_map -> getRegisterInfo(device, reg);

    // If register was not found, return error
    if (info == NULL)
    {
        DEBUG_PRINT("TPM::writeRegister. Register " << reg << " on device " << device << " not found in memory map");
        return FAILURE;
    }

    // Check if offset exceeds address area
    if (offset + n * sizeof(UINT) > info -> address + info -> size * sizeof(UINT))
    {
        DEBUG_PRINT("TPM::writeRegister. Offset and n exceed allocated address range for register " << reg);
        return FAILURE;
    }

    // Apply shift and bitmask to all values
    for(unsigned i = 0; i < n; i++)
        values[i] = (values[i] << info -> shift) & info -> bitmask;

    // Check if we have to apply a bitmask
    if (info -> bitmask != 0xFFFFFFFF)
    {
        // Read values from board
        VALUES vals = protocol -> readRegister(info -> address, n, offset);

        if (vals.error == FAILURE)
        {
            DEBUG_PRINT("TPM::writeRegister. Error reading value to apply bitmaks for register " << reg);
            return FAILURE; 
        }

        // Loop over all values, apply bitmask and mask with current value
        for(unsigned i = 0; i < n; i++)
            values[i] = (vals.values[i] & (~info -> bitmask)) | values[i];
    }

    // Finished pre-processing, write values to register
    return protocol -> writeRegister(info -> address, n, values, offset);
}

// Get address value
VALUES TPM::readAddress(UINT address, UINT n)
{
    return protocol -> readRegister(address, n);
}

// Set address value
ERROR TPM::writeAddress(UINT address, UINT n, UINT *values)
{
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

#include "UniBoard.hpp"
#include <sstream>
#include <math.h>

// Constructor
UniBoard::UniBoard(const char *ip, unsigned short port) : Board(ip, port)
{
    // Set number of FPGAs
    this -> num_fpgas = 8;

    // The provided IP is the base address for the UniBoard, each node has it's own IP
    vector<string> entries = split(string(ip),  '.');
    stringstream node_ip;
    node_ip << entries[0] << "." << entries[1] << "." << entries[2] << ".";

    // Set status
    this -> status = OK;

    // Create protocol instances for each node and set up connection
    for(unsigned i = 0; i < this -> num_fpgas; i++)
    {
        // Create instance
        UCP *conn = new UCP();
        
	    // Connect
        // While testing, the port number is incremented instead of the IP
        #if TEST
            stringstream current_ip;
            current_ip << node_ip.rdbuf() << (stoi(entries[3], 0, 10) + i % this -> num_fpgas);
	        RETURN ret = conn -> createConnection(current_ip.str().c_str(), port);
	    #else
            RETURN ret = conn -> createConnection(ip, port + i);
        #endif

        // Check if address is valid
        VALUES vals = conn -> readRegister(0x0, 1);
	    if (vals.error == FAILURE)
	    {
		    DEBUG_PRINT("UniBoard::UniBoard. Error during IP check.");
		    this -> status = NETWORK_ERROR;
	    }

        // Assign connection to array
        this -> connections[i] = conn;
    }

    // If an error occurred, disconnect from UniBoard
    if (this -> status == NETWORK_ERROR)
        this -> disconnect();
}

// Disconnect from board
void UniBoard::disconnect()
{
    // Close connection to all nodes
    for(unsigned i = 0; i < this -> num_fpgas; i++)
    {
        this -> connections[i] -> closeConnection();
        this -> connections[i] = NULL;
    }
}

// Get board status
STATUS UniBoard::getStatus()
{
    return status;
}

// Get register list from memory map
REGISTER_INFO *UniBoard::getRegisterList(UINT *num_registers)
{
    // Call memory map to get register information
    REGISTER_INFO* regInfo = memory_map -> getRegisterList(num_registers);

    // Populate structure with register values
    this -> initialiseRegisterValues(regInfo, *num_registers);

    // All done, return
    return regInfo;
}

// Synchronously load firmware to FPGA
RETURN UniBoard::loadFirmwareBlocking(DEVICE device, const char *bitstream)
{
    // A new firmware need to be loaded onto one of the FPGAs
    // NOTE: It is assumed that the new XML mapping contains all the
    // mappings (for 8 FPGAs), so we just need to reload
    // the memory map

    // Get XML file and re-create the memory map
    char *xml_file = extractXMLFile(bitstream);

    // Create a new memory map
    memory_map = new MemoryMap(xml_file);

    // All done
    return SUCCESS;
}

// Set register value
RETURN UniBoard::writeRegister(DEVICE device, REGISTER reg, UINT *values, UINT n, UINT offset)
{
    // Get register address from memory map
    MemoryMap::RegisterInfo *info = memory_map -> getRegisterInfo(device, reg);

    // If register was not found, return error
    if (info == NULL)
    {
        DEBUG_PRINT("UniBoard::writeRegister. Register " << reg << " on device " << device << " not found in memory map");
        return FAILURE;
    }

    // Check if offset exceeds address area
    if (offset + n * sizeof(UINT) > info -> address + info -> size * sizeof(UINT))
    {
        DEBUG_PRINT("UniBoard::writeRegister. Offset and n exceed allocated address range for register " << reg);
        return FAILURE;
    }

    // Apply shift and bitmask to all values
    for(unsigned i = 0; i < n; i++)
        values[i] = (values[i] << info -> shift) & info -> bitmask;

    // Check if we have to apply a bitmask
    if (info -> bitmask != 0xFFFFFFFF)
    {
        // Read values from board
        VALUES vals = connections[device] -> readRegister(info -> address, n, offset);

        if (vals.error == FAILURE)
        {
            DEBUG_PRINT("UniBoard::writeRegister. Error reading value to apply bitmaks for register " << reg);
            return FAILURE;
        }

        // Loop over all values, apply bitmask and mask with current value
        for(unsigned i = 0; i < n; i++)
            values[i] = (vals.values[i] & (~info -> bitmask)) | values[i];
    }

    // Finished pre-processing, write values to register
    return connections[device] -> writeRegister(info -> address, values, n, offset);
}

// Get register value
VALUES UniBoard::readRegister(DEVICE device, REGISTER reg, UINT n, UINT offset)
{
    // Get register address from memory map
    MemoryMap::RegisterInfo *info = memory_map -> getRegisterInfo(device, reg);

    // If register was not found, return error
    if (info == NULL)
    {
        DEBUG_PRINT("UniBoard::readRegister. Register " << reg << " on device " << device << " not found in memory map");
        return {0, FAILURE};
    }

    // Check if offset exceeds address area
    if (offset + n * sizeof(UINT) > info -> address + info -> size * sizeof(UINT))
    {
        DEBUG_PRINT("UniBoard::readRegister. Offset and n exceed allocated address range for register " << reg);
        return {0, FAILURE};
    }

    // Otherwise , send request through protocol
    VALUES vals = connections[(int) log2(device + 1)] -> readRegister(0, n, offset);

    // If failed, return
    if (vals.error == FAILURE)
        return vals;

    // Otherwise, loop through all values, apply bitmasks and shifts
    for(unsigned i = 0; i < n; i++)
        vals.values[i] = (vals.values[i] & info -> bitmask) >> info -> shift;

    return vals;
}

// Get fifo register value
VALUES UniBoard::readFifoRegister(DEVICE device, REGISTER reg, UINT n)
{
    // Get register address from memory map
    MemoryMap::RegisterInfo *info = memory_map -> getRegisterInfo(device, reg);

    // If register was not found, return error
    if (info == NULL)
    {
        DEBUG_PRINT("UniBoard::readRegister. Register " << reg << " on device " << device << " not found in memory map");
        return {0, FAILURE};
    }

    // NOTE: It is assumed that no bit-masking is required for a FIFO register

    // Send request through protocol and return values
    VALUES vals = connections[device] -> readFifoRegister(info -> address, n);

    return vals;
}

// Set fifo register value
RETURN UniBoard::writeFifoRegister(DEVICE device, REGISTER reg, UINT *values, UINT n)
{
    // Get register address from memory map
    MemoryMap::RegisterInfo *info = memory_map -> getRegisterInfo(device, reg);

    // If register was not found, return error
    if (info == NULL)
    {
        DEBUG_PRINT("UniBoard::writeFifoRegister. Register " << reg << " on device " << device << " not found in memory map");
        return FAILURE;
    }

    // NOTE: It is assumed that no bit-masking is required for a FIFO register

    // Write values to register
    return connections[device] -> writeFifoRegister(info -> address, values, n);
}


// Load firmware asynchronously
RETURN UniBoard::loadFirmware(DEVICE device, const char *bitstream)
{
    return NOT_IMPLEMENTED;
}

// =========================== NOT IMPLEMENTED FOR UNIBOARD ===========================

// Get address value. Not applicable to UniBoard
VALUES UniBoard::readAddress(UINT address, UINT n)
{ return {NULL, NOT_IMPLEMENTED}; }

// Set address value. Not applicable to UniBoard
RETURN UniBoard::writeAddress(UINT address, UINT *values, UINT n)
{ return NOT_IMPLEMENTED; }

// For now this is not implemented
FIRMWARE UniBoard::getFirmware(DEVICE device, UINT *num_firmware)
{ return nullptr; }

// Functions dealing with on-board devices (such as SPI devices)
// NOTE: Not applicable to UniBoard
SPI_DEVICE_INFO* UniBoard::getDeviceList(UINT *num_devices)
{ return NULL; }

VALUES UniBoard::readDevice(REGISTER device, UINT address)
{ return { NULL, NOT_IMPLEMENTED }; }

RETURN UniBoard::writeDevice(REGISTER device, UINT address, UINT value)
{ return NOT_IMPLEMENTED; }
#include "UniBoard.hpp"
#include <sstream>
#include <math.h>

// Constructor
UniBoard::UniBoard(const char *ip, unsigned short port) : Board(ip, port)
{
    // Set number of FPGAs
    this -> num_fpgas = 8;

    // Populate device_id_map
    device_id_map[FPGA_1] = 0;
    device_id_map[FPGA_2] = 1;
    device_id_map[FPGA_3] = 2;
    device_id_map[FPGA_4] = 3;
    device_id_map[FPGA_5] = 4;
    device_id_map[FPGA_6] = 5;
    device_id_map[FPGA_7] = 6;
    device_id_map[FPGA_8] = 7;

    // The provided IP is the base address for the UniBoard, each node has it's own IP
    vector<string> entries = split(string(ip),  '.');
    string node_ip = entries[0] + "." + entries[1] + "." + entries[2] + ".";

    // Set status
    this -> status = OK;

    // Create protocol instances for each node and set up connection
    for(unsigned i = 0; i < this -> num_fpgas; i++)
    {
        // Create instance
        UCP *conn = new UCP();
        
	    // Connect
        // While testing, the port number is incremented instead of the IP
        #if !TEST
            string current_ip = node_ip + std::to_string(stoi(entries[3], 0, 10) + i % this -> num_fpgas);
	        RETURN ret = conn -> createConnection(current_ip.c_str(), port);
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
    else
    {
        // Create empty memory map
        memory_map = new MemoryMap();

        // Get memory map from currently loaded firmware
        for(unsigned i = 0; i < this -> num_fpgas; i++)
        {
            this -> populateRegisterList(id_device_map[i]);
        }
    }
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

// When connected to a UniBoard, some form of firmware will be loaded. This function
// will extract the memory map from the loaded firmware
RETURN UniBoard::populateRegisterList(DEVICE device)
{
    // Read the memory map from the loaded firmware
    VALUES vals = connections[device_id_map[device]] -> readRegister(0x1000, ROM_SYSTEM_INFO_OFFSET);

    printf("Received values\n");

    // Check if read succeeded
    if (vals.error == FAILURE)
    {
        DEBUG_PRINT("UniBoard::populateRegisterList. Failed to load ROM_SYSTEM_INFO");
        return FAILURE;
    }

    // Fix endiannes
    for(int i = 0; i < ROM_SYSTEM_INFO_OFFSET; i++)
        vals.values[i] = ntohl(vals.values[i]);

    // Cast received data to input string stream and discard original data
    char *chr_str = (char *) vals.values;
    string info(chr_str);
    delete[] vals.values;

    // Process the read register map
    istringstream info_stream(info);
    string   register_name;
    UINT     address, offset;

    // Loop until end of input string
    while (!info_stream.eof())
    {
        // Read register name
        info_stream >> register_name;
        if (info_stream.fail() || info_stream.bad())
        {
            DEBUG_PRINT("UniBoard::populateRegisterList. Error while loading register map, invalid address/offset");
            return FAILURE;
        }

        // Read base address and offset
        info_stream >> hex >> address;
        info_stream >> dec >> offset;

        // Sanity check
        if (info_stream.fail() || info_stream.bad())
        {
            DEBUG_PRINT("UniBoard::populateRegisterList. Error while loading register map, invalid address/offset");
            return FAILURE;
        }

        if (address == 0 || offset == 0)
        {
            DEBUG_PRINT("UniBoard::populateRegisterList. Error while loading register map, corrupt address/offset");
            return FAILURE;
        }

        // Add new register to memory map
        if (memory_map->addRegisterEntry(device, register_name.c_str(), address, offset) == FAILURE)
            DEBUG_PRINT("UniBoard::populateRegisterList. Error while loading register map, failed to add register to map");
    }

    // Check if PIO_SYSTEM_INFO was included in register map, if not assign default value
    if (memory_map -> getRegisterInfo(device, "PIO_SYSTEM_INFO") == NULL)
       memory_map -> addRegisterEntry(device, "PIO_SYSTEM_INFO", PIO_SYSTEM_INFO, PIO_SYSTEM_INFO_OFFSET);

    // All done, return
    return SUCCESS;
}

// Get register list from memory map
REGISTER_INFO *UniBoard::getRegisterList(UINT *num_registers, bool load_values)
{
    // Call memory map to get register information
    REGISTER_INFO* regInfo = memory_map -> getRegisterList(num_registers);

    // Populate structure with register values
    if (load_values)
        this -> initialiseRegisterValues(regInfo, *num_registers);

    // All done, return
    return regInfo;
}

// Synchronously load firmware to FPGA
RETURN UniBoard::loadFirmwareBlocking(DEVICE device, const char *bitstream)
{
    // A new firmware needs to be loaded onto one of the FPGAs
    // NOTE: It is assumed that the new XML mapping contains all the
    // mappings (for 8 FPGAs), so we just need to reload
    // the memory map

    // Every time a new firmware is loaded, we need to reset the memory
    // map for the specific node
    memory_map -> resetDevice(device);

    // All done
    return NOT_IMPLEMENTED;
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
        VALUES vals = connections[device_id_map[device]] -> readRegister(info -> address, n, offset);

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
    return connections[device_id_map[device]] -> writeRegister(info -> address, values, n, offset);
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
    VALUES vals = connections[device_id_map[device]] -> readRegister(info -> address, n, offset);

    // If failed, return
    if (vals.error == FAILURE)
        return vals;

    // Otherwise, loop through all values, apply bitmasks and shifts
    for(unsigned i = 0; i < n; i++)
        vals.values[i] = (vals.values[i] & info -> bitmask) >> info -> shift;

    return vals;
}

// Get address value
VALUES UniBoard::readAddress(DEVICE device, UINT address, UINT n)
{
    return connections[device_id_map[device]] -> readRegister(address, n);
}

// Set address value
RETURN UniBoard::writeAddress(DEVICE device, UINT address, UINT *values, UINT n)
{
    return connections[device_id_map[device]] -> writeRegister(address, values, n);
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
    VALUES vals = connections[device_id_map[device]] -> readFifoRegister(info -> address, n);

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
    return connections[device_id_map[device]] -> writeFifoRegister(info -> address, values, n);
}


// Load firmware asynchronously
RETURN UniBoard::loadFirmware(DEVICE device, const char *bitstream)
{
    return NOT_IMPLEMENTED;
}

// =========================== NOT IMPLEMENTED FOR UNIBOARD ===========================

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

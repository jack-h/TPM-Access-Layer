#include "Board.hpp"
#include "TPM.hpp"
#include "UCP.hpp"

#include <unistd.h>

// TPM constructor
TPM::TPM(const char *ip, unsigned short port) : Board(ip, port)
{
    // Set number of FPGAs
    this -> num_fpgas = 2;

	protocol = new UCP();

	// Create socket and set up TPM address structure
	protocol -> createConnection(ip, port);

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
    protocol -> closeConnection();  
    protocol = NULL;
}

// Get board status
STATUS TPM::getStatus()
{
    return status;
}

// Get register list from memory map
REGISTER_INFO * TPM::getRegisterList(UINT *num_registers, bool load_values)
{
	// Call memory map to get register information
    REGISTER_INFO* regInfo = memory_map -> getRegisterList(num_registers);
	
	// Populate structure with register values
    if (load_values)
	    this -> initialiseRegisterValues(regInfo, *num_registers);
	
	// All done, return
	return regInfo;
}

// Get register value
VALUES TPM::readRegister(DEVICE device, REGISTER reg, UINT n, UINT offset)
{  
    // Get register address from memory map
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

// Set register value
RETURN TPM::writeRegister(DEVICE device, REGISTER reg, UINT *values, UINT n, UINT offset)
{  
    // Get register address from memory map
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
    return protocol -> writeRegister(info -> address, values, n, offset);
}

// Get address value
VALUES TPM::readAddress(DEVICE device, UINT address, UINT n)
{
    // Device is ignored for the TPM
    return protocol -> readRegister(address, n);
}

// Set address value
RETURN TPM::writeAddress(DEVICE device, UINT address, UINT *values, UINT n)
{
    // Device is ignored for the TPM
    return protocol -> writeRegister(address, values, n);
}

// Get list of SPI devices
SPI_DEVICE_INFO *TPM::getDeviceList(UINT *num_devices)
{
    if (spi_devices != NULL)
        return spi_devices -> getSPIList(num_devices);
    else
        return NULL;
}

// Read value from device
VALUES TPM::readDevice(REGISTER device, UINT address)
{
    // Get device information 
    std::pair<int, int> info = spi_devices -> getSPIInfo(device);

    // If device was not found, return error
    if (info.first == -1 && info.second == -1)
    {
        DEBUG_PRINT("TPM::readDevice. Device " << device << " was not found in device list");
        return {0, FAILURE};
    }

    // Wait for SPI switch to be ready
    // TODO: Make nicer
    for(;;)
    {
        VALUES vals = protocol -> readRegister(spi_devices -> cmd_address);
        printf("First Value: %d\n", (vals.values[0] & (spi_devices -> cmd_start_mask)));
        if ((vals.values[0] & (spi_devices -> cmd_start_mask)) == 0)
            break;
        sleep(1);
    }

    // All systems go, issue request as an array of values
    UINT values[6];
    values[0] = address;  // Address
    values[1] = 0;        // Applicable only to write operations
    values[2] = 0;        // Skip
    values[3] = 1 << info.first;   // spi_en
    values[4] = 1 << info.second;  // spi_sclk 
    values[5] = 0x03;     // Read operation    
    
    // Issue request
    if (protocol -> writeRegister(0x2000000, values, 6) == FAILURE)
    {
        DEBUG_PRINT("TPM::readDevice. Failed to read from device " << device);
        return {0, FAILURE};
    }

    // Wait for request to be completed on board
    for(;;)
    {
        VALUES vals = protocol -> readRegister(spi_devices -> cmd_address);
        if ((vals.values[0] & (spi_devices -> cmd_start_mask)) == 0)
            break;
        sleep(1);
    }

    // Request ready on device, grab data
    VALUES vals = protocol -> readRegister(spi_devices -> read_data);
    vals.values[0] = vals.values[0] & 0xFF;
    // All done
    return vals;
}

// Write value to device
RETURN TPM::writeDevice(REGISTER device, UINT address, UINT value)
{
    // Get device information 
    std::pair<int, int> info = spi_devices -> getSPIInfo(device);

    // If device was not found, return error
    if (info.first == -1 && info.second == -1)
    {
        DEBUG_PRINT("TPM::readDevice. Device " << device << " was not found in device list");
        return FAILURE;
    }

    // Wait for SPI switch to be ready
    // TODO: Make nicer
    for(;;)
    {
        VALUES vals = protocol -> readRegister(spi_devices -> cmd_address);
        if ((vals.values[0] & (spi_devices -> cmd_start_mask)) == 0)
            break;
    }

    // All system go, issue request as an array of values
    UINT values[6];
    values[0] = address;  // Address
    values[1] = (value & 0xFF) << 8;  // Value to write
    values[2] = 0;        // Skip
    values[3] = 1 << info.first;   // spi_en
    values[4] = 1 << info.second;  // spi_sclk
    values[5] = 0x01;     // Write operation    
     
    // Issue request
    if (protocol -> writeRegister(0x20000000, values, 6) == FAILURE)
    {
        DEBUG_PRINT("TPM::readDevice. Failed to read from device " << device);
        return FAILURE;
    }

    // Wait for request to be completed on board
    for(;;)
    {
        VALUES vals = protocol -> readRegister(spi_devices -> cmd_address);
        if ((vals.values[0] & (spi_devices -> cmd_start_mask)) == 0)
            break;
    }

    // All done
    return SUCCESS;
}

// Get list of firmware from board
FIRMWARE TPM::getFirmware(DEVICE device, UINT *num_firmware)
{
    return NULL;
}

// Synchronously load firmware to FPGA
RETURN TPM::loadFirmware(DEVICE device, const char *bitstream)
{
    // A new firmware needs to be loaded onto one of the FPGAs
    // NOTE: It is assumed that the new XML mapping contains all the
    // mappings (for CPLD, FPGA 1 and FPGA 2), so we just need to reload
    // the memory map

    // Get XML file and re-create the memory map
    char *xml_file = extractXMLFile(bitstream);

    // Create new memory map
    memory_map = new MemoryMap(xml_file); 

    // We have memory map, check if it contains an SPI entry
    MemoryMap::RegisterInfo *info = memory_map -> getRegisterInfo(BOARD, "spi");
    if (info == NULL)
        return SUCCESS;

    // SPI detected, check if XML file path exists
    if (info -> module == "")
    {
        DEBUG_PRINT("Error loading SPI devices, XML file not specified");
        return SUCCESS;
    }
    
    // Load SPI XML file
    spi_devices = new SPI(const_cast<char *>((info -> module).c_str()));       
       
    // Populate general SPI properties
    info = memory_map -> getRegisterInfo(BOARD, "spi");
    spi_devices -> spi_address = info -> address;
    
    info = memory_map -> getRegisterInfo(BOARD, "spi.address");
    spi_devices -> spi_address += info -> address;
    spi_devices -> spi_address_mask = info -> bitmask;

    info = memory_map -> getRegisterInfo(BOARD, "spi.write_data");
    spi_devices -> write_data = info -> address;
    spi_devices -> write_data_mask = info -> bitmask;

    info = memory_map -> getRegisterInfo(BOARD, "spi.read_data");
    spi_devices -> read_data = info -> address;
    spi_devices -> read_data_mask = info -> bitmask;

    info = memory_map -> getRegisterInfo(BOARD, "spi.chip_select");
    spi_devices -> chip_select = info -> address;
    spi_devices -> chip_select_mask = info -> bitmask;

    info = memory_map -> getRegisterInfo(BOARD, "spi.sclk");
    spi_devices -> sclk = info -> address;
    spi_devices -> sclk_mask = info -> bitmask;

    info = memory_map -> getRegisterInfo(BOARD, "spi.cmd");
    spi_devices -> cmd_address = info -> address;

    info = memory_map -> getRegisterInfo(BOARD, "spi.cmd.start");
    spi_devices -> cmd_start_mask = info -> bitmask;
    
    info = memory_map -> getRegisterInfo(BOARD, "spi.cmd.rnw");
    spi_devices -> cmd_rnw_mask = info -> bitmask;

    return SUCCESS;
}

// Reset board
RETURN TPM::reset(DEVICE device)
{ return NOT_IMPLEMENTED; }

// FIFO register are not yet implemented on the TPM
VALUES TPM::readFifoRegister(DEVICE device, REGISTER reg, UINT n)
{ return VALUES(); }

RETURN TPM::writeFifoRegister(DEVICE device, REGISTER reg, UINT *values, UINT n)
{ return NOT_IMPLEMENTED; }

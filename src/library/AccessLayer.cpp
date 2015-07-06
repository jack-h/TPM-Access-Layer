// Implementation of the TPM Access Layer API
// This is the main entry point, all high level commands have to pass
// through this file
// All global structure are stored here as well (these are not defined in the header file such that 
// clients do not have access to them -- are 'private')


// Includes and namespaces
#include <string>
#include <map>

#include "AccessLayer.hpp"
#include "ROACH.hpp"
#include "TPM.hpp"

#include "UniBoard.hpp"

using namespace std;

// The global boards map. Each board is identified via an IP address, which
// is translated into a board ID. All operation on the board are performed
// through the same instance (similar to the Singleton design pattern)
map<unsigned int, Board *> boards;

// Set up internal structures to be able to communicate with a processing board
// Arguments:
ID  connectBoard(BOARD_MAKE boardMake, const char* IP, unsigned short port)
{    
    DEBUG_PRINT("AccessLayer::connect. Connecting to " << IP);

    // Convert IP to an ID
    ID id = convertIPtoID(IP);

    DEBUG_PRINT("AccessLayer::connect. Board " << IP << " has ID " << id);
    
    // If board already exists in map, return ID
    if (boards.size() != 0)
    {
        map<unsigned int, Board *>::iterator it;
        it = boards.find(id);
        if (it != boards.end())
        {
            DEBUG_PRINT("AccessLayer::connect. Board " << IP << " already connected");
            return id;
        }
    }

    // If not, create board instance, store in map
    Board *board;

    switch (boardMake)
    {
        case TPM_BOARD:
        {
            board = new TPM(IP, port);
            break;
        }
        case ROACH_BOARD:
        {
            board = new ROACH(IP, port);
            break;
        }
        case ROACH2_BOARD:
        {
            board = new ROACH(IP, port);
            break;
        };
        case UNIBOARD_BOARD:
        {
            board = new UniBoard(IP, port);
            break;
        };
        case UNIBOARD2_BOARD:
            break;
    }

    // Check if board connected successfully
    if (board -> getStatus() == NETWORK_ERROR)
        return 0;

    // Return generated board ID
    boards[id] = board;
    DEBUG_PRINT("AccessLayer::connect. Connected to " << IP);
    return id;
}

// Clear up internal network structures for board in question
RETURN disconnectBoard(ID id)
{    
    // Check if board exists, and if not, return
    if (boards.size() == 0)
        return SUCCESS;

    map<unsigned int, Board *>::iterator it;
    it = boards.find(id);
    if (it == boards.end()) 
    {
        DEBUG_PRINT("AccessLayer::disconnect. " << id << " not connected");
        return SUCCESS;    
    }

    // Check if there any any pending requests, if so wait
    // TODO

    // Call board disconnect
    Board *board = it -> second;
    board -> disconnect();

    // Once everything is done, erase Board object and return
    boards.erase(it);

    DEBUG_PRINT("AccessLayer::disconnect. " << id << " disconnected");

    return SUCCESS;
}

// Rest board. Note that return from this function is not determined, due to
// the board being reset
RETURN  resetBoard(ID id)
{    
    return FAILURE;
}

// Get board status
STATUS  getStatus(ID id)
{
    // Check if board exists
    map<unsigned int, Board *>::iterator it;
    it = boards.find(id);
    if (it == boards.end())
    {
        DEBUG_PRINT("AccessLayer::getStatus. " << id << " not connected");
        return NOT_CONNECTED;
    }

    // Get pointer to board
    Board *board = it -> second;

    // Return register list
    return board -> getStatus();
}

// Get list of registers
REGISTER_INFO* getRegisterList(ID id, UINT *num_registers, bool load_values)
{    
    // Check if board exists
    map<unsigned int, Board *>::iterator it;
    it = boards.find(id);
    if (it == boards.end()) 
    {
        DEBUG_PRINT("AccessLayer::getRegisterList. " << id << " not connected");
        return NULL;   
    }

    // Get pointer to board
    Board *board = it -> second;

    // Return register list
    return board->getRegisterList(num_registers, false);
}

// Get list of SPI devices
SPI_DEVICE_INFO*  getDeviceList(ID id, UINT *num_devices)
{
    // Check if board exists
    map<unsigned int, Board *>::iterator it;
    it = boards.find(id);
    if (it == boards.end())
    {
        DEBUG_PRINT("AccessLayer::getDeviceList. " << id << " not connected");
        return NULL;   
    }

    // Get pointer to board
    Board *board = it -> second;

    // Return device list
    return board -> getDeviceList(num_devices);
}

// Get a register's value
VALUES  readRegister(ID id, DEVICE device, REGISTER reg, UINT n, UINT offset)
{  
    // Check if board exists
    map<unsigned int, Board *>::iterator it;
    it = boards.find(id);
    if (it == boards.end()) 
    {
        DEBUG_PRINT("AccessLayer::readRegister. " << id << " not connected");
        return {0, FAILURE};
    }

    // Get pointer to board
    Board *board = it -> second;

    // Get register value from board
    return board -> readRegister(device, reg, n, offset);
}

// Set a register's value
RETURN  writeRegister(ID id, DEVICE device, REGISTER reg, UINT *values, UINT n, UINT offset)
{    
    // Check if board exists
    map<unsigned int, Board *>::iterator it;
    it = boards.find(id);
    if (it == boards.end()) 
    {
        DEBUG_PRINT("AccessLayer::writeRegister. " << id << " not connected");
        return FAILURE;
    }

    // Get pointer to board
    Board *board = it -> second;

    // Get register value from board
    return board -> writeRegister(device, reg, values, n, offset);
}

// Get a FIFO register's value
VALUES  readFifoRegister(ID id, DEVICE device, REGISTER reg, UINT n)
{
    // Check if board exists
    map<unsigned int, Board *>::iterator it;
    it = boards.find(id);
    if (it == boards.end())
    {
        DEBUG_PRINT("AccessLayer::readFifoRegister. " << id << " not connected");
        return {0, FAILURE};
    }

    // Get pointer to board
    Board *board = it -> second;

    // Get register value from board
    return board -> readFifoRegister(device, reg, n);
}

// Set a FIFO register's value
RETURN  writeFifoRegister(ID id, DEVICE device, REGISTER reg, UINT *values, UINT n)
{
    // Check if board exists
    map<unsigned int, Board *>::iterator it;
    it = boards.find(id);
    if (it == boards.end())
    {
        DEBUG_PRINT("AccessLayer::writeFifoRegister. " << id << " not connected");
        return FAILURE;
    }

    // Get pointer to board
    Board *board = it -> second;

    // Get register value from board
    return board -> writeFifoRegister(device, reg, values, n);
}

// Read from address
VALUES  readAddress(ID id, DEVICE device, UINT address, UINT n)
{
    // Check if board exists
    map<unsigned int, Board *>::iterator it;
    it = boards.find(id);
    if (it == boards.end()) 
    {
        DEBUG_PRINT("AccessLayer::readAddress. " << id << " not connected");
        return {0, FAILURE};
    }

    // Get pointer to board
    Board *board = it -> second;

    // Get address value from board
    return board -> readAddress(device, address, n);
}


// Write from address
RETURN  writeAddress(ID id, DEVICE device, UINT address, UINT *values, UINT n)
{
    // Check if board exists
    map<unsigned int, Board *>::iterator it;
    it = boards.find(id);
    if (it == boards.end()) 
    {
        DEBUG_PRINT("AccessLayer::writeAddress. " << id << " not connected");
        return FAILURE;
    }

    // Get pointer to board
    Board *board = it -> second;

    // Write value to address on board
    return board -> writeAddress(device, address, values, n);
}

// Get a device's value
VALUES  readDevice(ID id, REGISTER device, UINT address)
{
    // Check if board exists
    map<unsigned int, Board *>::iterator it;
    it = boards.find(id);
    if (it == boards.end()) 
    {
        DEBUG_PRINT("AccessLayer::readDevice. " << id << " not connected");
        return {0, FAILURE};
    }

    // Get pointer to board
    Board *board = it -> second;

    // Get register value from board
    return board -> readDevice(device, address);
}

// Set a device's value
RETURN  writeDevice(ID id, REGISTER device, UINT address, UINT value)
{
    // Check if board exists
    map<unsigned int, Board *>::iterator it;
    it = boards.find(id);
    if (it == boards.end()) 
    {
        DEBUG_PRINT("AccessLayer::writeDevice. " << id << " not connected");
        return FAILURE;
    }

    // Get pointer to board
    Board *board = it -> second;

    // Write value to address on board
    return board -> writeDevice(device, address, value);
}

// Get list of firmware on board
FIRMWARE  getFirmware(ID id, DEVICE device, UINT *num_firmware)
{
    // Check if device is valid
    if (!(device == FPGA_1 || device == FPGA_2))
        return NULL;

    // Check if board exists
    map<unsigned int, Board *>::iterator it;
    it = boards.find(id);
    if (it == boards.end()) 
    {
        DEBUG_PRINT("AccessLayer::getFirmware. " << id << " not connected");
        return NULL;   
    }

    // Get pointer to board
    Board *board = it -> second;

    // Cal getFirmware on board instance
    return board -> getFirmware(device, num_firmware);
}

// Load firmware to FPGA. This function return immediately. The status of the
// board can be monitored through the getStatus call
RETURN  loadFirmware(ID id, DEVICE device, const char* bitstream)
{
    // Check if device is valid
    if (!(device == FPGA_1 || device == FPGA_2))
        return FAILURE;

    // Check if board exists
    map<unsigned int, Board *>::iterator it;
    it = boards.find(id);
    if (it == boards.end()) 
    {
        DEBUG_PRINT("AccessLayer::loadFirmware. " << id << " not connected");
        return FAILURE;   
    }

    // Get pointer to board
    Board *board = it -> second;
    
    // Call loadFirmware on board instance
    return board -> loadFirmwareBlocking(device, bitstream);
}

// Same as loadFirmware, however return only after the bitstream is loaded or
// an error occurs
RETURN  loadFirmwareBlocking(ID id, DEVICE device, const char* bitstream)
{
    // Check if device is valid
    if (!(device == FPGA_1 || device == FPGA_2 || device == FPGA_3 || device == FPGA_4 ||
          device == FPGA_5 || device == FPGA_6 || device == FPGA_7 || device == FPGA_8))
    {
        DEBUG_PRINT("AccessLayer::loadFirmwareBlocking. Invalid device");
        return FAILURE;
    }

    // Check if board exists
    map<unsigned int, Board *>::iterator it;
    it = boards.find(id);
    if (it == boards.end()) 
    {
        DEBUG_PRINT("AccessLayer::loadFirmwareBlocking. " << id << " not connected");
        return FAILURE;   
    }

    // Get pointer to board
    Board *board = it -> second;

    // Call loadFirmwareBlocking on board instance
    return board -> loadFirmwareBlocking(device, bitstream);
}
/*
// [Optional] Set a periodic register
RETURN setPeriodicRegister(ID id, DEVICE device, REGISTER reg, int period, CALLBACK callback)
{    
    return FAILURE;
}

// [Optional] Stop periodic register
RETURN stopPeriodicRegister(ID id, DEVICE device, REGISTER reg)
{    
    return FAILURE;
}

// [Optional] Set a periodic register
RETURN setConditionalRegister(ID id, DEVICE device, REGISTER reg, int period, CALLBACK callback)
{    
    return FAILURE;
}

// [Optional] Stop periodic register
RETURN stopConditionalRegister(ID id, DEVICE device, REGISTER reg)
{    
    return FAILURE;
}
*/ 
// Helper function to free up memory
void freeMemory(void *ptr)
{
    free(ptr);
}

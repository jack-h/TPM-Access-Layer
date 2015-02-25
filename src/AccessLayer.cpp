// Implementation of the TPM Access Layer API
// This is the main entry point, all high level commands have to pass
// through this file
// All global structure are stored here as well (these are not defined in the header file such that 
// clients do not have access to them -- are 'private')


// Includes and namespaces
#include <string>
#include <map>

#include "AccessLayer.hpp"
#include "Board.hpp"
#include "Utils.hpp"

using namespace std;

// The global boards map. Each board is identified via an IP address, which
// is translated into a board ID. All operation on the board are perofmed 
// through the same instance (similiar to the Singleton design pattern)make
map<unsigned int, Board *> boards;

// Set up internal structures to be able to communicate with a processing board
// Arguments:
ID connect(char* IP, unsigned short port)
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
    Board *board = new TPM(IP, port);
    boards[id] = board;

    DEBUG_PRINT("AccessLayer::connect. Connected to " << IP);

    // Return generated board ID
    return id;
}

// Clear up internal network structures for board in question
ERROR disconnect(ID id)
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

    // Once everything is done, destory Board object and return
    delete boards[id];
    boards.erase(it);

    DEBUG_PRINT("AccessLayer::disconnect. " << id << " disconnected");

    return SUCCESS;
}

// Rest board. Note that return from this function is not determined, due to
// the board being reset
ERROR resetBoard(ID id)
{    
    return FAILURE;
}

// Get board status
STATUS getStatus(ID id)
{    
    return OK;
}

// Get list of registers
REGISTER_INFO* getRegisterList(ID id, unsigned int *num_registers)
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
    return board -> getRegisterList(num_registers);
}

// Get a register's value
VALUE getRegisterValue(ID id, DEVICE device, REGISTER reg)
{  
    // Check if board exists
    map<unsigned int, Board *>::iterator it;
    it = boards.find(id);
    if (it == boards.end()) 
    {
        DEBUG_PRINT("AccessLayer::getRegisterValue. " << id << " not connected");
        return {0, FAILURE};
    }

    // Get pointer to board
    Board *board = it -> second;

    // Get register value from board
    return board -> getRegisterValue(device, reg);
}

// Set a register's value
ERROR setRegisterValue(ID id, DEVICE device, REGISTER reg, uint32_t value)
{    
    // Check if board exists
    map<unsigned int, Board *>::iterator it;
    it = boards.find(id);
    if (it == boards.end()) 
    {
        DEBUG_PRINT("AccessLayer::setRegisterValue. " << id << " not connected");
        return FAILURE;
    }

    // Get pointer to board
    Board *board = it -> second;

    // Get register value from board
    return board -> setRegisterValue(device, reg, value);
}

// Get a register's value
VALUE* getRegisterValues(ID id, DEVICE device, REGISTER reg, int N)
{    
    return NULL;
}

// Set a register's value
ERROR setRegisterValues(ID id, DEVICE device, REGISTER reg, int N, int *values)
{    
    return FAILURE;
}

// Load firmware to FPGA. This function return immediately. The status of the
// board can be monitored through the getStatus call
ERROR loadFirmware(ID id, DEVICE device, char* bitstream)
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
ERROR loadFirmwareBlocking(ID id, DEVICE device, char* bitstream)
{    
    // Check if device is valid
    if (!(device == FPGA_1 || device == FPGA_2))
        return FAILURE;

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

// [Optional] Set a periodic register
ERROR setPeriodicRegister(ID id, DEVICE device, REGISTER reg, int period, CALLBACK callback)
{    
    return FAILURE;
}

// [Optional] Stop periodic register
ERROR stopPeriodicRegister(ID id, DEVICE device, REGISTER reg)
{    
    return FAILURE;
}

// [Optional] Set a periodic register
ERROR setConditionalRegister(ID id, DEVICE device, REGISTER reg, int period, CALLBACK callback)
{    
    return FAILURE;
}

// [Optional] Stop periodic register
ERROR stopConditionalRegister(ID id, DEVICE device, REGISTER reg)
{    
    return FAILURE;
}

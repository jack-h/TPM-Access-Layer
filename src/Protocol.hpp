// Implements all functionality associated with the UCP protocol
// Handles all communication-related functionality

#ifndef PROTOCOL
#define PROTOCOL

#include "Definitions.hpp"

// UCP OPCODE Definitions
#define READ                 0x01
#define WRITE                0x02
#define BITWISE_AND          0x03
#define BITWISE_OR           0x04
#define FLASH_WRITE          0x06
#define FLASH_READ           0x07
#define FLASH_ERASE          0x08
#define FIFO_READ            0x09
#define FIFO_WRITE           0x0A
#define BIT_WRITE            0x0B
#define RESET_BOARD          0x11
#define PERIODIC_UPDATE      0x12
#define ASYNC_UPDATE         0x13
#define CANCEL_UPDATE        0x14
#define WAIT_FOR_PPS         0xFFFFFFFF

// Create protocol abstract class
class Protocol
{
    // Define functions to be implemented by derived classes
    public:
        // Create socket
        virtual ERROR createSocket(char *IP, int port) = 0;

        // Close socket
        virtual ERROR closeSocket() = 0;

        // Read register/memory area capability
        // This will take care of issuing multiple requests if 
        // the amount of data to read is larger than one UDP packet
        virtual ERROR readRegister() = 0;

        // Write register/memory area capability
        // This will take care of issuing multiple requests if the 
        // amount of data to write is larger than one UDP packet    
        virtual ERROR writeRegister() = 0;

    // Define functions common to any derived classes, if any
    protected:
        // Socket
        int socket;
};

// Protocol subclass implementing the UCP protocol
class UCP: public Protocol
{
    // Implement virtual functions
    public:
        ERROR createSocket(char *IP, int port);
        ERROR closeSocket();
        ERROR readRegister();
        ERROR writeRegister();
};

#endif  // PROTOCOL

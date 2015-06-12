// Implements all functionality associated with the UCP protocol
// Handles all communication-related functionality

#ifndef PROTOCOL_CLASS
#define PROTOCOL_CLASS

// Include OS-specific socket library
#ifdef __unix__ 
    #include <sys/socket.h>
    #include <arpa/inet.h>  
#elif defined(_WIN32) || defined(WIN32) || defined(WIN64) || defined(_WIN64)
    #include <winsock2.h>
#endif

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#include "Definitions.hpp"

// Define maximum payload size in words (4-bytes)
#define MAX_PAYLOAD_SIZE 350

// Create protocol abstract class
class Protocol
{
    public:
        // Declare constructor for all protocols
        Protocol()     
        {
            // Initialise socket descriptor
            this -> sockfd = -1;
        }
        
    // Define functions to be implemented by derived classes
    public:
        // Create socket
        virtual RETURN createConnection(const char *IP, int port) = 0;

        // Close socket
        virtual RETURN closeConnection() = 0;

        // Read register/memory area capability
        virtual VALUES readRegister(UINT address, UINT n = 1, UINT offset = 0) = 0;

        // Write register/memory area capability
        virtual RETURN writeRegister(UINT address, UINT *values, UINT n = 1, UINT offset = 0) = 0;

        // Read FIFO register capability
        virtual VALUES readFifoRegister(UINT address, UINT n = 1) = 0;

        // Write FIFO register capability
        virtual RETURN writeFifoRegister(UINT address, UINT *values, UINT n = 1) = 0;

        // Query board for list of firmware
        virtual FIRMWARE listFirmware(UINT *num_firmware) = 0;

        // Accessors
        char *getIP() { return this -> ip; }
        unsigned short getPort() { return this -> port; }

    // Define functions and properties common to any derived classes, if any
    protected:
        char            *ip;  // Board IP address
        unsigned short  port; // Port to communicate with board

        struct sockaddr_in board_addr;  // Board address structure
        int                sockfd;      // Socket
};

#endif  // PROTOCOL

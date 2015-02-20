#ifndef BOARD
#define BOARD

#include "Definitions.hpp"
#include "MemoryMap.hpp"
#include "Protocol.hpp"
#include "Utils.hpp"

#include <sys/socket.h>
#include <arpa/inet.h>
#include <string.h>

using namespace std;

// Class representation of a digital board
// This can eventually be sub-classed to add functionality
// specific to a particular board
class Board
{
    public:
        // Board constructor
        Board(char *ip, unsigned short port);

        // Board destructor
        virtual ~Board() = 0;

    // ---------- Public class functions --------
    public:

        // Create socket
        virtual ERROR connect() = 0;
    
        // Clear everything and remove connection
        virtual ERROR disconnect() = 0;

        // Get board status
        virtual STATUS getStatus(ID id) = 0;

        // Asynchronously load firmware to FPGA.
        virtual ERROR loadFirmware(ID id, FPGA fpga, char* bitstream) = 0;

        // Synchronously load firmware to FPGA
        virtual ERROR loadFirmwareBlocking(ID id, FPGA fpga, char* bitstream) = 0;

    // ---------- Protected class members ---------- 
    protected:

        unsigned int    id;   // Board identifier
        char            *ip;  // Board IP address
        unsigned short  port; // Port to communicate with board
        unsigned short  num_fpgas;  // Number of FPGAs on board

        Protocol        *protocol;  // Protocol instance to communicate with board

        struct sockaddr_in board_addr;  // Board address structure
        int                sockfd;      // Socket

        MemoryMap       *memory_map;
};

// Board derived class representing a Tile Processing Modules
class TPM: public Board
{
    public:
        // TPM constructor
        TPM(char *ip, unsigned short port);

        // TPM destructor
        ~TPM();

    public:
        // Create socket
        ERROR connect();

        // Clear everything and remove connection
        ERROR disconnect();

        // Get board status
        STATUS getStatus(ID id);

        // Asynchronously load firmware to FPGA.
        ERROR loadFirmware(ID id, FPGA fpga, char* bitstream);

        // Synchronously load firmware to FPGA
        ERROR loadFirmwareBlocking(ID id, FPGA fpga, char* bitstream);
};

#endif // BOARD

#include "Board.hpp"

#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdio.h>

// ------------------------ Board class implementation -----------------------

// Board constructor
Board::Board(char *ip, unsigned short port)
{
    // Check if IP is valid
    // TODO

    // Copy IP
    this -> ip = (char *) malloc(5 * sizeof(char));
    strcpy(this -> ip, ip);

    // Copy port
    this -> port = port; 

    // Set socket to -1
    sockfd = -1;

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
TPM::TPM(char *ip, unsigned short port) : Board(ip, port)
{
    // Set number of FPGAs
    this -> num_fpgas = 2;

    // Create protocol instance
    protocol = new UCP();

    // Create socket and set up TPM address structure
    this -> connect();
}

// TPM destructor
TPM::~TPM()
{  }

// Create socket and full up TPM address structure
ERROR TPM::connect()
{
    // Open socket
    if ((this -> sockfd = socket(AF_INET, SOCK_DGRAM, 0)) == -1)
    {
        perror("Could not create socket to board");        
        return FAILURE;
    }

    // Configure socket
    bzero(&board_addr, sizeof(board_addr));
    board_addr.sin_family = AF_INET;
    board_addr.sin_addr.s_addr = inet_addr(ip);
    board_addr.sin_port = htons(port);

    return SUCCESS;
}

// Clear everything and remove connection
ERROR TPM::disconnect()
{
    // Check if there's something pending
    // TODO

    // Close socket
    if (this -> sockfd != -1)
        close(this -> sockfd);
 
   return SUCCESS;
}

// Get board status
STATUS TPM::getStatus(ID id)
{
    return OK;
}

// Asynchronously load firmware to FPGA.
ERROR TPM::loadFirmware(ID id, FPGA fpga, char* bitstream)
{
    return FAILURE;
}

// Synchronously load firmware to FPGA
ERROR TPM::loadFirmwareBlocking(ID id, FPGA fpga, char* bitstream)
{
    // A new firmware needs to be loaded onto one of the FPGAs
    // NOTE: It is assumed that the new XML mapping contains all the
    // mappings (for CPLD, FPGA 1 and FPGA 2), so we just need to reload
    // the memory map

    // Get XML file and re-create the memory map
    char *xml_file = extractXMLFile(bitstream);

    printf("Loading firmware (memory map: %s\n", xml_file);

    // Remove any existing memory maps
    delete memory_map;

    // Create new memory map
    memory_map = new MemoryMap(xml_file);    

    return FAILURE;
}

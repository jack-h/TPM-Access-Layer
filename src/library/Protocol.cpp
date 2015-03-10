#include "Protocol.hpp"
#include "Utils.hpp"

#include <stdlib.h>

// UCP Constructor
UCP::UCP() : Protocol()
{
    // Initialise sequence number
    sequence_number = rand() % 100000;
}

// Create and initialise socket
ERROR UCP::createSocket(const char *IP, int port)
{
    // TODO: Check if IP is valid

    // Copy IP
    this -> ip = (char *) malloc(5 * sizeof(char));
    strcpy(this -> ip, IP);

    // Copy port
    this -> port = port; 

    // Open socket
    if ((this -> sockfd = socket(AF_INET, SOCK_DGRAM, 0)) == -1)
    {
        DEBUG_PRINT("UCP::constructor. Could not create socket for " << IP);
        return FAILURE;
    }

    // Configure socket
    bzero(&board_addr, sizeof(board_addr));
    board_addr.sin_family = AF_INET;
    board_addr.sin_addr.s_addr = inet_addr(ip);
    board_addr.sin_port = htons(port);

    // Set a receive timeout of 5 seconds
    struct timeval tv;
    tv.tv_sec = 5;  
    tv.tv_usec = 0; 
    setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, 
               (char *) &tv, sizeof(struct timeval));

    DEBUG_PRINT("UCP::constructor. Created socket for " << IP);

    return SUCCESS;
}

// Close network socket
ERROR UCP::closeSocket()
{
    return FAILURE;
}


// Send packet to board
ERROR UCP::sendPacket(char *message, size_t length)
{
    int ret;

    // Send datagram to board
    ret = sendto(sockfd,     // Socket
                 message,    // Message
                 length,     // Message length in bytes
                 0,          // Flags
                 (struct sockaddr *) &board_addr,  // Recipient
                 sizeof(struct sockaddr_in));	   // Struct size

    // If call failed, return error
    if (ret == -1)
        return FAILURE;

    // Return success
    return SUCCESS;
}

// Receive packet from board
ssize_t UCP::receivePacket(char *buffer, size_t max_length)
{
    // Wait for reply from board
    return recvfrom(sockfd,       // Socket
                    buffer,       // Buffer
                    max_length,   // Maximum buffer length
                    0,            // Flags
                    NULL,         // Receive from anyone
                    NULL);        // No structure provided, ignore
}

// Issue a read register request, and return reply
VALUES UCP::readRegister(uint32_t address, uint32_t n)
{
    // Create UCP header
    ucp_command_header *header = (ucp_command_header *) malloc(sizeof(ucp_command_header));

    // Increment sequence number
    uint32_t seqno = sequence_number++;

    // Fill out request
    // TODO: Explicitly change to little endian
    header -> psn     = seqno;
    header -> opcode  = OPCODE_READ;
    header -> nvalues = n;
    header -> address = address;
    
    // Send out packet  
    DEBUG_PRINT("UCP::readRegister. Sending packet");
    if (sendPacket((char *) header, sizeof(ucp_command_header)) == FAILURE)
    {
        DEBUG_PRINT("UCP::readRegister. Failed to send packet");
        free(header);
        return {0, FAILURE};
    }

    // Send packet no longer required, free memory
    free(header);

    // Sucessfully sent out packet, calculate responce size
    size_t reply_size = sizeof(ucp_reply_header) + n * sizeof(uint32_t);

    // Allocate buffer for reply
    ucp_read_reply *reply = (ucp_read_reply *) malloc(sizeof(ucp_read_reply));
    memset(reply, 0, sizeof(ucp_read_reply));

    // Wait for packet
    DEBUG_PRINT("UCP::readRegister. Receiving reply");
    ssize_t ret = receivePacket((char *) reply, reply_size);

    // Convert reply data to host endiannes
    // TODO: Check endiannes
    (reply -> header).addr = (reply -> header).addr;
    (reply -> header).psn = (reply -> header).psn;

    // Check number of bytes read
    if (ret < 0 || (size_t) ret < reply_size)
    {
        // Something wrong, return error
        free(reply);
        DEBUG_PRINT("UCP::readRegister. Failed to receive reply");
        return {NULL, FAILURE};
    }
    // Check if request was succesful on board
    else if ((reply -> header).psn != seqno || (reply -> header).addr != address)
    {   
        // Something wrong, return error
        free(reply);
        DEBUG_PRINT("UCP::readRegister. Command failed on board");
        return {NULL, FAILURE};
    }

    // Successfuly received reply, return values
    // TODO: Check endiannes
    
    // Create array containing required values
    uint32_t *values = (uint32_t *) malloc(n * sizeof(uint32_t));
    memcpy(values, reply -> data, n * sizeof(uint32_t));

    // We do not need the reply packet anymore
    free(reply);

    return {values, SUCCESS};
}

// Issue a write register request, and return reply
ERROR UCP::writeRegister(uint32_t address, uint32_t n, uint32_t *values)
{
    // Create UCP header
    ucp_command_packet *packet = (ucp_command_packet *) malloc(sizeof(ucp_command_packet));

    // Increment sequence number
    uint32_t seqno = sequence_number++;

    // Fill out request
    // TODO: explicitly change to little endian
    (packet -> header).psn     = seqno;
    (packet -> header).opcode  = OPCODE_WRITE;
    (packet -> header).nvalues = n;
    (packet -> header).address = address;

    // Place data in packet
    memcpy(&(packet -> data), values, n * sizeof(uint32_t));
    
    // Send out packet  
    DEBUG_PRINT("UCP::writeRegister. Sending packet");
    if (sendPacket((char *) packet, sizeof(ucp_command_header) + n * sizeof(uint32_t)) == FAILURE)
    {
        DEBUG_PRINT("UCP::writeRegister. Failed to send packet");
        free(packet);
        return FAILURE;
    }

    // Send packet no longer required, free memory
    free(packet);

    // Sucessfully sent out packet, calculate responce size
    size_t reply_size = sizeof(ucp_write_reply);

    // Allocate buffer for reply
    ucp_write_reply *reply = (ucp_write_reply *) malloc(sizeof(ucp_write_reply));
    memset(reply, 0, sizeof(ucp_write_reply));

    // Wait for packet
    DEBUG_PRINT("UCP::writeRegister. Receiving reply");
    ssize_t ret = receivePacket((char *) reply, reply_size);

    // Convert reply data to host endiannes
    // TODO: Check endiannes
    (reply -> header).addr = (reply -> header).addr;
    (reply -> header).psn = (reply -> header).psn;

    // Check number of bytes read
    if (ret < 0 || (size_t) ret < reply_size)
    {
        // Something wrong, return error
        free(reply);
        DEBUG_PRINT("UCP::writeRegister. Failed to receive reply");
        return FAILURE;
    }
    // Check if request was succesful on board
    else if ((reply -> header).psn != seqno || (reply -> header).addr != address)
    {   
        // Something wrong, return error
        free(reply);
        DEBUG_PRINT("UCP::readRegister. Command failed on board");
        return FAILURE;
    }

    // Free resources and return
    free(reply);

    return SUCCESS;
}

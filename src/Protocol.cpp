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
ERROR UCP::createSocket(char *IP, int port)
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
VALUE UCP::readRegister(uint32_t address)
{
    // Create UCP header
    ucp_command_header *header = (ucp_command_header *) malloc(sizeof(ucp_command_header));

    // Increment sequence number
    uint32_t seqno = sequence_number++;

    // Fill out request
    header -> psn     = htonl(seqno);
    header -> opcode  = htonl(OPCODE_READ);
    header -> nvalues = htonl(1);
    header -> address = htonl(address);
    
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
    size_t reply_size = sizeof(ucp_read_reply);

    // Allocate buffer for reply
    ucp_read_reply *reply = (ucp_read_reply *) malloc(sizeof(ucp_read_reply));
    memset(reply, 0, sizeof(ucp_read_reply));

    // Wait for packet
    DEBUG_PRINT("UCP::readRegister. Receiving reply");
    ssize_t ret = receivePacket((char *) reply, reply_size);

    // Convert reply data to host endiannes
    (reply -> header).addr = ntohl((reply -> header).addr);
    (reply -> header).psn = ntohl((reply -> header).psn);

    // Check number of bytes read
    if (ret < 0 || (size_t) ret < reply_size || (reply -> header).addr != address)
    {
        // Something wrong, return error
        free(reply);
        DEBUG_PRINT("UCP::readRegister. Failed to receive reply");
        return {0, FAILURE};
    }
    // Check if request was succesful on board
    else if ((reply -> header).psn != seqno)
    {   
        // Something wrong, return error
        free(reply);
        DEBUG_PRINT("UCP::readRegister. Command failed on board");
        return {0, FAILURE};
    }

    // Successfuly received reply, return value
    uint32_t value = ntohl(reply -> data);

    // Free resources and return
    free(reply);

    return {value, SUCCESS};
}

// Issue a write register request, and return reply
ERROR UCP::writeRegister(uint32_t address, uint32_t value)
{
    // Create UCP header
    ucp_command_packet *packet = (ucp_command_packet *) malloc(sizeof(ucp_command_packet));

    // Increment sequence number
    uint32_t seqno = sequence_number++;

    // Fill out request
    (packet -> header).psn     = htonl(seqno);
    (packet -> header).opcode  = htonl(OPCODE_WRITE);
    (packet -> header).nvalues = htonl(1);
    (packet -> header).address = htonl(address);
    packet -> data             = htonl(value);
    
    // Send out packet  
    DEBUG_PRINT("UCP::writeRegister. Sending packet");
    if (sendPacket((char *) packet, sizeof(ucp_command_packet)) == FAILURE)
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
    (reply -> header).addr = ntohl((reply -> header).addr);
    (reply -> header).psn = ntohl((reply -> header).psn);

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

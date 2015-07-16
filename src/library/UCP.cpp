#include "Utils.hpp"
#include "UCP.hpp"

#include <stdlib.h>

// UCP Constructor
UCP::UCP() : Protocol()
{
    // Initialise sequence number
    sequence_number = rand() % 100000;

    // Allocate packet once and re-use
    header      = (ucp_command_header *) malloc(sizeof(ucp_command_header));
    packet      = (ucp_command_packet *) malloc(sizeof(ucp_command_packet));
    read_reply  = (ucp_read_reply *) malloc(sizeof(ucp_read_reply));
    write_reply = (ucp_write_reply *) malloc(sizeof(ucp_write_reply));
}


// Create and initialise socket
RETURN UCP::createConnection(const char *IP, int port)
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
    memset(&board_addr, 0, sizeof(board_addr));
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
RETURN UCP::closeConnection()
{
    return FAILURE;
}


// Send packet to board
RETURN UCP::sendPacket(char *message, size_t length)
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
size_t UCP::receivePacket(char *buffer, size_t max_length)
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
VALUES UCP::read(UINT address, UINT n, UINT offset, bool fifo)
{
    // Value per payload
    unsigned values_per_payload = MAX_PAYLOAD_SIZE / sizeof(UINT);

    // Check if we need to split this request up into multiple packets
    unsigned num_packets = n / values_per_payload + 1;

    // Allocate memory area for full reply
    UINT *values = (UINT *) malloc(n * sizeof(UINT));

    // Issue requests one by one
    for(unsigned i = 0; i < num_packets; i++)
    {
        // Increment sequence number
        UINT seqno = sequence_number++;

        // Number of words for current request
        unsigned num_values = (i == num_packets - 1) ? n - i * values_per_payload: values_per_payload;

        // New address
        UINT currentAddress = (fifo) ? address : address + (offset + i * values_per_payload) * sizeof(UINT);

        // Fill out request
        header -> psn     = lendian(seqno);
        header -> opcode  = lendian((fifo) ? OPCODE_FIFO_READ : OPCODE_READ);
        header -> nvalues = lendian(num_values);
        header -> address = lendian(currentAddress);

        // Send out packet
        DEBUG_PRINT("UCP::readRegister. Sending packet");
        if (sendPacket((char *) header, sizeof(ucp_command_header)) == FAILURE)
        {
            DEBUG_PRINT("UCP::read. Failed to send packet");
            free(values);
            return {0, FAILURE};
        }

        // Successfully sent out packet, calculate response size
        size_t reply_size = sizeof(ucp_reply_header) + num_values * sizeof(UINT);

        // Allocate buffer for reply
        memset(read_reply, 0, sizeof(ucp_read_reply));

        // Wait for packet
        DEBUG_PRINT("UCP::read. Receiving reply");
        size_t ret = receivePacket((char *) read_reply, reply_size);

        // Convert reply data to host endiannes
        (read_reply -> header).addr = lendian((read_reply -> header).addr);
        (read_reply -> header).psn = lendian((read_reply -> header).psn);

        // Check number of bytes read
        if (ret < reply_size)
        {
            // Something wrong, return error
            DEBUG_PRINT("UCP::read. Failed to receive reply");
            free(values);
            return {NULL, FAILURE};
        }

        // Check if request was successful on board
        else if ((read_reply -> header).psn != seqno || (read_reply -> header).addr != currentAddress)
        {
            // Something wrong, return error
            DEBUG_PRINT("UCP::read. Command failed on board");
            free(values);
            return {NULL, FAILURE};
        }

        // Successfully received reply, return values
        // TODO: Check endiannes

        // Create array containing required values
        memcpy(values + i * values_per_payload, read_reply -> data, num_values * sizeof(UINT));
    }

    return {values, SUCCESS};
}

// Issue a write register request, and return reply
RETURN UCP::write(UINT address, UINT *values, UINT n, UINT offset, bool fifo)
{
    // Value per payload
    unsigned values_per_payload = MAX_PAYLOAD_SIZE / sizeof(UINT);

    // Check if we need to split this request up into multiple packets
    unsigned num_packets = n / values_per_payload + 1;

    // Issue requests one by one
    for(unsigned i = 0; i < num_packets; i++)
    {
        // Increment sequence number
        UINT seqno = sequence_number++;

        // Number of words for current request
        unsigned num_values = (i == num_packets - 1) ? n - i * values_per_payload: values_per_payload;

        // New address
        UINT currentAddress = (fifo) ? address : address + (offset + i * values_per_payload) * sizeof(UINT);

        // Fill out request
        (packet -> header).psn     = lendian(seqno);
        (packet -> header).opcode  = lendian((fifo) ? OPCODE_FIFO_WRITE : OPCODE_WRITE);
        (packet -> header).nvalues = lendian(num_values);
        (packet -> header).address = lendian(currentAddress);

        // Place data in packet
        memcpy(&(packet -> data), values + i * values_per_payload, num_values * sizeof(UINT));

        // Send out packet
        DEBUG_PRINT("UCP::write. Sending packet");
        if (sendPacket((char *) packet, sizeof(ucp_command_header) + num_values * sizeof(UINT)) == FAILURE)
        {
            DEBUG_PRINT("UCP::writeRegister. Failed to send packet");
            return FAILURE;
        }

        // Successfully sent out packet, calculate response size
        size_t reply_size = sizeof(ucp_write_reply);

        // Allocate buffer for reply
        memset(write_reply, 0, sizeof(ucp_write_reply));

        // Wait for packet
        DEBUG_PRINT("UCP::write. Receiving reply");
        size_t ret = receivePacket((char *) write_reply, reply_size);

        // Convert reply data to host endiannes
        (write_reply -> header).addr = lendian((write_reply -> header).addr);
        (write_reply -> header).psn = lendian((write_reply -> header).psn);

        // Check number of bytes read
        if (ret < reply_size)
        {
            // Something wrong, return error
            DEBUG_PRINT("UCP::write. Failed to receive reply");
            return FAILURE;
        }
            // Check if request was successful on board
        else if ((write_reply -> header).psn != seqno || (write_reply -> header).addr != currentAddress)
        {
            // Something wrong, return error
            DEBUG_PRINT("UCP::read. Command failed on board");
            return FAILURE;
        }
    }

    // All done
    return SUCCESS;
}

// Issue a write request to a register or memory block
VALUES UCP::readRegister(UINT address, UINT n, UINT offset)
{
    DEBUG_PRINT("UCP::readRegister. Reading register at " << address);
    return read(address, n, offset);
}

// Issue a read request to a register or memory block
RETURN UCP::writeRegister(UINT address, UINT *values, UINT n, UINT offset)
{
    DEBUG_PRINT("UCP::writeRegister. Writing to register at " << address);
    return write(address, values, n, offset);
}

// Issue a read request to a FIFO register
VALUES UCP::readFifoRegister(UINT address, UINT n)
{
    DEBUG_PRINT("UCP::readFifoRegister. Reading FIFO register at " << address);
    return read(address, n, 0, true);
}

// Issue a write request to a FIFO register
RETURN UCP::writeFifoRegister(UINT address, UINT *values, UINT n)
{
    DEBUG_PRINT("UCP::writeFifoRegister. Writing to FIFO register at " << address);
    return write(address, values, n, 0, true);
}

// TODO: Implement this when functionality is defined
FIRMWARE UCP::listFirmware(UINT *num_firmware)
{
    return NULL;
}

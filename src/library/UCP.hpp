#ifndef UCP_CLASS
#define UCP_CLASS

#include "Protocol.hpp"

// Protocol subclass implementing the UCP protocol
class UCP: public Protocol
{
    public:
        // UCP Constructor
        UCP();

    // Implement virtual functions
    public:
        RETURN createConnection(const char *IP, int port);
        RETURN closeConnection();
        VALUES readRegister(UINT address, UINT n = 1, UINT offset = 0);
        RETURN writeRegister(UINT address, UINT *values, UINT n = 1, UINT offset = 0);
        FIRMWARE listFirmware(UINT *num_firmware);

    private:
        // Send packet
        RETURN sendPacket(char *message, size_t length);

        // Receive packet
        size_t receivePacket(char *buffer, size_t max_length);

    private:
        // Sequence number
        UINT  sequence_number;

    private:
    
        // OPCODE definitions 
        enum { OPCODE_READ             = 0x01, 
               OPCODE_WRITE            = 0x02, 
               OPCODE_BITWISE_AND      = 0x03,
               OPCODE_BITWISE_OR       = 0x04,
               OPCODE_FLASH_WRITE      = 0x06,
               OPCODE_FLASH_READ       = 0x07,
               OPCODE_FLASH_ERASE      = 0x08,
               OPCODE_FIFO_READ        = 0x09,
               OPCODE_FIFO_WRITE       = 0x0A,
               OPCODE_BIT_WRITE        = 0x0B,
               OPCODE_RESET_BOARD      = 0x11,
               OPCODE_PERIODIC_UPDATE  = 0x12,
               OPCODE_ASYNC_UPDATE     = 0x13,
               OPCODE_CANCEL_UPDATE    = 0x14,
               OPCOED_WAIT_FOR_PPS     = 0xFFFFFFFF} 
               OPCODE;

        // Packet structure definitions
        // NOTE: __packed__ makes sure that the values are packet
        //       together in memory (no gaps)

        // Generic UCP command header
        struct ucp_command_header
        {
            UINT psn;
            UINT opcode;
            UINT nvalues;
            UINT address;
        } __attribute__ ((__packed__));

        // UCP command packet 
        struct ucp_command_packet
        {
            struct ucp_command_header header;
            UINT data[MAX_PAYLOAD_SIZE];
        } __attribute__ ((__packed__));


        // Generic UCP reply header
        struct ucp_reply_header 
        {
            UINT psn;
            UINT addr;
        } __attribute__ ((__packed__));

        // UCP write reply
        struct ucp_write_reply
        {
            struct ucp_reply_header header;
        } __attribute__ ((__packed__));

        // UCP read reply
        struct ucp_read_reply
        {
            struct ucp_reply_header header;
            UINT data[MAX_PAYLOAD_SIZE];
        } __attribute__ ((__packed__));

        // Declare and initiaslie packet once (hopefully for speed)
        ucp_command_header *header;
        ucp_command_packet *packet;
        ucp_read_reply     *read_reply;
        ucp_write_reply    *write_reply;
};

#endif  // UCP_CLASS

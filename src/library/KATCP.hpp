#ifndef UCP_CLASS
#define UCP_CLASS

#include "Protocol.hpp"

#include <vector>
#include <string>

// Protocol subclass implementing the UCP protocol
class KATCP: public Protocol
{
    public:
        // KATCP Constructor
        KATCP();

    // Implement virtual functions
    public:
        RETURN createSocket(const char *IP, int port);
        RETURN closeSocket();
        VALUES readRegister(UINT address,  UINT n, UINT offset = 0);
        RETURN writeRegister(UINT address, UINT *values, UINT n = 1, UINT offset = 0);

    // Public function which extend KATCP's functionality
    public:
        // Get register list from board
        REGISTER_INFO* getRegisterList(UINT *num_registers);

        // Get list of firmware from board
        FIRMWARE listFirmware(UINT *num_firmware);

        // Load boffile
        RETURN loadFirmwareBlocking(const char* boffile);
    
        // Get register index from internal list (to use as address)
        int getRegisterIndex(REGISTER reg);

    // Private functions
    private:
        void processInforms(std::string entry);
        void sendRequest(std::string command, std::vector<std::string> args);
        char *readReply(UINT bytes = 8192);

    // Public functions specific to KATCP
    public:
        KATCP *katcp; 

    // Protected class members
    protected:
        std::vector<std::string> boffiles;  // Store boffiles
        std::vector<std::string> registers; // Stores register names       
};

#endif  // UCP_CLASS

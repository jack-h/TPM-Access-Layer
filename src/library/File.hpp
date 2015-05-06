#ifndef FILE_CLASS
#define FILE_CLASS

#include "Protocol.hpp"

// Protocol subclass implementing the File protocol
class FileProtocol: public Protocol
{
	// Implement virtual functions
    public:
        RETURN createConnection(const char *IP, int port);
        RETURN closeConnection();
        VALUES readRegister(UINT address, UINT n = 1, UINT offset = 0);
        RETURN writeRegister(UINT address, UINT *values, UINT n = 1, UINT offset = 0);
        FIRMWARE listFirmware(UINT *num_firmware);

    // Define functions and properties common to any derived classes, if any
    protected:
        FILE     *fp;
};

#endif // FILE_CLASS
#include "Definitions.hpp"
#include "KATCP.hpp"
#include "Utils.hpp"

#include <sys/select.h>
#include <unistd.h>
#include <stdio.h>
#include <errno.h>

#include <algorithm>
#include <sstream>
#include <iostream>

using namespace std;

// ========================== Private functions =======================

// Process inform from board.
void KATCP::processInforms(string entry)
{  
    string logPrefix = "#log"; 
    string clientConnectedPrefix = "#client-connected";

    // Emptry inform, ignore
    if (entry.size() < 2)
        return;

    // Client connected inform, ignore
    else if (entry.substr(0, clientConnectedPrefix.size()) == clientConnectedPrefix)
        return;

    // Process logs
    else if (entry.substr(0, logPrefix.size()) == logPrefix)
    {
        entry = entry.substr(logPrefix.size(), entry.size());
        vector<string> entries = split(entry,  ' ');
        entry = processEscapes(entries[3]);
        cout << entry << endl;
    }
}

// Send KATCP request
void KATCP::sendRequest(string command, vector<string> args)
{
    // Generate command string
    string command_string = "?" + command;
    for(auto s: args)
        command_string += " " + s;
    command_string += "\n";

    const char *buf = command_string.c_str();
    unsigned int count = command_string.size();
    unsigned int sent = 0;
    unsigned int retries = 3;

    // Safe write, continue issuing the write request until
    // all the bytes are sent
    while(sent < count)
    {
        unsigned int s = write(this -> sockfd, buf, count - sent);

        // If write was unsuccesful and we still have a retry, continue
        if (s < 0 && retries > 0)
        {
            retries--;
            continue;
        }
        else if (s < 0)  // No retries left, issue error
        {
            DEBUG_PRINT("KATPC::sendRequest. Failed to write command to KATCP device");
            break;
        }
        else
            sent += s;
    }
}

// Read reply stream from KATCP device
char *KATCP::readReply(UINT bytes)
{   
    // Read data from socket
    int count, total = 0;
    char *buffer = (char *) malloc(bytes * sizeof(char));
    memset(buffer, 0, bytes * sizeof(char));

    bool ready = false;
    while (!ready)
    {
        if ((count = read(this -> sockfd, buffer + total, bytes)) <= 0)
        {
            // Timeout
            buffer[0] = '\0';
            if (errno == EAGAIN)
                return buffer;
            else // Error occured
            {
                DEBUG_PRINT("KATCP::readReply. Error while reading reply from KATCP device");
                return buffer;
            }
        }

        // Set timeout
        struct timeval tv;
        tv.tv_sec = 0;
        tv.tv_usec = 0; 

        // Successfully read data, check if any more data is pending
        // Set up sets for select
        fd_set readset;
        FD_ZERO(&readset);
        FD_SET(this -> sockfd, &readset);

        int result;
        do
        {
            result = select(1, &readset, NULL, NULL, &tv);
        } while (result == -1 && errno == EINTR);

        // Check if data is pending, and if so issue another read
        total += count;
        if (result <= 0 && buffer[total -1] == '\n')
            ready = true;
    }

    // All done, return
    return buffer;
}

// Process KATCP escapes
string KATCP::processEscapes(string &s)
{
    string value = "";
    for(unsigned i = 0; i < s.size(); i++)
    {
        if (s[i] == '\\')
        {
            if (s[i+1] == '0') 
                value += '\0';
            else if (s[i+1] == 'e')
                value += '\x1b';
            else if (s[i+1] == 't') 
                value += '\t';
            else if (s[i+1] == 'n') 
                value += '\n';
            else if (s[i+1] == 'r') 
                value += '\r';
            else if (s[i+1] == '\'') 
                value += '\'';
            else if (s[i+1] == '"') 
                value += '\"';
            else if (s[i+1] == '\\') 
                value += '\\';
            else if (s[i+1] == '_') 
                value += ' ';
            else
                i--;
            i++;
        }
        else
            value += s[i];
    }

    return value;
}

// =====================================================================

// Class constructor
KATCP::KATCP() : Protocol()
{
    
}

// Create and initialise socket
RETURN KATCP::createConnection(const char *IP, int port)
{
    // Copy IP
    this -> ip = (char *) malloc(5 * sizeof(char));
    strcpy(this -> ip, IP);

    // Copy port
    this -> port = port; 

    // Open socket
    if ((this -> sockfd = socket(AF_INET, SOCK_STREAM, 0)) == -1)
    {
        DEBUG_PRINT("KATCP::createSocket. Could not create socket for " << IP);
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

    // Connect to board
    if (connect(this -> sockfd, (struct sockaddr *) &board_addr, sizeof(board_addr)) < 0)
    {
        DEBUG_PRINT("KATCP::createSocket. Could not connect to board");
        return FAILURE;
    }

    DEBUG_PRINT("KATCP::constructor. Created socket for " << IP);

    // Connected to board, read inform generated by on connection
    processInforms(readReply());

    // Set logging level on board
    sendRequest(string("log-level"), { string("warn") });

    return SUCCESS;
}

// Close connection and socket
RETURN KATCP::closeConnection()
{
    // Check if socket was created
    if (this -> sockfd == -1)
        return SUCCESS;

    // Check is socket is still open
    int error = 0;
    socklen_t len = sizeof (error);
    if (getsockopt (this -> sockfd, SOL_SOCKET, SO_ERROR, &error, &len) != 0)
        return SUCCESS;

    // Attempt to close socket
    close(this -> sockfd);

    return SUCCESS;
}

// Issue a read register request, and return reply
VALUES KATCP::readRegister(UINT address, UINT n, UINT offset)
{
	DEBUG_PRINT("KATCP::readRegister. Reading register");
	
    // Send command
    string regname = this -> registers[address];
    sendRequest(string("read"), { regname, to_string(offset), to_string(n * 4) });

    // Store values
    vector<uint32_t> values;

    // Read replies for board
    RETURN result = FAILURE;
    bool processed = false;
    while (!processed)
    {
        // Four bytes per word * 2 for escape characters + buffer
        char *buffer = readReply(n * 4 * 2 + 15); 
        string reply = string(buffer); 
        istringstream inputStream;
        inputStream.str(reply);
        string endRequestPrefix = "!read"; 
        while(!inputStream.eof())
        {
            string line;
            getline(inputStream, line);

            // Line contains result
            if (line.substr(0, endRequestPrefix.size()) == endRequestPrefix)
            {
                line = line.substr(endRequestPrefix.size() + 1, line.size());
                processed = true;

                // Check if command was succesful
                if (line.substr(0, 2) != "ok")
                {
                    DEBUG_PRINT("KATCP::readRegister. Command failed on board");
                    continue;
                } 

                // Extract binary string 
                line = line.substr(3, line.size());

                // Process escapes
                line = processEscapes(line);

                // Check if size is a multiple of 4
                if (line.size() < 4 || line.size() % 4 != 0)
                {
                    DEBUG_PRINT("KATCP::readRegister. Incorrect value reply size");
                    continue;
                }

                // We have our data, convert to unsigned integers
                const unsigned char *buf = (unsigned char *) line.c_str();
                for (unsigned i = 0; i < line.size(); i+= 4)
                {
                    uint32_t value = 0;
                    value |= (*buf++ << 24);
                    value |= (*buf++ << 16);
                    value |= (*buf++ << 8);
                    value |= (*buf++     );
                    values.push_back(value);
                }
                result = SUCCESS;
            }
            else    
                // Other type of output, treat as inform
                // TODO: Get these
                processInforms(line);
        }

		 free(buffer);
    }

    // Create VALUES result
    if (result == SUCCESS)
    {
        UINT *retValues = (UINT *) malloc(values.size() * sizeof(UINT));
        memcpy(retValues, &values[0], values.size() * sizeof(UINT));
        return {retValues, result};
    }
    else
        return {NULL, result};
}

// Issue a write register request, and return reply
RETURN KATCP::writeRegister(UINT address, UINT *values, UINT n, UINT offset)
{
	DEBUG_PRINT("KATCP::writeRegister. Writing to register");
	
    // Convert unsigned integer to string
    string packedData = "";

    // Loop over values and package them
    for(unsigned i = 0; i < n; i++)
    {
        // Split unsigned integer into 4 bytes
        unsigned char bytes[4];
        bytes[3] = values[i] & 0xFF;
        bytes[2] = (values[i] >> 8)  & 0xFF;
        bytes[1] = (values[i] >> 16) & 0xFF;
        bytes[0] = (values[i] >> 26) & 0xFF;

        // Concatenate each byte to the packed string
        for(unsigned j = 0; j < 4; j++)
        {
            if (bytes[j] == '\0')
                packedData += "\\0";
            else if (bytes[j] == '\t')
                packedData += "\\t";
            else if (bytes[j] == '\n')
                packedData += "\\n";
            else if (bytes[j] == '\r')
                packedData += "\\r";
            else if (bytes[j] == '\'')
                packedData += "\\'";
            else if (bytes[j] == '\"')
                packedData += "\\\"";
            else if (bytes[j] == '\\')
                packedData += "\\\\";
            else if (bytes[j] == ' ')
                packedData += "\\_";
            else
                packedData += bytes[j];  
        }    
    }

    // Send command
    string regname = this -> registers[address];
    sendRequest(string("write"), { regname, to_string(offset), packedData });

    // Read replies from board
    bool processed = false;
    bool succesful = true;
    while (!processed)
    {
        char *buffer = readReply();
        string reply = string(buffer); 
        istringstream inputStream(reply);
        string endRequestPrefix = "!write";
        while (!inputStream.eof())
        {
            // Categorise statement
            string line;
            getline(inputStream, line);
            // Line contains result
            if (line.substr(0, endRequestPrefix.size()) == endRequestPrefix)
            {
                // Check if command was succesful
                line = line.substr(endRequestPrefix.size() + 1, line.size());
                string okString = "ok";
                if (line.substr(0, okString.size()) != okString)
                    DEBUG_PRINT("KATCP::writeRegister. Command failed on board");
                else
                    succesful = true;

                processed = true;
            }
            else    
                // Other type of output, treat as inform
                // TODO: Get these
                processInforms(line);
        }

        free(buffer);
    }

    return ((succesful) ? SUCCESS : FAILURE);
}

// Get list of boffiles from board
FIRMWARE KATCP::listFirmware(UINT *num_firmware)
{
	DEBUG_PRINT("KATCP::listFirmware. Querying board for firmware list");
	
    *num_firmware = 0;

    // Send command to board
    sendRequest(string("listbof"), vector<string>());

    // Clear current list of firmware
    this -> boffiles.clear();
    
    // Keep reading output from katcp device until the command has been
    // executed. Each entry is seperated by a newline
    // Only informs starting with #listbof belong to the reply
    bool processed = false;
    while (!processed)
    {
        // Read data, separate entitires and process one by one
        char *buffer = readReply();
        string reply = string(buffer); 
        istringstream inputStream(reply);
        string bofEntryPrefix   = "#listbof";
        string endRequestPrefix = "!listbof";
        while(!inputStream.eof())
        {
            // Categorise statement
            string line;
            getline(inputStream, line);

            // Line contains a new boffile
            if (line.substr(0, bofEntryPrefix.size()) == bofEntryPrefix)
            {
                // Remove prefix and space to extract boffile name
                line = line.substr(bofEntryPrefix.size(), line.size()); 
                line.erase(remove_if(line.begin(), line.end(), ::isspace), line.end());

                // Add boffile to list of boffiles
                this -> boffiles.push_back(line);
            }
            // End of command reply line
            else if (line.substr(0, endRequestPrefix.size()) == endRequestPrefix)
            {
                // Check if number of processed boffiles is the same as the
                // number sent by the server
                line = line.substr(bofEntryPrefix.size() + 1, line.size());

                // Check if command was successful on board
                string okString = "ok";
                if (line.substr(0, okString.size()) != okString)
                {
                    DEBUG_PRINT("KATCP::listFirmware. Command failed on board");
                    this -> boffiles.clear();
                }
                else
                {
                    // Remove white spaces
                    line = line.substr(okString.size(), line.size());
                    line.erase(remove_if(line.begin(), line.end(), ::isspace), line.end());
                    
                    // Check if number of entries sent matches number received
                    int numSent = stoi(line, 0, 10);
                    if (numSent != (int) boffiles.size())
                        DEBUG_PRINT("KATCP::listFirmware. Incorrect number of boffiles received");
                }
                processed = true;
            }
            else
                // Other type of output, treat as inform
                processInforms(line);
        }

        free(buffer);
    }

    // Create list of firmware and return
    *num_firmware = this -> boffiles.size();

    FIRMWARE firmware = (FIRMWARE) malloc(*num_firmware * sizeof(char *));
    for (unsigned i = 0; i < *num_firmware; i++)
        firmware[i] = const_cast<char *>(this -> boffiles[i].c_str());

    return firmware;
}

// Get list of registers from board
REGISTER_INFO* KATCP::getRegisterList(UINT *num_registers)
{
	DEBUG_PRINT("KATCP::getRegisterList. Querying board for register list");
	
    *num_registers = 0;

    // Send command to board
    sendRequest(string("listdev"), vector<string>());

    // Clear current list of registers
    this -> registers.clear();
    
    // Keep reading output from katcp device until the command has been
    // executed. Each entry is seperated by a newline
    // Only informs starting with #listdev belong to the reply
    bool processed = false;
    while (!processed)
    {
        // Read data, separate entitires and process one by one
        char *buffer = readReply();
        string reply = string(buffer); 
        istringstream inputStream(reply);
        string devEntryPrefix   = "#listdev";
        string endRequestPrefix = "!listdev";
        while(!inputStream.eof())
        {
            // Categorise statement
            string line;
            getline(inputStream, line);

            // Line contains a new register entry
            if (line.substr(0, devEntryPrefix.size()) == devEntryPrefix) 
            {
                // Remove prefix and empty space from line to 
                // extract register name
                line = line.substr(devEntryPrefix.size(), line.size());
                line.erase(remove_if(line.begin(), line.end(), ::isspace), line.end());
        
                // Add register to list of registers
                this -> registers.push_back(line);
            }
            // End of command reply line
            else if  (line.substr(0, endRequestPrefix.size()) == endRequestPrefix)
            {   
                // End of request, check if number of processed registers is
                // the same as the number sent by the server
                line = line.substr(devEntryPrefix.size() + 1, line.size());

                // Check if command was successful on board
                string okString = "ok";
                if (!(line.substr(0, okString.size()) == okString))
                {
                    DEBUG_PRINT("KATCP::getRegisterList. Command failed on board");
                    this -> registers.clear();   // Failed
                }

                processed = true;  
            }
            else
                // Other type of output, treat as inform
                processInforms(line);
        }   

        free(buffer); 
    }

    // Populate list of registers and return
    *num_registers = this -> registers.size();
    
    REGISTER_INFO *list = (REGISTER_INFO *) malloc(*num_registers * sizeof(REGISTER_INFO));
    for (unsigned i = 0; i < *num_registers; i++)
    {
        // Copy name
        list[i].name = const_cast<char *>(this -> registers[i].c_str());
        list[i].address = i;
        list[i].type = FIRMWARE_REGISTER;
        list[i].device = FPGA_1;
        list[i].permission = READWRITE;
        list[i].size = 1; 
        list[i].bitmask = 0xFFFFFFFF;
        list[i].bits = 32;
        list[i].description = "";
    }

    return list;
}

// Load boffile
RETURN KATCP::loadFirmwareBlocking(const char* boffile)
{
	DEBUG_PRINT("KATCP::loadFirmware. Loading firmware");
	
    // Send command to board
    sendRequest(string("progdev"), { string(boffile) });

    // Set when ready from operation
    bool processed = false;
    bool programmed = false;

    // Keep listening to the socket until the commadn is succesful or 
    // a warning is generated stating that the boffile couldn't be loaded
    while (!processed)
    {
        char *buffer = readReply();
        string reply = string(buffer); 
        istringstream inputStream(reply);
        string progdevSuccess = "!progdev";
        string progdevFailed  = "#log warn "; 
        while (!inputStream.eof())
        {
            // Categorise statement
            string line;
            getline(inputStream, line);
           
            // Line contains a new boffile entry
            if (line.substr(0, progdevSuccess.size()) == progdevSuccess)
            { 
                // End of request, check if number of processed boffiles is
                // the same as the number sent by the server
                line = line.substr(progdevSuccess.size() + 1, line.size()); 

                // Check if command was successful on board
                string okString = "ok";
                if (line.substr(0, okString.size()) == okString)
                    programmed = true;                
                else
                    DEBUG_PRINT("KATCP::loadFirmware. Command failed on board");
                processed = true;
            }
            else if (line.substr(0, progdevFailed.size()) == progdevFailed)
            {
                DEBUG_PRINT("KATCP::loadFirmware. Command failed on board");
                processed = true;
                programmed = false;
            }
            // Line does not belong to command reply, ignore for now
            else
                // Other type of output, treat as inform
                processInforms(line);
        }

        free(buffer);
    }

    return ((programmed) ? SUCCESS : FAILURE);
}

// Get register index from internal list (to use as address)
int KATCP::getRegisterIndex(REGISTER reg)
{
    vector<string>::iterator it;
    it = find(this -> registers.begin(), this -> registers.end(), reg);
    if (it == registers.end())
        return -1;
    else 
        return it - this -> registers.begin();
}

// ------ Functions not supported by ROACH -------------
VALUES KATCP::readFifoRegister(UINT address, UINT n) {
    return VALUES();
}

RETURN KATCP::writeFifoRegister(UINT address, UINT *values, UINT n) {
    return NOT_IMPLEMENTED;
}

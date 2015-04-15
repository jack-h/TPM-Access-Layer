#include <stdio.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <stdlib.h>
#include <string.h>

#include <iostream>
#include <vector>
#include <algorithm>
#include <sstream>
#include <string>
#include <map>

using namespace std;

#define MAX_SIZE 8192

unsigned short port   = 7147;
string IP             = "192.168.100.2";

char buf[MAX_SIZE];

// Enumeration defining log level
enum LOG_LEVEL { LOG_OFF = 0,   LOG_FATAL = 1, LOG_ERROR = 2,
                 LOG_WARN = 3,  LOG_INFO = 4,  LOG_DEBUG = 5,  
                 LOG_TRACE = 6, LOG_ALL = 7 };

std::map<LOG_LEVEL, std::string> logLevel;

// TODO: safe_write

// Vector of strings to hold list of boffiles
vector<string> boffiles;

// Vector of string to hold list of registers
vector<string> registers;

// ======================================== Helper Functions ==================================
vector<string> &split(const string &s, char delim, vector<string> &elems) 
{
    stringstream ss(s);
    string item;
    while (getline(ss, item, delim)) 
        if (!item.empty())
            elems.push_back(item);
    return elems;
}


vector<string> split(const string &s, char delim) 
{
    vector<string> elems;
    split(s, delim, elems);
    return elems;
}

string stringReplace(string &s, string toReplace, string replaceWith)
{
    return (s.replace(s.find(toReplace), toReplace.length(), replaceWith));
}

string processEscapes(string &s, const char to_detect, const char to_replace)
{
    string value = "";
    for(unsigned i = 0; i < s.size(); i++)
        if (s[i] == '\\' && s[i+1] == to_detect) 
        {
            value += to_replace;
            i++;
        }
        else
            value += s[i];
    return value;
}

// ==============================================================================================

void setLogLevel(int sock, LOG_LEVEL level)
{
    // Create string comamand
    string command_string = string("?log-level ") + logLevel[level] + string("\n");

    // Send command to katcp server
    if (write(sock, command_string.c_str(), command_string.size()) < 0)
    {
        perror("Failed to write listbof request");
        return;
    }

    // Wait for confirmation of changed log level
    bool processed = false;
    while (!processed)
    { 
        // Read data from socket
        if (read(sock, buf, MAX_SIZE) == -1)
        {
            perror("Error during socket read");
            continue;
        }

        istringstream inputStream(buf);
        string logLevelOK = "!log-level ok";
        while (!inputStream.eof())
        {
            string line;
            getline(inputStream, line);

            // Check if status is ok
            if (line.substr(0, logLevelOK.size()) == logLevelOK)
            {
                // Check if correct log level was set
                line = line.substr(logLevelOK.size(), line.size());
                line.erase(remove_if(line.begin(), line.end(), ::isspace), line.end());   

                cout << "Changed log level to " << line << ", " << logLevel[level] << " required" << endl;
                processed = true;
            }
            else
            {
                // Other checks
            }
        }
    }

    // Clear buffer
    memset(buf, 0, MAX_SIZE);
}

void listbof(int sock)
{
    // Create command string
    string command_string = "?listbof\n";
    
    // Send command to katcp server
    if (write(sock, command_string.c_str(), command_string.size()) < 0)
    {
        perror("Failed to write listbof request");
        return;
    }

    // Clear vector of boffiles
    boffiles.clear();

    // Keeping reading output from the katcp server until !listbof is met. 
    // Each entry is seperated by a newline
    // Only informs starting with #listbof belong to the reply to this request
    bool processed = false;
    while (!processed)
    {
        // Read data from socket
        if (read(sock, buf, MAX_SIZE) == -1)
        {
            perror("Error during socket read");
            continue;
        }

        // We have read some data, convert string, separate entries and process
        // each entry one by one
        istringstream inputStream(buf);
        string bofEntryPrefix   = "#listbof";
        string endRequestPrefix = "!listbof";
        while (!inputStream.eof())
        {
            // Categorise statement
            string line;
            getline(inputStream, line);
           
            // Line contains a new boffile entry
            if (line.substr(0, bofEntryPrefix.size()) == bofEntryPrefix) 
            {
                // Remove prefix and empty space from line to extract boffile name
                line = line.substr(bofEntryPrefix.size(), line.size());
                line.erase(remove_if(line.begin(), line.end(), ::isspace), line.end());
        
                // Add boffile to list of boffiles
                boffiles.push_back(line);
            }
            // End of command reply line
            else if (line.substr(0, endRequestPrefix.size()) == endRequestPrefix)
            {
                // End of request, check if number of processed boffiles is the
                // same as the number sent by the server
                line = line.substr(bofEntryPrefix.size() + 1, line.size()); // +1 for extra space

                // Check if command was successful on board
                string okString = "ok";
                if (line.substr(0, okString.size()) == okString)
                { 
                    // Remove white spaces
                    line = line.substr(okString.size(), line.size());
                    line.erase(remove_if(line.begin(), line.end(), ::isspace), line.end());

                    // Check if numer of sent entries matches number of read entries
                    int numSent = stoi(line, 0, 10);
                    if (numSent != boffiles.size())
                        cerr << "Server sent " << numSent << " entries, received " << boffiles.size() << endl;
                }
                else  // Failed
                    boffiles.clear();

                processed = true;
            }
            // Line does not belong to command reply, ignore for now
            else if (line.size() >= 2)
            {
                cout << "Unrecognised reply: " << line << endl;
            }
        }
    }

    // Clear buffer
    memset(buf, 0, MAX_SIZE);

    // TEMPORARY: Print boffiles
    cout << "List of boffiles:" << endl;
    for (auto s : boffiles)
        cout << s << endl;
    cout << endl;
}

void progdev(int sock, string boffile)
{
    // Create command string
    string command_string = string("?progdev ") + boffile + string("\n");

    // Set when ready from operation
    bool processed  = false;
    bool programmed = false;

    // Send command to katcp server
    if (write(sock, command_string.c_str(), command_string.size()) < 0)
    {
        perror("Failed to write progdev request");
        return;
    }

    sleep(5); 

    // Keep listening to the socket until the command is successful or a 
    // warning is generated stating that the boffile couldn't be loaded 
    // successfully
    while (!processed)
    {
        // Read data from socket
        int count;
        if ((count = read(sock, buf, MAX_SIZE)) == -1)
        {
            perror("Error during socket read");
            continue;
        }

        if (count == 0)
            processed = true;
    
        // We have read some data, convert string, separate entries and process
        // each entry one by one
        istringstream inputStream(buf);
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
                // End of request, check if number of processed boffiles is the
                // same as the number sent by the server
                line = line.substr(progdevSuccess.size() + 1, line.size()); // +1 for extra space

                // Check if command was successful on board
                string okString = "ok";
                if (line.substr(0, okString.size()) == okString)
                    programmed = true;                

                processed = true;
            }
            else if (line.substr(0, progdevFailed.size()) == progdevFailed)
            {
                processed = true;
                programmed = false;
            }
            // Line does not belong to command reply, ignore for now
            else if (line.size() >= 2)
            {
                cout << "Unrecognised reply: " << line << endl;
            }
        }
    }

    if (programmed)
        cout << "Successfully loaded " << boffile << " on board" << endl;
    else
        cerr << "Failed to program board with " << boffile << endl;

    // Clear buffer
    memset(buf, 0, MAX_SIZE);
}

void listdev(int sock)
{
    // Create command string
    string command_string = "?listdev\n";
    
    // Send command to katcp server
    if (write(sock, command_string.c_str(), command_string.size()) < 0)
    {
        perror("Failed to write listdev request");
        return;
    }

    // Clear vector of boffiles
    registers.clear();

    // Keeping reading output from the katcp server until !listbof is met. 
    // Each entry is seperated by a newline
    // Only informs starting with #listbof belong to the reply to this request
    bool processed = false;
    while (!processed)
    {
        // Read data from socket
        if (read(sock, buf, MAX_SIZE) == -1)
        {
            perror("Error during socket read");
            continue;
        }

        // We have read some data, convert string, separate entries and process
        // each entry one by one
        istringstream inputStream(buf);
        string devEntryPrefix   = "#listdev";
        string endRequestPrefix = "!listdev";
        while (!inputStream.eof())
        {
            // Categorise statement
            string line;
            getline(inputStream, line);
           
            // Line contains a new REGISTER entry
            if (line.substr(0, devEntryPrefix.size()) == devEntryPrefix) 
            {
                // Remove prefix and empty space from line to extract register name
                line = line.substr(devEntryPrefix.size(), line.size());
                line.erase(remove_if(line.begin(), line.end(), ::isspace), line.end());
        
                // Add register to list of registers
                registers.push_back(line);
            }
            // End of command reply line
            else if (line.substr(0, endRequestPrefix.size()) == endRequestPrefix)
            {
                // End of request, check if number of processed registers is the
                // same as the number sent by the server
                line = line.substr(devEntryPrefix.size() + 1, line.size()); // +1 for extra space

                // Check if command was successful on board
                string okString = "ok";
                if (!(line.substr(0, okString.size()) == okString))
                {
                    cerr << "Failed to list registers" << endl;
                    boffiles.clear();   // Failed
                }

                processed = true;
            }
            // Line does not belong to command reply, ignore for now
            else if (line.size() >= 2)
            {
                cout << "Unrecognised reply: " << line << endl;
            }
        }
    }

    // Clear buffer
    memset(buf, 0, MAX_SIZE);

    // TEMPORARY: Print boffiles
    cout << "List of registers:" << endl;
    for (auto s : registers)
        cout << s << endl;
    cout << endl;
}

void read(int sock, string regname, uint32_t offset = 0, uint32_t byte_count = 4)
{
    // Create command string
    string command_string = "?read " + regname + string(" ") + to_string(offset) + string(" ") + to_string(byte_count) + string("\n");

    // Send command to katcp server
    if (write(sock, command_string.c_str(), command_string.size()) < 0)
    {
        perror("Failed to write read request");
        return;
    }

    // Store values
    vector<uint32_t> values;
    
    // Read replies from board
    bool processed = false;
    while (!processed)
    {
        // Read data from socket
        if (read(sock, buf, MAX_SIZE) == -1)
        {
            perror("Error during socket read");
            continue;
        }

        // We have read some data, convert string, separate entries and process
        // each entry one by one
        istringstream inputStream(buf);
        string logPrefix        = "#log";
        string endRequestPrefix = "!read";
        while (!inputStream.eof())
        {
            // Categorise statement
            string line;
            getline(inputStream, line);

             // Line contains result
            if (line.substr(0, endRequestPrefix.size()) == endRequestPrefix)
            {
                line = line.substr(endRequestPrefix.size() + 1, line.size());

                processed = true;

                // Check if command was successful
                if (line.substr(0, 2) != "ok")
                {
                    cerr << "Failed to read" << endl;
                    continue;     
                }

                // Extract binary string 
                line = line.substr(3, line.size());

                // Process nulls
                line = processEscapes(line, '0', '\0');

                // Check if size is a multiple of 4
                if (line.size() < 4 || line.size() % 4 != 0)
                {
                    cerr << "Incorrect value reply size: " << line.size() << endl;
                    continue;
                }

                // We have our data, convert to unsigned integers
                for(unsigned i = 0; i < line.size() / 4; i++)
                {
                    const char *data = line.substr(i * 4, (i + 1) * 4).c_str();
                    uint32_t value = 0;
                    value |= ( data[0] << 24 );
                    value |= ( data[1] << 16 );
                    value |= ( data[2] <<  8 );
                    value |= ( data[3]       );
                    values.push_back(value);
                }               
            }
            else if (line.substr(0, logPrefix.size()) == logPrefix)
            {
                // We have received a warning, extract messages
                line = line.substr(logPrefix.size(), line.size());
                vector<string> entries = split(line, ' ');
                
                // Print out message
                cout << processEscapes(entries[3], '_', ' ') << endl;
                
            }
            // Line does not belong to command reply, ignore for now
            else if (line.size() >= 2)
            {
                cout << "Unrecognised reply: " << line << endl;
            }
        }
    }

    for(auto s : values)
        cout << s << " ";
    cout << endl;

    // Clear buffer
    memset(buf, 0, MAX_SIZE);
}

void write(int sock, string regname, uint32_t *values, uint32_t numValues,  uint32_t offset = 0)
{
    string packedData = "";

    // Loop over values and package them
    for(unsigned i = 0; i < numValues; i++)
    {
        // Split unsigned integer into 4 bytes
        char bytes[4];
        bytes[3] = values[i] & 0xFF;
        bytes[2] = (values[i] >> 8)  & 0xFF;
        bytes[1] = (values[i] >> 16) & 0xFF;
        bytes[0] = (values[i] >> 26) & 0xFF;

        // Catenate each byte to the packed string
        for(unsigned j = 0; j < 4; j++)
            if (bytes[j] == '\0')
                packedData += "\\0";
            else
                packedData += bytes[j];      
    }

    // Create command string
    string command_string = "?write " + regname + string(" ") + to_string(offset) + string(" ") + packedData + "\n";

    // Send command to katcp server
    if (write(sock, command_string.c_str(), command_string.size()) < 0)
    {
        perror("Failed to write write request");
        return;
    }

    // Read replies from board
    bool processed = false;
    while (!processed)
    {
        // Read data from socket
        if (read(sock, buf, MAX_SIZE) == -1)
        {
            perror("Error during socket read");
            continue;
        }

        // Sent write request, wait for reply
        istringstream inputStream(buf);
        string logPrefix        = "#log";
        string endRequestPrefix = "!write";
        while (!inputStream.eof())
        {
            // Categorise statement
            string line;
            getline(inputStream, line);
    
             // Line contains result
            if (line.substr(0, endRequestPrefix.size()) == endRequestPrefix)
            {
                processed = true;
                cout << "Write successful" << endl;
            }
            else if (line.substr(0, logPrefix.size()) == logPrefix)
            {
                // We have received a warning, extract messages
                line = line.substr(logPrefix.size(), line.size());
                vector<string> entries = split(line, ' ');
                
                // Print out message
                cout << processEscapes(entries[3], '_', ' ') << endl;
                
            }
            // Line does not belong to command reply, ignore for now
            else if (line.size() >= 2)
            {
                cout << "(Write) Unrecognised reply: " << line << endl;
            }
        }
    }
}

int main()
{
    // Client socket descriptor
    int sock;
    struct sockaddr_in serv_addr;

    // Create socket
    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        perror("Failed to create socket");
        exit(-1);
    }

    // Set a receive timeout of 5 seconds
    struct timeval tv;
    tv.tv_sec = 5;  
    tv.tv_usec = 0; 
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, 
               (char *) &tv, sizeof(struct timeval));

    // Populate sockaddr_in structure    
    bzero((char *) &serv_addr, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = inet_addr(IP.c_str());
    serv_addr.sin_port = htons(port);

    // Connect
    if (connect(sock, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0)
    {
        perror("Failed to connect");
        exit(-1);
    }

    // Populate log levels
    logLevel[LOG_OFF]   = string("off");
    logLevel[LOG_FATAL] = string("fatal");
    logLevel[LOG_ERROR] = string("error");
    logLevel[LOG_WARN]  = string("warn");
    logLevel[LOG_INFO]  = string("info");
    logLevel[LOG_DEBUG] = string("debug");
    logLevel[LOG_TRACE] = string("trace");
    logLevel[LOG_ALL]   = string("all");

    // Read any informs generated by the katcp server and just print to screen
    read(sock, buf, MAX_SIZE);
    printf("%s\n", buf);

    // Connection successful, we can start communicating with the katcp server (wherever it may reside)

    // Set log level
    setLogLevel(sock, LOG_WARN);

    // Get list of boffiles
    listbof(sock);

    // Program board
//    progdev(sock, boffiles[0]);

    // List registers
    listdev(sock);

    // Read a register
    read(sock, string("gbe_dest_port"), 0, 4);

    // Write a register
    uint32_t toWrite = 42;
    write(sock, string("gbe_dest_port"), &toWrite, 1);

    // Read value again
    read(sock, string("gbe_dest_port"), 0, 4);    

    exit(0);
}

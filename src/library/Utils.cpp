#include "Utils.hpp"

// Include OS-specific socket library
#ifdef __unix__ 
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
#elif defined(_WIN32) || defined(WIN32) || defined(WIN64) || defined(_WIN64)
    #include <winsock2.h>
#endif

#include <sstream>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>

using namespace std;

// Convert string IP address to a 32-bit number
ID convertIPtoID(const char *IP)
{
    struct sockaddr_in sa;
    inet_pton(AF_INET, IP, &(sa.sin_addr));
    return (ID) abs((long) sa.sin_addr.s_addr);
}

// Extract XML mapping file from filepath
char *extractXMLFile(const char *filepath)
{
    // NOTE: This is currently a hack, to be updated
    // Assumes that filepath has a 3-character extension which
    // need to be changed to .xml
    int len = strlen(filepath);
    
    char *xml_file = (char *) malloc ((len + 1) * sizeof(char));
    strcpy(xml_file, filepath);
    xml_file[len - 3] = 'x';
    xml_file[len - 2] = 'm';
    xml_file[len - 1] = 'l';

    return xml_file;
}

// Check if architecture is big endian
UINT lendian(UINT value)
{
    #if __ENDIANNESS__ == __BIG_ENDIAN
        value = (value & 0x0000FFFF) << 16 | (value & 0xFFFF0000) >> 16;
        value = (value & 0x00FF00FF) << 8  | (value & 0xFF00FF00) >> 8;
    #endif

    return value;
}

// Split string by delimeter
vector<string> & split(const string &s, char delim, vector<string> &elems) 
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


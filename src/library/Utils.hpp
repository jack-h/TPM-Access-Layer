#ifndef UTILS
#define UTILS

#include "Definitions.hpp"

#include <iostream>
#include <string>
#include <vector>

// Logging macro
#if DEBUG
    #define DEBUG_PRINT(str) do { std::cout << str << std::endl; } while( false )
#else
    #define DEBUG_PRINT(str) do { } while ( false )
#endif

// Convert a string representation of IP to a 32-bit number
ID convertIPtoID(const char *IP);

// Extract XML mapping file from filepath
char *extractXMLFile(const char *filepath);

// Convert to little endian if required
UINT lendian(UINT value);

// Convert string to number (Windows only)
#if defined(_WIN32) || defined(WIN32) || defined(WIN64) || defined(_WIN64)
    int stoi(std::string input, int beg, int base);
#endif

// Split string by delimeter
std::vector<std::string> &split(const std::string &s, char delim, 
                                std::vector<std::string> &elems);

std::vector<std::string> split(const std::string &s, char delim);


#endif // UTILS

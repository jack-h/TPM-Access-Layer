#ifndef UTILS
#define UTILS

#include "Definitions.hpp"

#include <iostream>

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

#endif // UTILS

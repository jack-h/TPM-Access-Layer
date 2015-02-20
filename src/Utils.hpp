#ifndef UTILS
#define UTILS

#include "Definitions.hpp"

// Convert a string representation of IP to a 32-bit number
ID convertIPtoID(const char *IP);

// Extract XML mapping file from filepath
char *extractXMLFile(const char *filepath);

#endif // UTILS

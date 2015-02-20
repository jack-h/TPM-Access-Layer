#include "Utils.hpp"

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// Convert string IP address to a 32-bit number
ID convertIPtoID(const char *IP)
{
    struct sockaddr_in sa;
    inet_pton(AF_INET, IP, &(sa.sin_addr));
    return (ID) sa.sin_addr.s_addr;
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

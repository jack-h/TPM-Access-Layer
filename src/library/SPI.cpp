#include "SPI.hpp"
#include "RapidXML.hpp"
#include "Utils.hpp"    

#include <string.h>
#include <stdio.h>

using namespace rapidxml;
using namespace std;

// SPI constructor
SPI::SPI(char *path)
{
    // TODO: Check if filepath exists

    // If so, store locally
    size_t len = strlen(path);
    this -> filepath = (char *) malloc((len + 1) * sizeof(char));
    strcpy(this -> filepath, path);

    // Load file contents
    FILE *f = fopen(path, "r"); 
    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    fseek(f, 0, SEEK_SET);

    char *content = (char *) malloc((fsize + 1) * sizeof(char));
    fread(content, fsize, sizeof(char), f);
    fclose(f);

    content[fsize] = 0;

    // Clear map
    spi_map.clear();

    // Parse memory map
    xml_document<> doc;
    doc.parse<0>(content);

    DEBUG_PRINT("SPI::Constructor. Loading devices from " << path);

    // We are at the root of the XML file, we now need to iterate through
    // the child nodes to access all SPI devices
    xml_node<> *root = doc.first_node();
    for(xml_node<> *deviceNode = root -> first_node(); 
        deviceNode; 
        deviceNode = deviceNode -> next_sibling())
    {           
        // New device detected, get device id
        xml_attribute<> *deviceAttr = deviceNode -> first_attribute("id");  
        if (deviceAttr == 0)
        {
            DEBUG_PRINT("Missing id attribute for device, skipping");
            continue;
        }
        string device_id = deviceAttr -> value(); 

        deviceAttr = deviceNode -> first_attribute("spi_en");
        if (deviceAttr == 0)
        {
            DEBUG_PRINT("Missing spi_en attribute for device " << device_id << ", skipping");
            continue;
        }
        UINT spi_en = atoi(deviceAttr -> value());

        deviceAttr = deviceNode -> first_attribute("spi_sclk");  
        if (deviceAttr == 0)
        {
            DEBUG_PRINT("Missing spi_clk attribute for device " << device_id << ", skipping");
            continue;
        }
        UINT spi_sclk = atoi(deviceAttr -> value());     

        // Add new device to list of SPI devices
        spi_map[device_id] = make_pair(spi_en, spi_sclk);
    }    
}  

// Compose list of SPI devices from SPI list
SPI_DEVICE_INFO* SPI::getSPIList(UINT *num_devices)
{
    DEBUG_PRINT("SPI::getSPIList. Generating SPI device list");

    // Get number of entires
    *num_devices = spi_map.size();

    // If no items in map, return NULL
    if (*num_devices == 0)
    {
        DEBUG_PRINT("SPI::getSPIList. No SPI devices found in list");
        return NULL;
    }

    // Otherwise, create list
    SPI_DEVICE_INFO *list = (SPI_DEVICE_INFO *) malloc(*num_devices * sizeof(SPI_DEVICE_INFO));

    // Global register index;
    unsigned int index = 0;

    // Go through all devices
    std::map<std::string, std::pair<int, int> >::iterator iter;
    for(iter = spi_map.begin(); 
        iter != spi_map.end(); 
        iter++)
    {
        list[index].name     = (iter -> first).c_str();
        list[index].spi_en   = (iter -> second).first;
        list[index].spi_sclk = (iter -> second).second;

        index++;
    }

    return list;
}

// Get information for SPI device
std::pair<int, int> SPI::getSPIInfo(REGISTER device)
{
    // Check if device is in map
    map<string, pair<int, int> >::iterator iter;
    iter = spi_map.find(device);

    // If device not found, return error
    if (iter == spi_map.end())
    {
        DEBUG_PRINT("SPI::getSPIInfo. Device " << device << " not found in SPI map");
        return make_pair(-1, -1);
    }

    // Otherwise, return information    
    return iter -> second;
}

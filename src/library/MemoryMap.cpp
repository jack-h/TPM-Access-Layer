#include "MemoryMap.hpp"
#include "RapidXML.hpp"
#include "Utils.hpp"
#include <iostream>
#include <string.h>
#include <stdio.h>

using namespace rapidxml;
using namespace std;

// MemoryMap constructor
MemoryMap::MemoryMap(char *path)
{
    // Check if filepath exists

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
    memory_map.clear();

    // Parse memory map
    xml_document<> doc;
    doc.parse<0>(content);

    DEBUG_PRINT("MemoryMap::Constructor. Loading memory map from " << path);

    // We are at the root of the XML file, we now need to iterate through
    // the child nodes to access all FPGA and board memory maps
    xml_node<> *root = doc.first_node();
    for(xml_node<> *deviceNode = root -> first_node(); 
        deviceNode; 
        deviceNode = deviceNode -> next_sibling())
    {           
        // New device detected, get device id        
        xml_attribute<> *deviceAttr = deviceNode -> first_attribute("id");  
        string device_id = deviceAttr -> value();  
        DEVICE currDevice;
        REGISTER_TYPE currType;

        if (device_id.compare("FPGA1") == 0)
        {
            currDevice = FPGA_1;
            currType   = FIRMWARE_REGISTER;
            std::cout << "Found FPGA1 device " << device_id << std::endl;
        }
        else if (device_id.compare("FPGA2") == 0)
        {
            currDevice = FPGA_2;
            currType   = FIRMWARE_REGISTER;
            std::cout << "Found FPGA2 device " << device_id << std::endl;
        }
        else
        {
            currDevice = BOARD;
            currType   = BOARD_REGISTER;
            std::cout << "Found Board device " << device_id << std::endl;
        }

        // Create new device entry in register map
        map<string, RegisterInfo *> reg_map;
        memory_map.emplace(currDevice, reg_map);

        // Get base address for device (if any)
        deviceAttr = deviceNode -> first_attribute("address");
        UINT device_address;
        if (deviceAttr == 0)
            device_address = 0x0;
        else
            device_address = stoi(deviceAttr -> value(), 0, 16);       

        // Loop over device node attributes
        for(deviceAttr = deviceNode -> first_attribute();
            deviceAttr;
            deviceAttr = deviceAttr -> next_attribute())
        {
            std::string name = deviceAttr -> name();

            // Extract attribute values
            if (name.compare("id") || name.compare("address"))
                ; // Already processed, skip
            else if (name.compare("module") == 0)
                ; // We need to load an additional file, ignore for now
            else 
                ; // Unsupported attribute, ignore for now
        }

        // Loop over blocks within the device (relate to higher level components
        // in firmware of device groups for the board itself
        for(xml_node<> *compNode = deviceNode -> first_node();
            compNode;
            compNode = compNode -> next_sibling())
        {
            // New component detected, get component ID 
            xml_attribute<> *compAttr = compNode -> first_attribute("id");
            string comp_id = compAttr -> value();

            std::cout << "Found component " << comp_id << std::endl;

            // Check if a base address is specified
            compAttr = compNode -> first_attribute("address");
            UINT comp_address;
            if (compAttr == 0)
                comp_address = 0;
            else
                comp_address = stoi(compAttr -> value(), 0, 16);      

            // NOTE: We are ignoring additional attributes for now...
            
            // Loop through list of registers for current component
            for(xml_node<> *registerNode = compNode -> first_node();
                registerNode;
                registerNode = registerNode -> next_sibling())
            {
                // New register detected, get register ID
                xml_attribute<> *registerAttr = registerNode -> first_attribute("id");
                string reg_id = registerAttr -> value();

                std::cout << "Found register " << reg_id << std::endl;

                // Get register memory mapped address
                registerAttr = registerNode -> first_attribute("address");
                UINT register_address;
                if (registerAttr != 0)
                    register_address = device_address + comp_address + stoi(registerAttr -> value(), 0, 16);
                else
                    register_address = device_address + comp_address;

                // Check whether register contains bitfields
                xml_node<> *bitNode = registerNode -> first_node();

                // If no bitfields define, create entry for current register
                if (bitNode == 0)
                {   
                    // Create RegisterInfo object and set defaults
                    string full_id = comp_id + "." + reg_id;
                    RegisterInfo *reg_info = new RegisterInfo(RegisterInfo(full_id));
                    reg_info -> device = currDevice;
                    reg_info -> type   = currType;
                    reg_info -> address = register_address;

                    // Create new entry in map
                    memory_map[currDevice].emplace(full_id, reg_info);

                    // Loop over device registers and update register info struct
                    for(registerAttr = registerNode -> first_attribute();
                        registerAttr;
                        registerAttr = registerAttr -> next_attribute())
                    {
                        std::string name = registerAttr -> name();

                        // Extract attribute values
                        if (name.compare("id") == 0 || name.compare("address") == 0)
                            ; // Skip, already processed
                        else if (name.compare("mode") == 0)
                        {
                            
                        }
                        else if (name.compare("mask") == 0)
                            // Set register mask
                           reg_info -> bitmask = strtoul(registerAttr -> value(), 0, 16);
                        else if (name.compare("permission") == 0)
                        {       
                            // Set register permission
                            string mode = registerAttr -> value();
                            if (mode.compare("r") == 0)
                                reg_info -> permission = READ;
                            else if (mode.compare("w") == 0)
                                reg_info -> permission = WRITE;
                            else if (mode.compare("rw") == 0)
                                reg_info -> permission = READWRITE;
                            else
                                ; // Unknown permission, ignore for now
                        }
                        else if (name.compare("size") == 0)
                            // Set register size
                            reg_info -> size = stoi(registerAttr -> value(), 0, 10);
                        else if (name.compare("description") == 0)
                        {
                            // Set register description
                            reg_info -> description = registerAttr -> value();
                        }
                        else if (name.compare("tags") == 0)
                        {
                            // Use tag to detect if register is a sensor
                            string tag = registerAttr -> value();
                            if (name.compare("sensor") == 0)
                                reg_info -> type = SENSOR;
                        }
                        else if (name.compare("module") == 0)
                            ; // Ignore for now
                        else 
                            ; // Unsupported attribute, ignore for now
                    }

                }
                // Register contains bitfields, loop over all of them
                else
                {
                    for(bitNode = registerNode -> first_node();
                        bitNode;
                        bitNode = bitNode -> next_sibling())
                    {
                        // New bitfield detected, get ID
                        xml_attribute<> *bitAttr = bitNode -> first_attribute("id");
                        string bit_id = bitAttr -> value();

                        std::cout << "Found bitfield " << comp_id << "." << reg_id << "." << bit_id << std::endl;

                        // Create RegisterInfo object and set defaults
                        string full_id = comp_id + "." + reg_id + "." + bit_id;
                        RegisterInfo *reg_info = new RegisterInfo(RegisterInfo(full_id));
                        reg_info -> device = currDevice;
                        reg_info -> type   = currType;
                        reg_info -> address = register_address;

                        // Create new entry in map
                        memory_map[currDevice].emplace(full_id, reg_info);

                        // Loop over bitfields and update register info struct
                        for(bitAttr = bitNode -> first_attribute();
                            bitAttr;
                            bitAttr = bitAttr -> next_attribute())
                        {
                            std::string name = bitAttr -> name();

                            // Extract attribute values
                            if (name.compare("id") == 0 || name.compare("address") == 0)
                                ; // Skip, already processed
                            else if (name.compare("mode") == 0)
                            {
                                
                            }
                            else if (name.compare("mask") == 0)
                                // Set register mask
                                reg_info -> bitmask = strtoul(bitAttr -> value(), 0, 16);
                            else if (name.compare("permission") == 0)
                            {       
                                // Set register permission
                                string mode = bitAttr -> value();
                                if (mode.compare("r") == 0)
                                    reg_info -> permission = READ;
                                else if (mode.compare("w") == 0)
                                    reg_info -> permission = WRITE;
                                else if (mode.compare("rw") == 0)
                                    reg_info -> permission = READWRITE;
                                else
                                    ; // Unknown permission, ignore for now
                            }
                            else if (name.compare("size") == 0)
                                // Set register size
                                reg_info -> size = stoi(bitAttr -> value(), 0, 10);
                            else if (name.compare("description") == 0)
                            {
                                // Set register description
                                reg_info -> description = bitAttr -> value();
                            }
                            else if (name.compare("tags") == 0)
                            {
                                // Use tag to detect if register is a sensor
                                string tag = bitAttr -> value();
                                if (name.compare("sensor") == 0)
                                    reg_info -> type = SENSOR;
                            }
                            else if (name.compare("module") == 0)
                                ; // Ignore for now
                            else 
                                ; // Unsupported attribute, ignore for now
                        }
                    }
                }
            }
        }
    }
    DEBUG_PRINT("MemoryMap::Constructor. Finished loading memory map from " << path);
}

// Compose register list from memory map
REGISTER_INFO* MemoryMap::getRegisterList(UINT *num_registers)
{
    DEBUG_PRINT("MemoryMap::getRegisterList. Generating register list");

    // Get number of entries
    *num_registers = 0;

    // Iterate over all devices
    map<DEVICE, map<string, RegisterInfo *> >::iterator iter;
    for(iter = memory_map.begin(); 
        iter != memory_map.end(); 
        iter++)
    {
        // Add number of items
        *num_registers += (iter -> second).size();
    }

    // If no items in map, return NULL
    if (*num_registers == 0)
    {
        DEBUG_PRINT("MemoryMap::getRegisterList. No registers found in list");
        return NULL;
    }

    // Otherwise, create list
    REGISTER_INFO *list = (REGISTER_INFO *) malloc(*num_registers * sizeof(REGISTER_INFO));

    // Global register index;
    unsigned int index = 0;

    // Go through all devices
    for(iter = memory_map.begin(); 
        iter != memory_map.end(); 
        iter++)
    {
        // Go through all registers in device
        map<string, RegisterInfo *>::iterator reg_iter;
        for(reg_iter  = (iter -> second).begin();
            reg_iter != (iter -> second).end();
            reg_iter++)
        {
            RegisterInfo *reg = reg_iter -> second;

            // Create register structure 
            list[index].name = (reg -> name).c_str();
            list[index].type = reg -> type;
            list[index].device = reg -> device;
            list[index].permission = reg -> permission;
            list[index].size = reg -> size; 
            list[index].bitmask = reg -> bitmask;
            list[index].description = (reg -> description).c_str();

            index++;
        }
    }

    DEBUG_PRINT("MemoryMap::getRegisterList. Generated register list, " << *num_registers << " registers found");

    return list;
}

// Get register address from map
MemoryMap::RegisterInfo *MemoryMap::getRegisterInfo(DEVICE device, REGISTER reg)
{
    // Check if device is in map
    map<DEVICE, map<string, RegisterInfo *> >::iterator it;
    it = memory_map.find(device);

    // If device not found, return error
    if (it == memory_map.end())
    {
        DEBUG_PRINT("MemoryMap::getRegisterAddress. Device " << device << " not found in memory map");
        return NULL;
    }

    // Check if device contain the register
    map<string, RegisterInfo *> ::iterator reg_it;
    string register_name(reg);
    reg_it = memory_map[device].find(register_name);

    // Register not in map, return error
    if (reg_it == memory_map[device].end())
    {
        DEBUG_PRINT("MemoryMap::getRegisterAddress. Register " << reg << " on device " << device << " not found in memory map");
        return NULL;
    }

    DEBUG_PRINT("TPM::getRegisterValue. Register " << reg << " on device " 
                 << device << " has address 0x" << hex << uppercase 
                 << (reg_it -> second) -> address << dec);

    // Register found, return RegisterInfo reference
    return reg_it -> second;
}

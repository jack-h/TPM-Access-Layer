#include "MemoryMap.hpp"
#include "RapidXML.hpp"
#include "Utils.hpp"
#include <algorithm>
#include <iostream>
#include <string.h>
#include <stdio.h>

using namespace rapidxml;
using namespace std;

// MemoryMap constructor
MemoryMap::MemoryMap(char *path)
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

        // Transform board string to upper case
        transform(device_id.begin(), device_id.end(), device_id.begin(), ::toupper);

        if (device_id.compare("FPGA1") == 0)
        {
            currDevice = FPGA_1;
            currType   = FIRMWARE_REGISTER;
        }
        else if (device_id.compare("FPGA2") == 0)
        {
            currDevice = FPGA_2;
            currType   = FIRMWARE_REGISTER;
        }
        else
        {
            currDevice = BOARD;
            currType   = BOARD_REGISTER;
        }

        // Create new device entry in register map
        map<string, RegisterInfo *> reg_map;
        memory_map[currDevice] = reg_map;

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

            // Check if a base address is specified
            compAttr = compNode -> first_attribute("address");
            UINT comp_address = (compAttr == 0) ? 0 : stoi(compAttr -> value(), 0, 16);

            // Check if description is specified
            compAttr = compNode -> first_attribute("description");
            string desc = (compAttr == 0) ? "" : compAttr -> value();

            // Check if module exists
            compAttr =  compNode -> first_attribute("module");
            string module = (compAttr == 0) ? "" : compAttr -> value();

            // Create entry in memory map
            RegisterInfo *reg_info = new RegisterInfo(RegisterInfo(comp_id));
            reg_info -> device      = currDevice;
            reg_info -> type        = COMPONENT;
            reg_info -> address     = comp_address;
            reg_info -> description = desc;        
            reg_info -> module      = module;
            memory_map[currDevice][comp_id]  = reg_info;

            // NOTE: We are ignoring additional attributes for now...
            
            // Loop through list of registers for current component
            for(xml_node<> *registerNode = compNode -> first_node();
                registerNode;
                registerNode = registerNode -> next_sibling())
            {
                // New register detected, get register ID
                xml_attribute<> *registerAttr = registerNode -> first_attribute("id");
                string reg_id = registerAttr -> value();

                // Get register memory mapped address
                registerAttr = registerNode -> first_attribute("address");
                UINT register_address;
                if (registerAttr != 0)
                    register_address = device_address + comp_address + stoi(registerAttr -> value(), 0, 16);
                else
                    register_address = device_address + comp_address;

                // Create RegisterInfo object and set defaults
                string full_id = comp_id + "." + reg_id;
                reg_info = new RegisterInfo(RegisterInfo(full_id));
                reg_info -> device = currDevice;
                reg_info -> type   = currType;
                reg_info -> address = register_address;

                // Create new entry in map
                memory_map[currDevice][full_id] = reg_info;

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
                    {
                        // Set register mask
                        reg_info -> bitmask = strtoul(registerAttr -> value(), 0, 16);

                        // Get number of bits and bitshift
                        UINT shift = 0, bits = 0;
                        bool found = false;
                        for(unsigned i = 0; i <= sizeof(UINT) * 8 - 1; i++)
                        {
                            if (((reg_info -> bitmask >> i) & 0x00000001) == 1)
                            {
                                bits++;
                                if (!found) { found = true; shift = i; }
                            }
                        }                        

                        reg_info -> shift = shift;
                        reg_info -> bits  = bits;
                    }   
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
                        reg_info -> module = registerAttr -> value();
                    else 
                        ; // Unsupported attribute, ignore for now
                }

                // Check whether register contains bitfields
                if (registerNode -> first_node())
                {
                    for(xml_node<> *bitNode = registerNode -> first_node();
                        bitNode;
                        bitNode = bitNode -> next_sibling())
                    {
                        // New bitfield detected, get ID
                        xml_attribute<> *bitAttr = bitNode -> first_attribute("id");
                        string bit_id = bitAttr -> value();

                        // Create RegisterInfo object and set defaults
                        string full_id = comp_id + "." + reg_id + "." + bit_id;
                        reg_info = new RegisterInfo(RegisterInfo(full_id));
                        reg_info -> device = currDevice;
                        reg_info -> type   = currType;
                        reg_info -> address = register_address;

                        // Create new entry in map
                        memory_map[currDevice][full_id] = reg_info;

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
                            {
                                // Set register mask
                                reg_info -> bitmask = strtoul(bitAttr -> value(), 0, 16);

                                // Get number of bits and bitshift
                                UINT shift = 0, bits = 0;
                                bool found = false;
                                for(unsigned i = 0; i <= sizeof(UINT) * 8 - 1; i++)
                                {
                                    if (((reg_info -> bitmask >> i) & 0x00000001) == 1)
                                    {
                                        bits++;
                                        if (!found) { found = true; shift = i; }
                                    }
                                }                        

                                reg_info -> shift = shift;
                                reg_info -> bits  = bits;
                            }
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
            list[index].address = reg -> address;
            list[index].type = reg -> type;
            list[index].device = reg -> device;
            list[index].permission = reg -> permission;
            list[index].size = reg -> size; 
            list[index].bitmask = reg -> bitmask;
            list[index].bits = reg -> bits;
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

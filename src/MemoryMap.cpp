#include "MemoryMap.hpp"
#include "RapidXML.hpp"
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

    // Parse memory map
    xml_document<> doc;
    doc.parse<0>(content);

    // We are at the root of the XML file, we now need to iterate through
    // the child nodes to access all FPGA and board memory maps
    xml_node<> *root = doc.first_node();
    for(xml_node<> *groupNode = root -> first_node(); 
        groupNode; 
        groupNode = groupNode -> next_sibling())
    {           
        // Get board or FPGA ID and base address
        xml_attribute<> *groupAttr = groupNode -> first_attribute();

        printf("Found map for: %s\n", groupAttr -> value());         

        // Loop over group node attributes
        for(xml_attribute<> *attribute = groupNode -> first_attribute();
            attribute;
            attribute = attribute -> next_attribute())
        {
            std::string name = attribute -> name();

            // Extract attribute values
            if (name.compare("id") == 0)
                printf("   Attribute id is %s\n", attribute -> value());
            else if (name.compare("address") == 0)
                printf("   Attribute address is %s\n", attribute -> value());
            else if (name.compare("module") == 0)
                 printf("   Attribute module is %s\n", attribute -> value()); // Ignore for now
            else 
                ; // Unsupported attribute, ignore for now
        }

        // Now we'll loop through the register names in each individual map
        for(xml_node<> *registerNode = groupNode -> first_node();
            registerNode;
            registerNode = registerNode -> next_sibling())
        {
            printf("\tFound register\n");

            // Loop over register node attributes
            for(xml_attribute<> *attribute = registerNode -> first_attribute();
                attribute;
                attribute = attribute -> next_attribute())
            {
                std::string name = attribute -> name();

                // Extract attribute values
                if (name.compare("id") == 0)
                    printf("\t  Attribute id is %s\n", attribute -> value());
                else if (name.compare("address") == 0)
                    printf("\t  Attribute address is %s\n", attribute -> value());
                else if (name.compare("mode") == 0)
                    printf("\t  Attribute mode is %s\n", attribute -> value());
                else if (name.compare("permission") == 0)
                    printf("\t  Attribute permission is %s\n", attribute -> value());
                else if (name.compare("size") == 0)
                    printf("\t  Attribute size is %s\n", attribute -> value());
                else if (name.compare("description") == 0)
                    printf("\t  Attribute description is %s\n", attribute -> value());
                else if (name.compare("tags") == 0)
                    printf("\t  Attribute tags is %s\n", attribute -> value());
                else if (name.compare("module") == 0)
                    ; // Ignore for now
                else 
                    ; // Unsupported attribute, ignore for now
            }

            // Check if register has any child nodes, if so then this register
            // is a bit register
        }
    }
}

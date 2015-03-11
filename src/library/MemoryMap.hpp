#ifndef MEMORY_MAP
#define MEMORY_MAP

#include "Definitions.hpp"
#include <map>

using namespace std;

// Class representing a memory map
class MemoryMap
{
    // Make TPM a friend class so that it can access private methods 
    // within the memory map (to access RegisterInfo items)
    friend class TPM;

    public:
        // MemoryMap constructor accepting filepath
        MemoryMap(char *filepath);

    private:
        // Class to hold register information
        class RegisterInfo
        {
            public:
                // Class constructor
                RegisterInfo(string name)
                {
                    // Assign name
                    this -> name = name;

                    // Assign default values
                    this -> permission  = READ;
                    this -> size        = 1;
                    this -> description = "";
                    this -> address     = 0x0;
                    this -> bitmask     = 0xFFFFFFFF;
                }

            public:
                string         name;         // String representation of register
                REGISTER_TYPE  type;         // Sensor, board-register or firmware-register
                DEVICE         device;       // Set of FPGAs (if any) to which this is applicable
                PERMISSION     permission;   // Define register access type
                unsigned int   size;         // Memory size in bytes 
                string         description;  // Register string description
                UINT           address;      // Memory-mapped address 
                UINT           bitmask;      // Register bitmask
        };

    public:
        // Get register list
        REGISTER_INFO* getRegisterList(UINT *num_registers);

        // Get register address
        int getRegisterAddress(DEVICE device, REGISTER reg);

    private:
        // Get bitmask for register
        UINT getRegisterBitMask(DEVICE device, REGISTER reg);

    private:
        char        *filepath;  // Store filepath to memory map XML file
        map<DEVICE, map<string, RegisterInfo *> >   memory_map;   // Full memory map of devices
};


#endif  // MEMORY_MAP

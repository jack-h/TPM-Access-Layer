#ifndef MEMORY_MAP
#define MEMORY_MAP

#include "Definitions.hpp"
#include <string>
#include <map>

using namespace std;

// Class representing a memory map
class MemoryMap
{
    // Make TPM a friend class so that it can access private methods 
    // within the memory map (to access RegisterInfo items)
    friend class TPM;
    friend class UniBoard;

    public:
        // MemoryMap constructor accepting filepath
        MemoryMap(char *filepath);

        // MemoryMap constructor which is initialised empty
        MemoryMap();

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
                    this -> module      = "";
                    this -> permission  = READ;
                    this -> size        = 1;
                    this -> description = "";
                    this -> address     = 0x0;
                    this -> bitmask     = 0xFFFFFFFF;
                    this -> bits        = 32;
                    this -> shift       = 0;
                }

            public:
                string         name;         // String representation of register
                string         module;       // Path of any additional modules
                REGISTER_TYPE  type;         // Sensor, board-register or firmware-register
                DEVICE         device;       // Set of FPGAs (if any) to which this is applicable
                PERMISSION     permission;   // Define register access type
                unsigned int   size;         // Memory size in bytes 
                string         description;  // Register string description
                UINT           address;      // Memory-mapped address 
                UINT           bitmask;      // Register bitmask
                UINT           bits;         // Number of bits
                UINT           shift;        // Bit shift
        };

    public:
        // Get register list
        REGISTER_INFO* getRegisterList(UINT *num_registers);

    private:
        // Get register information
        RegisterInfo *getRegisterInfo(DEVICE device, REGISTER reg);

        // Add a new register entry
        RETURN addRegisterEntry(DEVICE device, REGISTER reg, UINT address, UINT offset);

        // Remove a register entry
        RETURN removeRegisterEntry(DEVICE device, REGISTER reg);

        // Reset device map
        RETURN resetDevice(DEVICE device);

    private:
        char        *filepath;                                    // Store filepath to memory map XML file
        map<DEVICE, map<string, RegisterInfo *> >   memory_map;   // Full memory map of devices

        
};


#endif  // MEMORY_MAP

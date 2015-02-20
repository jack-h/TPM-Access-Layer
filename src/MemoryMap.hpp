#ifndef MEMORY_MAP
#define MEMORY_MAP

#include "Definitions.hpp"
#include <map>

using namespace std;

// Class representing a memory map
class MemoryMap
{
    public:
        // MemoryMap constructor accepting filepath
        MemoryMap(char *filepath);

    private:
        char  *filepath;  // Store filepath to memory map XML file
        map<string, map<string, REGISTER_INFO> > memory_map; 
};


#endif  // MEMORY_MAP

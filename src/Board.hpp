#ifndef BOARD
#define BOARD_ERROR

#include "Definitions.hpp"

#include <string.h>

using namespace std;

// Class representation of a digital board
// This can eventually be sub-classed to add functionality
// specific to a particular board
class Board
{
    public:
        Board(string ip, unsigned short port);     

    private:

        // ---------- Priavte class functions --------

        // Create socket
        ERROR connect();
    
        // Clear everything and remove connection
        ERROR disconnect();

        // ---------- Private class members ---------- 
        unsigned int    id;   // Board identifier
        string          ip;   // Board IP address
        unsigned short  port  // Port to communicate with board

        int             socket;  // Representation of internal socket to communicate with board
};

#endif // BOARD

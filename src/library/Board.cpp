#include "Board.hpp"

// Board constructor
Board::Board(const char *ip, unsigned short port)
{
    // Set default number of FPGAs
    this -> num_fpgas = 1;
    this -> spi_devices = NULL;
    this -> memory_map  = NULL;
    this -> protocol    = NULL;
}


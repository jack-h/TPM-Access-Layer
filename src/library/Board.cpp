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

// Get values for all registers (called after getRegisterList)
void Board::initialiseRegisterValues(REGISTER_INFO *regInfo, int num_registers)
{
	// For all registers
	for(int i = 0; i < num_registers; i++)
	{
		REGISTER_INFO reg = regInfo[i];
		VALUES values = this -> readRegister(reg.device, reg.name);
		if (values.error == SUCCESS)
			reg.value = values.values[0];
		else
			reg.value = 0;
	}
	
	// All done
}



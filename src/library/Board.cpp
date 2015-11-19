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
		VALUES values = this -> readRegister(regInfo[i].device, regInfo[i].name);
		if (values.error == SUCCESS) {
			regInfo[i].value = values.values[0];

			if (values.values[0] != 0)
			{
				std::cout << "Read value " << values.values[0] << " from register " << regInfo[i].name << std::endl;
			}
		}
		else
			regInfo[i].value = 0;
	}
	
	// All done
}
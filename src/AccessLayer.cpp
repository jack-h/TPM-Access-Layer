// Implementation of the TPM Access Layer API
// This is the main entry point, all high level commands have to pass
// through this file
// All global structure are stored here as well (these are not defined in the header file such that 
// clients do not have access to them -- are 'private')


// Set up internal structures to be able to communicate with a processing board
// Arguments:
ID connect(char *IP, int port)
{    }

// Clear up internal network structures for board in question
ERROR disconnect(ID id)
{    }

// Rest board. Note that return from this function is not determined, due to
// the board being reset
ERROR resetBoard(ID id)
{    }

// Get board status
STATUS getStatus(ID id)
{    }

// Get list of registers
REGISTER_INFO* getRegisterList(ID id)
{    }

// Get a register's value
VALUE getRegisterValue(ID id, FPGA fpga, REGISTER reg)
{    }

// Set a register's value
ERROR setRegisterValue(ID id, FPGA fpga, REGISTER reg, int value)
{    }

// Get a register's value
VALUE* getRegisterValues(ID id, FPGA fpga, REGISTER reg, int N)
{    }

// Set a register's value
ERROR setRegisterValues(ID id, FPGA fpga, REGISTER reg, int N, int *values)
{    }

// [Optional] Set a periodic register
ERROR setPeriodicRegister(ID id, FPGA fpga, REGISTER reg, int period, CALLBACK callback)
{    }

// [Optional] Stop periodic register
ERROR stopPeriodicRegister(ID id, FPGA fpga, REGISTER reg)
{    }

// [Optional] Set a periodic register
ERROR setConditionalRegister(ID id, FPGA fpga, REGISTER reg, int period, CALLBACK callback)
{    }

// [Optional] Stop periodic register
ERROR stopConditionalRegister(ID id, FPGA fpga, REGISTER reg)
{    }

// Load firmware to FPGA. This function return immediately. The status of the
// board can be monitored through the getStatus call
ERROR loadFirmware(ID id, FPGA fpga, char* bistream)
{    }

// Same as loadFirmware, however return only after the bitstream is loaded or
// an error occurs
ERROR loadFirmwareBlocking(ID id, FPGA fpga, char* bistream)
{    }

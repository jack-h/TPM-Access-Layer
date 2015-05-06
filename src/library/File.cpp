#include "File.hpp"
#include "Utils.hpp"

#include <stdio.h>

// Create file
RETURN FileProtocol::createConnection(const char *IP, int port)
{
	// Try to open file for writing
	if ((this -> fp = fopen(IP, "w")) == NULL)
	{
		DEBUG_PRINT("File::createConnection. Failed to open file for writing");
		return FAILURE;
	}
	
	return SUCCESS;
}

// Close file
RETURN FileProtocol::closeConnection()
{	
	// Try to close file
	if (fclose(this -> fp) < 0)
	{
		DEBUG_PRINT("File::closeConnection. Failed to close file");
		return FAILURE;
	}

	return SUCCESS;
}

// Call read register
VALUES FileProtocol::readRegister(UINT address, UINT n, UINT offset)
{
	// Add line to file
	fprintf(this -> fp, "READ. Address: %#010x, N = %d, offset = %d\n", address, n, offset);
	fflush(this -> fp);
	return {NULL, FAILURE};
}

// Call write register
RETURN FileProtocol::writeRegister(UINT address, UINT *values, UINT n, UINT offset)
{
	// Add line to file
	fprintf(this -> fp, "WRITE. Address: %#010x, N = %d, offset = %d, values =(", address, n, offset);
	for (unsigned i = 0; i < n - 1; i++)
		fprintf(this -> fp, "%d, ", values[i]);
	fprintf(this -> fp, "%d)\n", values[n-1]);
	fflush(this -> fp);
	
	return FAILURE;
}

// Call list firmware
FIRMWARE FileProtocol::listFirmware(UINT *num_firmware)
{
	return NULL; // Not implementable for a file
}
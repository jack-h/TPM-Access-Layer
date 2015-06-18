#ifndef TPM_ACCESS_LAYER
#define TPM_ACCESS_LAYER

/* This header file lists the functions which will be provided by the Low-Level 
   Access Layer, acting as a bridge between TPMs and LMC. This layer will 
   implement the client side of the interface control protocol and internally 
   make use of firmware memory maps to translate register names to memory 
   addresses. The primary aim of the layer is to mask protocol and firmware 
   specific implementation details and provide a uniform access to LMC and any 
   other applications which want to monitor and control TPMs. 

   NOTE: This is for design purposes only. Data types and some parameters might 
         change.
*/

#include "Definitions.hpp"

// Callback function definition for asynchronous updates
// typedef void (* CALLBACK)(ID, REGISTER, VALUES);

// ======================= CONNECTION RELATED FUNCTIONS =======================

// Set up internal structures to be able to communicate with a processing board
// Arguments:
//   IP    String representation of the board's IP address
//   port  Port number to use
// Returns:
//   A board ID in case of success, -1 on failure      
extern "C" ID connectBoard(BOARD_MAKE board, const char* IP, unsigned short port);

// Clear up internal network structures for board in question
// Arguments:
//   id    Board ID
// Returns:
//   RETURN
extern "C" RETURN disconnectBoard(ID id);

// ========================= BOARD RELATED FUNCTIONS =========================

// Rest board. Note that return from this function is not determined, due to
// the board being reset
// Arguments:
//   id    Board ID
// Returns:
//   RETURN
extern "C" RETURN resetBoard(ID id);

// Get board status
// Arguments:
//   id    Board ID
// Returns:
//   Board status
extern "C" STATUS getStatus(ID id);

// ========================= REGISTER RELATED FUNCTIONS =========================

// Get list of registers
// Arguments:
//   id    Board ID
// Returns:
//   Array of REGISTER_INFO
extern "C" REGISTER_INFO* getRegisterList(ID id, UINT *num_registers);

// Get a register's value
// Arguments:
//   id      Board ID
//   device  Specify to which DEVICE (if any) this applies
//   reg     Register to query
//   n       Number of words to read
//   offset  Address offset to read from
// Returns:
//    VALUE 
extern "C" VALUES readRegister(ID id, DEVICE device, REGISTER reg, UINT n = 1, UINT offset = 0);

// Arguments:
//   id      Board ID
//   device  Specify to which DEVICE (if any) this applies
//   reg     Register to write to
//   values  32-bit value to write to register
//   n       Number of words to write
//   offset  Address offset to write from
// Returns:
//    VALUE

extern "C" RETURN writeRegister(ID id, DEVICE device, REGISTER reg, UINT *values, UINT n = 1, UINT offset = 0);

// Get a register's value
// Arguments:
//   id      Board ID
//   device  Specify to which DEVICE (if any) this applies
//   reg     Register to query
//   n       Number of words to read
// Returns:
//    VALUE
extern "C" VALUES readFifoRegister(ID id, DEVICE device, REGISTER reg, UINT n = 1);

// Arguments:
//   id      Board ID
//   device    Specify to which DEVICE (if any) this applies
//   reg     Register to write to
//   value   32-bit value to write to register
//   n       Number of words to write
// Returns:
//    VALUE
extern "C" RETURN writeFifoRegister(ID id, DEVICE device, REGISTER reg, UINT *values, UINT n = 1);

// Get address content
// Arguments:
//   id       Board ID
//   address  Address to read from
//   n        Number of values to read
// Returns:
//    VALUE 
extern "C" VALUES readAddress(ID id, DEVICE device, UINT address, UINT n = 1);

// Arguments:
//   id      Board ID
//   reg     Address to write to
//   n       Number of value to write
//   values  32-bit values to write to address
// Returns:
//    VALUE 
extern "C" RETURN writeAddress(ID id, DEVICE device, UINT address, UINT *values, UINT n = 1);

// [Optional] Set a periodic register
// Arguments:
//   id       Board ID
//   device   Specify to which DEVICE (if any) this applies
//   reg      Register to query
//   period   Register update period in seconds
//   callback Callback function to send periodic updates
// Returns:
//   RETURN
// extern "C" RETURN setPeriodicRegister(ID id, DEVICE device, REGISTER reg, int period, CALLBACK callback);

// [Optional] Stop periodic register
// Arguments:
//   id       Board ID
//   device   Specify to which DEVICE (if any) this applies
//   reg      Register to stop querying
// Returns:
//   RETURN
// extern "C" RETURN stopPeriodicRegister(ID id, DEVICE device, REGISTER reg);

// [Optional] Set a periodic register
// Arguments:
//   id       Board ID
//   device   Specify to which DEVICE (if any) this applies
//   reg      Register to query
//   period   Periodicity of checks in seconds
//   low      Lowest acceptable register value
//   high     Highest acceptable register value
//   callback Callback function to send periodic updates
// Returns:
//   RETURN
// extern "C" RETURN setConditionalRegister(ID id, DEVICE device, REGISTER reg, int period, CALLBACK callback);

// [Optional] Stop periodic register
// Arguments:
//   id       Board ID
//   device   Specify to which DEVICE (if any) this applies
//   reg      Register to stop querying
// Returns:
//   RETURN
// extern "C" RETURN stopConditionalRegister(ID id, DEVICE device, REGISTER reg);

// ====================== SPI DEVICES RELATED FUNCTIONS =======================

// Get list of SPI devices
// Arguments:
//   id    Board ID
// Returns:
//   Array of REGISTER_INFO
extern "C" SPI_DEVICE_INFO* getDeviceList(ID id, UINT *num_devices);

// Get a device's value
// Arguments:
//   id       Board ID
//   device   Device name
//   address  Address to read value from
// Returns:
//    VALUE 
extern "C" VALUES readDevice(ID id, REGISTER device, UINT address);

// Set a device's value
// Arguments:
//   id      Board ID
//   device  Device name
//   address Address to write value to 
//   value   32-bit value to write to device
// Returns:
//    VALUE 
extern "C" RETURN writeDevice(ID id, REGISTER device, UINT address, UINT value);

// ======================== FIRMWARE RELATED FUNCTIONS ========================

// NOTE: Currently it is assumed that the memory map will be located in the same
//       directory as the bitstream, with the same name (except the extension, which
//       will be .XML. It is also assumed that the file will contain the mapping for
//       the CPLD, FPGA1 and FPGA2, and that no additional module files are required

// Get list of firmware preset on the board
// Arguments:
//    id            Board ID
//    device        Sepicfy to which DEVICE this applies
//    num_firmware  Return number of firmware on board
extern "C" FIRMWARE getFirmware(ID id, DEVICE device, UINT *num_firmware);

// Load firmware to DEVICE. This function return immediately. The status of the
// board can be monitored through the getStatus call
// Arguments:
//   id       Board ID
//   device   Specify to which DEVICE (if any) this applies
//   bistream array containing data bitfile
// Returns:
//   RETURN
extern "C" RETURN loadFirmware(ID id, DEVICE device, const char* bitstream);

// Same as loadFirmware, however return only after the bitstream is loaded or
// an error occurs
extern "C" RETURN loadFirmwareBlocking(ID id, DEVICE device, const char* bitstream);

// Request RF data from the running firmware. This is still TBD


// ============================ HELPER FUNCTIONS ============================

// Free up memory
extern "C" void freeMemory(void *ptr);

#endif  // TPM_ACCESS_LAYER



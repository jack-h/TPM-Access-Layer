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

// _TODO: Define data tap mechanism
//        Check whether bit-wise register access will be permitted, and how

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
extern "C" ID connectBoard(const char* IP, unsigned short port);

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
// Returns:
//    VALUE 
extern "C" VALUES readRegister(ID id, DEVICE device, REGISTER reg, UINT n, UINT offset = 0);

// Arguments:
//   id      Board ID
//   device    Specify to which DEVICE (if any) this applies
//   reg     Register to write to
//   value   32-bit value to write to register
// Returns:
//    VALUE 
extern "C" RETURN writeRegister(ID id, DEVICE device, REGISTER reg, UINT n, UINT *values, UINT offset = 0);

// Get address content
// Arguments:
//   id       Board ID
//   address  Address to read from
//   n        Number of values to read
// Returns:
//    VALUE 
extern "C" VALUES readAddress(ID id, UINT address, UINT n);

// Arguments:
//   id      Board ID
//   reg     Address to write to
//   n       Number of value to write
//   values  32-bit values to write to address
// Returns:
//    VALUE 
extern "C" RETURN writeAddress(ID id, UINT address, UINT n, UINT *values);

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
//   high     Highst acceptable register value
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

// ======================== FIRMWARE RELATED FUNCTIONS ========================

// NOTE: Currently it is assumed that the memory map will be located in the same
//       directory as the bitstream, with the same name (except the extention, which
//       will be .XML. It is also assumed that the file will contain the mapping for
//       the CPLD, FPGA1 and FPGA2, and that no additional module files are required

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



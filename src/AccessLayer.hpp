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
typedef void (* CALLBACK)(ID, REGISTER, VALUE);

// ======================= CONNECTION RELATED FUNCTIONS =======================

// Set up internal structures to be able to communicate with a processing board
// Arguments:
//   IP    String representation of the board's IP address
//   port  Port number to use
// Returns:
//   A board ID in case of success, -1 on failure      
extern "C" ID connectBoard(char* IP, unsigned short port);

// Clear up internal network structures for board in question
// Arguments:
//   id    Board ID
// Returns:
//   ERROR
extern "C" ERROR disconnectBoard(ID id);

// ========================= BOARD RELATED FUNCTIONS =========================

// Rest board. Note that return from this function is not determined, due to
// the board being reset
// Arguments:
//   id    Board ID
// Returns:
//   ERROR
extern "C" ERROR resetBoard(ID id);

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
extern "C" REGISTER_INFO* getRegisterList(ID id, unsigned int *num_registers);

// Get a register's value
// Arguments:
//   id      Board ID
//   device  Specify to which DEVICE (if any) this applies
//   reg     Register to query
// Returns:
//    VALUE 
extern "C" VALUE getRegisterValue(ID id, DEVICE device, REGISTER reg);

// Set a register's value
// Arguments:
//   id      Board ID
//   device    Specify to which DEVICE (if any) this applies
//   reg     Register to write to
//   value   32-bit value to write to register
// Returns:
//    VALUE 
extern "C" ERROR setRegisterValue(ID id, DEVICE device, REGISTER reg, uint32_t value);

// Get a register's value
// Arguments:
//   id      Board ID
//   device  Specify to which DEVICE (if any) this applies
//   reg     Register to query
//   N       Number of values to read
// Returns:
//    VALUE 
extern "C" VALUE* getRegisterValues(ID id, DEVICE device, REGISTER reg, int N);

// Set a register's value
// Arguments:
//   id      Board ID
//   device  Specify to which DEVICE (if any) this applies
//   reg     Register to write to
//   N       Number of 32-bit values to write
//   values  Array of 32-bit values to write to register
// Returns:
//    VALUE 
extern "C" ERROR setRegisterValues(ID id, DEVICE device, REGISTER reg, int N, uint32_t *values);

// [Optional] Set a periodic register
// Arguments:
//   id       Board ID
//   device   Specify to which DEVICE (if any) this applies
//   reg      Register to query
//   period   Register update period in seconds
//   callback Callback function to send periodic updates
// Returns:
//   ERROR
extern "C" ERROR setPeriodicRegister(ID id, DEVICE device, REGISTER reg, int period, CALLBACK callback);

// [Optional] Stop periodic register
// Arguments:
//   id       Board ID
//   device   Specify to which DEVICE (if any) this applies
//   reg      Register to stop querying
// Returns:
//   ERROR
extern "C" ERROR stopPeriodicRegister(ID id, DEVICE device, REGISTER reg);

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
//   ERROR
extern "C" ERROR setConditionalRegister(ID id, DEVICE device, REGISTER reg, int period, CALLBACK callback);

// [Optional] Stop periodic register
// Arguments:
//   id       Board ID
//   device   Specify to which DEVICE (if any) this applies
//   reg      Register to stop querying
// Returns:
//   ERROR
extern "C" ERROR stopConditionalRegister(ID id, DEVICE device, REGISTER reg);

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
//   ERROR
extern "C" ERROR loadFirmware(ID id, DEVICE device, char* bitstream);

// Same as loadFirmware, however return only after the bitstream is loaded or
// an error occurs
extern "C" ERROR loadFirmwareBlocking(ID id, DEVICE device, char* bitstream);

// Request RF data from the running firmware. This is still TBD

#endif  // TPM_ACCESS_LAYER

#ifndef DEFINITIONS
#define DEFINITIONS

#include <stdint.h>

// Enable or disable debugging
#define DEBUG

// ========================== DATA TYPE DEFINITIONS ==========================

// Representation of board ID
typedef unsigned int ID;

// Representation of register name
typedef const char* REGISTER;

// Device types
typedef enum { BOARD = 1, FPGA_1 = 2, FPGA_2 = 4 } DEVICE;

// Return type for most of the function calls, specifying whether the call
// succeeded or failed
typedef enum {SUCCESS = 0, FAILURE = -1, NOT_IMPLEMENTED = -2} ERROR;

// Define possible board statuses
typedef enum { OK,                 // Board is functioning properly
               LOADING_FIRMWARE,   // Firmware being laoded on an FPGA
               CONFIG_ERROR,       // ### Error configuring firmware
               BOARD_ERROR,        // Board health check failed
               NOT_CONNECTED,      // Connect wasn't called 
               NETWORK_ERROR }     // Board cannot be reached
STATUS;

// At least three types of registers can be defined (a sensor, a board/
// peripheral register and a firmware register).
typedef enum {SENSOR, BOARD_REGISTER, FIRMWARE_REGISTER} REGISTER_TYPE;

// ### Register access permissions 
typedef enum {READ, WRITE, READWRITE} PERMISSION;

// Encapsulate a register or sensor value. This structure is require to avoid
// assigning a particular value as the error value, or avoid using reference
// varaibles in the parameter list. This structure can be extended if 
// additional functionality is required
typedef struct VALUE {
    uint32_t  value;     // Sensor or register value
    ERROR     error;     // If error is FAILURE, then value is invalid
} VALUE;

// Encapsulate register information
typedef struct REGISTER_INFO {
    REGISTER      name;  // String representation of register
    REGISTER_TYPE type;  // Sensor, board-register or firmware-register
    DEVICE        device;  // Set of FPGAs (if any) to which this is applicable
    PERMISSION    permission;   // ### Define register access type
    unsigned int  size;  // ### Memory size in bytes 
    const char    *description; // ### Register string description
} REGISTER_INFO;

#endif // DEFINITIONS

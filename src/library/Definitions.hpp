#ifndef DEFINITIONS
#define DEFINITIONS

#include <stdint.h>

// Enable or disable debugging
#define DEBUG 1

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
typedef enum { OK                =  0,  // Board is functioning properly
               LOADING_FIRMWARE  = -1,  // Firmware being laoded on an FPGA
               CONFIG_ERROR      = -2,  // ### Error configuring firmware
               BOARD_ERROR       = -3,  // Board health check failed
               NOT_CONNECTED     = -4,  // Connect wasn't called 
               NETWORK_ERROR     = -5}  // Board cannot be reached
STATUS;

// At least three types of registers can be defined (a sensor, a board/
// peripheral register and a firmware register).
typedef enum {SENSOR = 1, BOARD_REGISTER = 2, FIRMWARE_REGISTER = 3} REGISTER_TYPE;

// ### Register access permissions 
typedef enum {READ = 1, WRITE = 2, READWRITE = 3} PERMISSION;

// Encapsulate a register or sensor value. This structure is require to avoid
// assigning a particular value as the error value, or avoid using reference
// varaibles in the parameter list. This structure can be extended if 
// additional functionality is required
typedef struct VALUES {
    uint32_t  *values;     // Sensor or register value
    ERROR     error;     // If error is FAILURE, then value is invalid
} VALUES;

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

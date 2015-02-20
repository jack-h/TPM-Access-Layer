#ifndef DEFINITIONS
#define DEFINITIONS

// ========================== DATA TYPE DEFINITIONS ==========================

// Flags refererring to particular FPGAs
#define ALL_FPGAS  0xFF  // Refer to all FPGAs
#define NO_FPGAS   0x00  // Not FPGA-related (board or peripheral)
#define FPGA_1     0x01  // FPGA 1
#define FPGA_2     0x02  // FPGA 2

// Representation of board ID
typedef int ID;

// Representation of register name
typedef char* REGISTER;

// Board can contain one or more FPGAs on them, each running different firmwamre.
// A register might therefore reside on a number of FPGAs
typedef int FPGA;

// Return type for most of the function calls, specifying whether the call
// succeeded or failed
typedef enum {SUCCESS, FAILURE, NOT_IMPLEMENTED} ERROR;

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
    int   value;     // Sensor or register value
    ERROR error;     // If error is FAILURE, then value is invalid
} VALUE;

// Encapsulate register information
typedef struct REGISTER_INFO {
    REGISTER      name;  // String representation of register
    REGISTER_TYPE type;  // Sensor, board-register or firmware-register
    FPGA          fpga;  // Set of FPGAs (if any) to which this is applicable
    PERMISSION    permission;   // ### Define register access type
    unsigned int  size;  // ### Memory size in bytes 
    char          *description; // ### Register string description
} REGISTER_INFO;

#endif // DEFINITIONS

#ifndef DEFINITIONS
#define DEFINITIONS

#include <stdint.h>

// Enable or disable debugging
#define DEBUG 1
#define TEST  0

// ========================== DATA TYPE DEFINITIONS ==========================

// Representation of board ID
typedef int ID;

// Representation of register name
typedef const char* REGISTER;

// Representation of basic datatype
typedef uint32_t UINT;

// Represent list of firmware
typedef char** FIRMWARE;

// Device types
typedef enum { FPGA_1 = 1, FPGA_2 = 2, FPGA_3 = 4, FPGA_4 = 8,
               FPGA_5 = 16, FPGA_6 = 32, FPGA_7 = 64, FPGA_8 = 128,
               BOARD = 65536 } DEVICE;

// Implemented board types
typedef enum { TPM_BOARD       = 1, 
               ROACH_BOARD     = 2, 
               ROACH2_BOARD    = 3, 
               UNIBOARD_BOARD  = 4,
               UNIBOARD2_BOARD = 5 } BOARD_MAKE;

// Return type for most of the function calls, specifying whether the call
// succeeded or failed
typedef enum {SUCCESS = 0, FAILURE = -1, NOT_IMPLEMENTED = -2} RETURN;

// Define possible board statuses
typedef enum { OK                =  0,  // Board is functioning properly
               LOADING_FIRMWARE  = -1,  // Firmware being loaded on an FPGA
               CONFIG_ERROR      = -2,  // Error configuring firmware
               BOARD_ERROR       = -3,  // Board health check failed
               NOT_CONNECTED     = -4,  // Connect wasn't called 
               NETWORK_ERROR     = -5}  // Board cannot be reached
STATUS;

// Enumeration of register types
typedef enum {SENSOR            = 1, 
              BOARD_REGISTER    = 2, 
              FIRMWARE_REGISTER = 3, 
              SPI_DEVICE        = 4,
              COMPONENT         = 5,
              FIFO_REGISTER     = 6} REGISTER_TYPE;

// ### Register access permissions 
typedef enum {READ = 1, WRITE = 2, READWRITE = 3} PERMISSION;

// Encapsulate a register or sensor value. This structure is require to avoid
// assigning a particular value as the error value, or avoid using reference
// variables in the parameter list. This structure can be extended if
// additional functionality is required
typedef struct VALUES {
    UINT      *values;     // Sensor or register value
    RETURN    error;       // If error is FAILURE, then value is invalid
} VALUES;

// Encapsulate register information
typedef struct REGISTER_INFO {
    REGISTER      name;         // String representation of register
    UINT          address;      // Register memory-mapped address
    REGISTER_TYPE type;         // Sensor, board-register or firmware-register
    DEVICE        device;       // Set of FPGAs (if any) to which this is applicable
    PERMISSION    permission;   // Define register access type
    UINT          bitmask;      // Register bitmask
    UINT          bits;         // Number of bits
	UINT          value;        // Initial value 
    unsigned int  size;         // Memory size in bytes 
    const char    *description; // Register string description
} REGISTER_INFO;

// Encapsulate SPI device information 
typedef struct SPI_DEVICE_INFO {
    REGISTER      name;         // String representation of register
    UINT          spi_sclk;     // SPI_SCLK
    UINT          spi_en;       // SPI_EN
} SPI_DEVICE_INFO;

#endif // DEFINITIONS

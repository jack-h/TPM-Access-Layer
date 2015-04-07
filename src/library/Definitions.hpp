#ifndef DEFINITIONS
#define DEFINITIONS

#include <stdint.h>

// Enable or disable debugging
#define DEBUG 1

// To export functions to a Windows DLL we need to apply the DLL_EXPORT in each
// functions. This is defined in Windows, however will not work for Linux. Therefore
// in Linux we map this to an empty string
#ifndef DLL_EXPORT
    #if defined(_WIN32) || defined(WIN32) || defined(WIN64) || defined(_WIN64)
        #define DLL_EXPORT __declspec(dllexport)
    #else
        #define DLL_EXPORT
    #endif
#endif

// ========================== DATA TYPE DEFINITIONS ==========================

// Representation of board ID
typedef int ID;

// Representation of register name
typedef const char* REGISTER;

// Representation of basic datatype
typedef uint32_t UINT;

// Device types
typedef enum { BOARD = 1, FPGA_1 = 2, FPGA_2 = 4 } DEVICE;

// Return type for most of the function calls, specifying whether the call
// succeeded or failed
typedef enum {SUCCESS = 0, FAILURE = -1, NOT_IMPLEMENTED = -2} RETURN;

// Define possible board statuses
typedef enum { OK                =  0,  // Board is functioning properly
               LOADING_FIRMWARE  = -1,  // Firmware being laoded on an FPGA
               CONFIG_ERROR      = -2,  // Error configuring firmware
               BOARD_ERROR       = -3,  // Board health check failed
               NOT_CONNECTED     = -4,  // Connect wasn't called 
               NETWORK_ERROR     = -5}  // Board cannot be reached
STATUS;

// At least three types of registers can be defined (a sensor, a board/
// peripheral register and a firmware register).
typedef enum {SENSOR            = 1, 
              BOARD_REGISTER    = 2, 
              FIRMWARE_REGISTER = 3, 
              SPI_DEVICE        = 4, 
              COMPONENT         = 5} REGISTER_TYPE;

// ### Register access permissions 
typedef enum {READ = 1, WRITE = 2, READWRITE = 3} PERMISSION;

// Encapsulate a register or sensor value. This structure is require to avoid
// assigning a particular value as the error value, or avoid using reference
// varaibles in the parameter list. This structure can be extended if 
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

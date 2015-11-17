#include "Utils.hpp"
#include "message.pb.h"

// Disable return type warning temporarily
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wreturn-type"

// Convert Error enum
Reply::ResultType convertErrorEnum(RETURN err)
{
    if (err == SUCCESS)
        return Reply::SUCCESS;
    else
        return Reply::FAILURE;
}

// Convert Device enum (overload 1)
Reply::DeviceType convertDeviceEnum(DEVICE dev)
{
    if (dev == BOARD)
        return Reply::BOARD;
    else if (dev == FPGA_1)
         return Reply::FPGA_1;
    else if (dev == FPGA_2)
        return Reply::FPGA_2; 

    return Reply::BOARD;
}

// Convert Device enum (overload 2)
DEVICE convertDeviceEnum(Reply::DeviceType dev)
{
    if (dev == Reply::BOARD)
        return BOARD;
    else if (dev == Reply::FPGA_1)
        return FPGA_1;
    else if (dev == Reply::FPGA_2)
        return FPGA_2;

    return BOARD;
}

// Convert Device enum (overload 3)
DEVICE convertDeviceEnum(Request::DeviceType dev)
{
    if (dev == Request::BOARD)
        return BOARD;
    else if (dev == Request::FPGA_1)
        return FPGA_1;
    else if (dev == Request::FPGA_2)
        return FPGA_2;

    return BOARD;
}

// Convert Register Type enum
Reply::RegisterType convertTypeEnum(REGISTER_TYPE type)
{
    if (type == SENSOR)
        return Reply::SENSOR;
    else if (type == BOARD_REGISTER)
        return Reply::BOARD_REGISTER;
    else
        return Reply::FIRMWARE_REGISTER;
}

// Convert Permission enum
Reply::PermissionType convertPermissionEnum(PERMISSION per)
{
    if (per == READ)
        return Reply::READ;
    else if (per == WRITE)
        return Reply::WRITE;
    else
        return Reply::READWRITE;
}

// Convert BoardMake enum
BOARD_MAKE convertBoardEnum(Request::BoardMake board)
{
    if (board == Request::TPM)
        return TPM_BOARD;
    else if (board == Request::ROACH)
        return ROACH2_BOARD;
    else 
        return UNIBOARD_BOARD;
}

// Re-enable return type warning
#pragma GCC diagnostic pop

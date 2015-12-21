#ifndef UTILS_HEADER
#define UTILS_HEADER

#include "AccessLayer.hpp"
#include "message.pb.h"

// Convert Error enum
Reply::ResultType convertErrorEnum(RETURN err);

// Convert Device enum (overload 1)
Reply::DeviceType convertDeviceEnum(DEVICE dev);

// Convert Device enum (overload 2)
DEVICE convertDeviceEnum(Reply::DeviceType dev);

// Convert Device enum (overload 3)
DEVICE convertDeviceEnum(Request::DeviceType dev);

// Convert TPM Status
Reply::TpmStatus convertTpmStatus(STATUS status);

// Convert Register Type enum
Reply::RegisterType convertTypeEnum(REGISTER_TYPE type);

// Convert Permission enum
Reply::PermissionType convertPermissionEnum(PERMISSION per);

// Convert BoardMake enum
BOARD_MAKE convertBoardEnum(Request::BoardMake board);

#endif // UTILS_HEADER

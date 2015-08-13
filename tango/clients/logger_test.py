from aavs_logger import Aavs_Logger, LogLevels

myLogger = Aavs_Logger(LogLevels.Informational, ";")
myLogger.log(log_message = "hello moon", source = "dev1.dev2.dev3", log_level = LogLevels.Debugging)
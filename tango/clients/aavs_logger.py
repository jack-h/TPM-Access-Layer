import syslog
from enum import Enum

_LEVELS = {
    'Emergency': syslog.LOG_EMERG,
    'Alert': syslog.LOG_ALERT,
    'Critical': syslog.LOG_CRIT,
    'Error': syslog.LOG_ERR,
    'Warning': syslog.LOG_WARNING,
    'Notice': syslog.LOG_NOTICE,
    'Informational': syslog.LOG_INFO,
    'Debugging': syslog.LOG_DEBUG}

class LogLevels(Enum):
    Emergency = 0
    Alert =  1
    Critical = 2
    Error = 3
    Warning = 4
    Notice = 5
    Informational = 6
    Debugging = 7

class Aavs_Logger(object):

    _apptag = "AAVS"

    # Class constructor
    def __init__(self, log_level = LogLevels.Debugging, delimiter = ';'):
        self.log_level = self.get_log_level(log_level)
        self.delimiter = delimiter
        syslog.openlog()

    def get_log_level(self, log_level):
        return _LEVELS.get(log_level.name)

    def set_log_level(self, level):
        if level is not None:
            self.log_level = self.get_log_level(level)

    def get_delimiter(self):
        return self.delimiter

    def set_delimiter(self, delimiter):
        if delimiter is not None:
            self.delimiter = delimiter

    def log(self, log_message, source = "log", log_level = None):
        if log_level is not None:
            context_log_level = self.get_log_level(log_level)
        else:
            context_log_level = self.log_level

        full_msg = self._apptag+self.delimiter+source+self.delimiter+log_message
        syslog.syslog(context_log_level, full_msg)

if __name__ == '__main__':
    myLogger = Aavs_Logger(LogLevels.Informational, ";")
    myLogger.log(log_message = "hello world", source = "dev1.dev2.dev3", log_level = LogLevels.Informational)
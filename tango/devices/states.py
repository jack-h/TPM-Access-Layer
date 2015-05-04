from enum import Enum

class BoardState(Enum):
    """ Board State enumeration """
    UNKNOWN = 0         # Tango
    INIT = 1            # Tango (was Initialising)
    ON = 2              # Tango (was Ready)
    RUNNING = 3         # Tango (was In_use)
    FAULT = 4           # Tango (was Faulty)
    OFF = 5             # Tango
    STANDBY = 6         # Tango
    SHUTTING_DOWN = 7   # Tango Close?
    MAINTENANCE = 8     # ???
    LOW_POWER = 9       # ???
    SAFE_STATE = 10     # ???

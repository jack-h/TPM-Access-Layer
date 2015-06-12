from pyfabil.boards.fpgaboard import FPGABoard
from pyfabil.base.definitions import *

class UniBoard(FPGABoard):
    """ FPGABoard subclass for communicating with a UniBoard """

    def __init__(self, **kwargs):
        """ Class constructor """

        # Check that a nodelist

        kwargs['fpgaBoard'] = BoardMake.UniboardBoard
        super(UniBoard, self).__init__(**kwargs)




from boarddriver.boards.fpgaboard import FPGABoard
from boarddriver.base.definitions import *

class UniBoard(FPGABoard):
    """ FPGABoard subclass for communicating with a UniBoard """

    def __init__(self, **kwargs):
        """ Class constructor """
        kwargs['fpgaBoard'] = BoardMake.UniboardBoard
        super(UniBoard, self).__init__(**kwargs)
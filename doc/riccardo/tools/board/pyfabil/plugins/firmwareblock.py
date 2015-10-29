# Add parent directory to PYTHONPATH
from sys import path
import os
path.append(os.path.abspath('...'))

from abc import ABCMeta, abstractmethod

class FirmwareBlock(object):
    """ Abstract super class which must be used to implement firmware
        block plugins to be used with the access layer """

    def __init__(self, board):
        """ Initialiase FirmwareBlock instance
        :param board: Reference to board instance on which operations will be performed
        :return: Nothing
        """
        # Define class as an abstract class
        self.__metaclass__ = ABCMeta

        # Plugins require access to board members to perform operations on the board
        # For this reason, the calling board instance has to be stored here
        # self._board  = board
        self.board = board

    @abstractmethod
    def initialise(self, **kwargs):
        """ Abstract method where all firmware block initialisation should be performed
        :param kwargs: Initialisation arguments
        :return: True or Flase, depending on whether initialisation was successful
        """
        pass

    @abstractmethod
    def status_check(self):
        """ Abstract method where all status checks should be performed
        :return: Firmware status
        """
        pass

    @abstractmethod
    def clean_up(self):
        """ Abstract method where all cleaning up should be performed when unload firmware
        :return: True or Flase, depending on whether call was successful
        """
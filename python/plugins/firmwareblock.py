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
        # TODO: Add type checks, since plugins can only be compatible with specific board types (presumably)
        self._board  = board


    @abstractmethod
    def initialise(self):
        """ Abstract method where all firmware block initialisation should be performed
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
    def test(self):
        """ Test firmware block
        :return: Success or Failure
        """
        pass

    @abstractmethod
    def clean_up(self):
        """ Abstract method where all cleaning up should be performed when unload firmware
        :return: True or Flase, depending on whether call was successful
        """

    # ------------------------ Access Layer function wrappers ----------------------------
    def readRegister(self, device, register, n = 1, offset = 0):
        """ Read register on board
        :param device: Device on board
        :param register: Register name
        :param n: Number of values to read
        :param offset: Offset at which to read
        :return: read data
        """
        return self._board.readRegister(device, register, n, offset)

    def writeRegister(self, device, register, values, offset = 0):
        """ Write register on board
        :param device: Device on board
        :param register: Register name
        :param values: Values to write
        :param offset: Offset at which to write
        :return: Success or Failure
        """
        return self._board.writeRegister(device, register, values, offset)

    def readAddress(self, address, n = 1):
        """ Read address on board
        :param address: Address
        :param n: Number of wrods to read
        :return: Values
        """
        self._board(address, n)

    def writeAddress(self, address, values):
        """ Write address on board
        :param address: Address
        :param values: Values to write
        :return: Success or Failure
        """
        self._board(address, values)

    def readDevice(self, device, address):
        """ Read from SPI device on board
        :param device: SPI device
        :param address: Address
        :return: Values
        """
        self._board.readDevice(device, address)

    def writeDevice(self, device, address, value):
        """ Write to SPI device on board
        :param device: SPI device
        :param address: Address
        :param value: Value to write
        :return: Success or Failure
        """
        self._board.writeDevice(device, address, value)
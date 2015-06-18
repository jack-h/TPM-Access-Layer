# This script present a mock UniBoard, used for testing the access layer
from time import sleep
import threading
import socket
import struct

UDP_PORT = 50000

# Unpack string for UCP packet header
# 1st byte:  PSN
# 2nd byte:  OPCODE
# 3rd byte:  N
# 4th byte:  ADDRESS
UCP_header_fmt = 'IIII'

# UCP OPCODES
OPCODE_READ  = 0x01
OPCODE_WRITE = 0x02

logging = False
def output(string):
    if logging:
        print string

class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

class Node(StoppableThread):

    def __init__(self, port):
        """ Class initialiser """
        super(Node, self).__init__()

        # Dictionary to represent memory
        self._memory = {}

        # Create socket, bind and set timeout
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(("", port))
        self._sock.settimeout(1)

    def read_memory(self, address, n):
        """ Mock reading from TPM memory """

        # Read values
        values = []

        # For each memory address, check if it is alread in memory
        # if not, create a value and store in memory
        for i in range(n):
            addr = address + i * 4
            if addr in self._memory.keys():
                values.append(self._memory[addr])
            else:
                self._memory[addr] = 0
                values.append(0)

        # Return values
        return values

    def write_memory(self, address, n, values):
        """ Mock writing to TPM memory """

        # Blindly store all value to memory
        for i in range(n):
            addr = address + i * 4
            self._memory[addr] = values[i]

    def run(self):

        while True:
            # If stopping clause has been set, return from main method
            if self.stopped():
                return

            # Receive packet (non-blocking)
            output("%s. Waiting for packet" % self.name)
            try:
                data, addr = self._sock.recvfrom(512)
            except Exception:
                continue

            # Received packet, extract and convert data
            psn, opcode, num_elements, address = struct.unpack(UCP_header_fmt, data[:16])
            psn           = psn
            opcode        = opcode
            num_elements  = num_elements
            address       = address

            # Switch on opcode
            if opcode == OPCODE_READ:

                # Read operation, return packet with data
                values = self.read_memory(address, num_elements)
                packet = struct.pack("II" + "I" * num_elements,
                                     psn,
                                     address,
                                     *values)
                self._sock.sendto(packet, addr)
                output("%s. Request to read addr %#08X, provided value %d (x %d)" % (self.name, address, values[0], num_elements))

            elif opcode == OPCODE_WRITE:

                # Write opreation, extract value
                values = struct.unpack('I' * num_elements, data[16:])

                # Return reply packet
                self.write_memory(address, num_elements, values)
                packet = struct.pack("II",
                                     psn,
                                     address)
                self._sock.sendto(packet, addr)
                output("%s. Request to write value %d to address %#08X" % (self.name, values[0], address))
            else:
                output("%s. Unsupported opcode %d" % (self.name, opcode))


class UniBoardSimulator(StoppableThread):

    def __init__(self):
        super(UniBoardSimulator, self).__init__()
        self._nodes = []

    def run(self):

        # Initialise and run Node threads
        for i in xrange(8):
            n = Node(UDP_PORT + i)
            n.setName("Node %d" % i)
            self._nodes.append(n)
            n.start()

        # Wait until the thread is stopped
        while not self.stopped():
            sleep(1)

        # Wait for all node threads to finish
        [n.join() for n in self._nodes]

        return

    def stop(self):
        """ Override stop to call the stop method for all nodes """
        [n.stop() for n in self._nodes]
        super(UniBoardSimulator, self).stop()

# Script entry point
if __name__ == "__main__":
    logging = True
    simulator = UniBoardSimulator()
    simulator.start()
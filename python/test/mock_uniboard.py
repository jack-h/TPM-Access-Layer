# This script present a mock UniBoard, used for testing the access layer

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

class Node(threading.Thread):

    def __init__(self, port):
        """ Class initialiser """
        super(Node, self).__init__()

        self.memory = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", port))


    def readMemory(self, address, n):
        """ Mock reading from TPM memory """

        # Read values
        values = []

        # For each memory address, check if it is alread in memory
        # if not, create a value and store in memory
        for i in range(n):
            addr = address + i * 4
            if addr in self.memory.keys():
                values.append(self.memory[addr])
            else:
                self.memory[addr] = 0
                values.append(0)

        # Return values
        return values

    def writeMemory(self, address, n, values):
        """ Mock writing to TPM memory """

        # Blindly store all value to memory
        for i in range(n):
            addr = address + i * 4
            self.memory[addr] = values[i]

    def run(self):

        while True:
            # Receive packet (blocking)
            print "%s. Waiting for packet" % self.name
            data, addr = self.sock.recvfrom(512)

            # Received packet, extract and convert data
            psn, opcode, num_elements, address = struct.unpack(UCP_header_fmt, data[:16])
            psn           = psn
            opcode        = opcode
            num_elements  = num_elements
            address       = address

            # Switch on opcode
            if opcode == OPCODE_READ:

                # Read operation, return packet with data
                values = self.readMemory(address, num_elements)
                packet = struct.pack("II" + "I" * num_elements,
                                     psn,
                                     address,
                                     *values)
                self.sock.sendto(packet, addr)
                print "%s. Request to read addr %#08X, provided value %d (x %d)" % (self.name, address, values[0], num_elements)

            elif opcode == OPCODE_WRITE:

                # Write opreation, extract value
                values = struct.unpack('I' * num_elements, data[16:])

                # Return reply packet
                self.writeMemory(address, num_elements, values)
                packet = struct.pack("II",
                                     psn,
                                     address)
                self.sock.sendto(packet, addr)
                print "%s. Request to write value %d to address %#08X" % (self.name, values[0], address)
            else:
                print "%s. Unsupported opcode %d" % (self.name, opcode)


# Script entry point
if __name__ == "__main__":

    nodes = []
    for i in xrange(8):
        n = Node(UDP_PORT + i)
        n.setName("Node %d" % i)
        nodes.append(n)
        n.start()



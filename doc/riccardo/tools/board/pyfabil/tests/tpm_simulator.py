# This script present a mock TPM, used for testing the access layer

import socket
import struct

UDP_PORT = 10000

# Unpack string for UCP packet header
# 1st byte:  PSN
# 2nd byte:  OPCODE
# 3rd byte:  N
# 4th byte:  ADDRESS
UCP_header_fmt = 'IIII'

# UCP OPCODES
OPCODE_READ  = 0x01
OPCODE_WRITE = 0x02

# Mock TPM memory
# An entry per memory location is created
memory = { }

def readMemory(address, n):
    """ Mock reading from TPM memory """

    # Read values
    values = []

    # For each memory address, check if it is alread in memory
    # if not, create a value and store in memory
    for i in range(n):
        addr = address + i * 4
        if addr in memory.keys():
            values.append(memory[addr])
        else:
            memory[addr] = 0
            values.append(0)

    # Return values
    return values

def writeMemory(address, n, values):
    """ Mock writing to TPM memory """

    # Blindly store all value to memory
    for i in range(n):
        addr = address + i * 4
        memory[addr] = values[i]

# Script entry point
if __name__ == "__main__":
    
    # Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind socket
    sock.bind(("", UDP_PORT))

    # Continuously wait for packets
    while True:

        # Receive packet (blocking)
        print "Waiting for packet"
        data, addr = sock.recvfrom(512)
        
        # Received packet, extract and convert data
        psn, opcode, n, address = struct.unpack(UCP_header_fmt, data[:16])
        psn     = psn
        opcode  = opcode
        n       = n
        address = address

        # Switch on opcode
        if (opcode == OPCODE_READ):
         
            # Read operation, return packet with data
            values = readMemory(address, n)
            packet = struct.pack("II" + "I" * n, 
                                 psn, 
                                 address, 
                                 *values)
            sock.sendto(packet, addr)
            print "Request to read addr %#08X, provided value %d (x %d)" % (address, values[0], n)

        elif (opcode == OPCODE_WRITE):

            # Write opreation, extract value
            values = struct.unpack('I' * n, data[16:])        

            # Return reply packet
            writeMemory(address, n, values)
            packet = struct.pack("II", 
                                 psn, 
                                 address)
            sock.sendto(packet, addr)
            print "Request to write value %d to address %#08X" % (values[0], address)
        else:
            print "Unsupported opcode %d" % opcode
            continue

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

# Script entry point
if __name__ == "__main__":
    
    # Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind socket
    sock.bind(("10.62.14.234", UDP_PORT))

    # Continuously wait for packets
    while True:

        # Receive packet (blocking)
        print "Waiting for packet"
        data, addr = sock.recvfrom(512)
        
        # Received packet, extract and convert data
        psn, opcode, n, address = struct.unpack(UCP_header_fmt, data[:16])
        psn     = socket.ntohl(psn)
        opcode  = socket.ntohl(opcode)
        n       = socket.ntohl(n)
        address = socket.ntohl(address)

        # Switch on opcode
        if (opcode == OPCODE_READ):
         
            # Read operation, return packet with data
            value = 69
            packet = struct.pack("III", 
                                 socket.htonl(psn), 
                                 socket.htonl(address), 
                                 socket.htonl(value))
            sock.sendto(packet, addr)
            print "Request to read addr %#08X, provided value %d" % (address, value)

        elif (opcode == OPCODE_WRITE):

            # Write opreation, extract value
            value = socket.ntohl(struct.unpack('I', data[16:])[0])        

            # Return reply packet
            packet = struct.pack("II", 
                                 socket.htonl(psn), 
                                 socket.htonl(address))
            sock.sendto(packet, addr)
            print "Request to write value %d to address %#08X" % (value, address)
        else:
            print "Unsupported opcode %d" % opcode
            continue

import socket
from time import sleep
import spead
import numpy

IP   = "192.168.1.65"
PORT = 10000

def transmit():

    # Initialise SPEAD transmitter
    tx = spead.Transmitter(spead.TransportUDPtx(IP, PORT))

    # Add items to item group
    ig = spead.ItemGroup()
    ig.add_item(name="station", shape=[], fmt=spead.mkfmt(('u', 1)), init_val = (1))
    data = numpy.arange(40000).astype(numpy.uint32); data.shape = (40000)
    ig.add_item(name='data', shape=[40000], ndarray=data)

    # Continuously send heap
    while True:
        tx.send_heap(ig.get_heap())

    tx.end()
    print 'TX: Done.'

def transmit_bare_udp():
    message = "Hello, World!"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP

    while True:
        sock.sendto(bytes(message), (IP, PORT))

if __name__ == "__main__":
    transmit_bare_udp()
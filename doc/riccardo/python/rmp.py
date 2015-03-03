"""!@package rmp UDP socket management and RMP packet encoding/decoding
 
This package provides functions for network initializing and basic 32 bit read/write
operations on the network attached device using RMP protocol. This is rough and minimal code
not exploiting all the RMP protocol features.     
"""
import socket
import array
from struct import *

def InitNetwork(this_ip,fpga_ip,udp_port,timeout):
   """!@brief Initialize the network
   
   It Opens the sockets and sets specific options as socket receive time-out and buffer size.
   
   @param this_ip  -- str -- Host machine IP address
   @param fpga_ip  -- str -- Network attached device IP address
   @param udp_port -- int -- UDP port
   @param timeout  -- int -- Receive Socket time-out in seconds
   
   Returns -- int -- socket handle
   """
   global this_fpga_ip
   global this_sock
   global this_udp_port
   
   sock = socket.socket(socket.AF_INET,      # Internet
                        socket.SOCK_DGRAM)   # UDP   
   sock.settimeout(timeout)
   sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024*1024)
   sock.bind((this_ip, udp_port))
   this_fpga_ip = fpga_ip
   this_udp_port = udp_port
   this_sock = sock
   return sock
   
def CloseNetwork():
   """!@brief Close previously opened socket.
   """
   global this_sock
   this_sock.close()
   return
   
def wr32(add,dat):
   """!@brief Write remote register at address add with dat. 
   
   It transmits a write request to the remote device.
   It performs 32 bits write operations only, each UDP packet contains a single write.
   
   @param add -- int -- 32 bits remote address
   @param dat -- int -- 32 bits write data 
   """
   global this_fpga_ip
   global this_sock
   global this_udp_port
   
   pkt = array.array('L')
   pkt.append(1001)           #psn
   pkt.append(2)              #opcode
   pkt.append(1)              #noo
   pkt.append(add)            #sa
   pkt.append(dat)            #dat
   
   this_sock.sendto(bytes(pkt.tostring()),(this_fpga_ip,this_udp_port))
   data, addr = this_sock.recvfrom(10240)
   return
   
def rd32(add):
   """!@brief Read remote register at address add. 
   
   It transmits a read request and waits for a read response from the remote device.
   Once the response is received it extracts relevant data from a specific offset within the
   UDP payload and returns it. In case no response is received from the remote device
   a socket time-out occurs.
   It performs 32 bits read operations only, each UDP packet contains a single read.
   
   @param add -- int -- 32 bits remote address  
   
   Returns -- int -- read data
   """
   global this_fpga_ip
   global this_sock
   global this_udp_port
   
   pkt = array.array('L')
   pkt.append(1001)           #psn
   pkt.append(1)              #opcode
   pkt.append(1)              #noo
   pkt.append(add)            #sa
   
   this_sock.sendto(bytes(pkt.tostring()),(this_fpga_ip,10000))
   data, addr = this_sock.recvfrom(10240)

   add, dat, = unpack('LL',data[4:4+8])
   
   #dat_list = []
   #for n in range(0,2):
   #   dat, = unpack('L',data[8+4*n:8+4*n+4])
   #   print dat
   #   dat_list.append(dat)
   #print dat_list
   
   return dat 
   
   
   
   
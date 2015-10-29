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
   global remote_udp_port
   global this_timeout
   
   sock = socket.socket(socket.AF_INET,      # Internet
                        socket.SOCK_DGRAM)   # UDP   
   sock.settimeout(1)
   sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024*1024)
   sock.bind((this_ip, 0))
   this_fpga_ip = fpga_ip
   remote_udp_port = udp_port
   this_sock = sock
   this_timeout = timeout
   return sock
   
def CloseNetwork():
   """!@brief Close previously opened socket.
   """
   global this_sock
   this_sock.close()
   return
   
def recvfrom_to(buff):
   global this_timeout
   global this_sock
   
   attempt = 0
   while(attempt<this_timeout or this_timeout==0):
      try: 
         return this_sock.recvfrom(10240)
      except:
         attempt += 1
   raise NameError("UDP timeout. No answer from remote end!")

def wr32(add,dat):
   """!@brief Write remote register at address add with dat. 
   
   It transmits a write request to the remote device.
   
   @param add -- int -- 32 bits remote address
   @param dat -- int -- 32 bits write data 
   """
   global this_fpga_ip
   global this_sock
   global remote_udp_port
     
   pkt = array.array('I')
   pkt.append(1001)           #psn
   pkt.append(2)              #opcode
   if  type(dat) == list:
      pkt.append(len(dat))    #noo
   else:
      pkt.append(1)           #noo
   pkt.append(add)            #sa
   if type(dat) == list:
      for d in dat:
         pkt.append(d)
   else:
      pkt.append(dat)         #dat
   
   
   this_sock.sendto(bytes(pkt.tostring()),(this_fpga_ip,remote_udp_port))
   data, addr = recvfrom_to(10240)
   return
   
def rd32(add,n=1):
   """!@brief Read remote register at address add. 
   
   It transmits a read request and waits for a read response from the remote device.
   Once the response is received it extracts relevant data from a specific offset within the
   UDP payload and returns it. In case no response is received from the remote device
   a socket time-out occurs.
   
   @param add -- int -- 32 bits remote address  
   
   Returns -- int -- read data
   """
   global this_fpga_ip
   global this_sock
   global remote_udp_port
   
   pkt = array.array('I')
   pkt.append(1001)           #psn
   pkt.append(1)              #opcode
   pkt.append(n)              #noo
   pkt.append(add)            #sa
   
   this_sock.sendto(bytes(pkt.tostring()),(this_fpga_ip,remote_udp_port))
   data, addr = recvfrom_to(10240)

   data = bytes(data)
   
   add = unpack('I', data[4:8]) 
   dat = unpack('I'*n, data[8:])
   
   dat_list = []
   for k in range(n):
      dat_list.append(dat[k])
   
   if n == 1:
      return dat_list[0]
   else:
      return dat_list

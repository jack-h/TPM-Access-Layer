import socket
import rmp
from struct import *
import sys

THIS_UDP_IP = "10.62.14.253"#"10.0.10.1"
FPGA_UDP_IP = "10.62.14.251"#"10.0.10.2"
UDP_PORT = 1000#0xAAAB

def convert_input(s):
   return int(s[s.find("x")+1:],16)
   
rmp.InitNetwork(THIS_UDP_IP,FPGA_UDP_IP,UDP_PORT,1)

if len(sys.argv) == 2:
   print hex(rmp.rd32(convert_input(sys.argv[1])))
elif len(sys.argv) == 3:
   rmp.wr32(convert_input(sys.argv[1]),convert_input(sys.argv[2]))
else:
   "input error!"

rmp.CloseNetwork()
   
   
import sys
import socket
import array
from struct import *
from time import sleep
from optparse import OptionParser
sys.path.append("../")
import config.manager as config_man

def ucp_cmd_parse(pkt):
   data = []
   psn,  = unpack('I', pkt[0:4])
   opc,  = unpack('I', pkt[4:8])
   num,  = unpack('I', pkt[8:12])
   add,  = unpack('I', pkt[12:16])
   
   if opc == 2:
      for n in range(num):
         dat, = unpack('I', pkt[16+4*n:16+4*(n+1)])
         data.append(dat)
         opc_str = "wr"
   elif opc == 1:
      opc_str = "rd"
   else:
      print "unsupported opcode!"
      sys.exit()
   print "UCP " + opc_str + " request:"
   print "   psn:",psn,"opc:",opc,"num:",num,"add:",hex(add)
   for n in data:
      print "   data:", hex(n)
   return psn,opc_str,num,add,data
   
def read_swap_file(file_name):
   while(True):
      sim_file = open(file_name, "r+")
      from_file = sim_file.read()
      content = from_file.split("\n")
      if content[0] == "from_vhdl":
         sim_file.write("")
         sim_file.close()
         #print content
         break;
      else:
         sleep(0.1)
         sim_file.close()
   psn = int(content[1])
   add = int(content[2],16)
   data = []
   idx = 3
   while(True):
      if content[idx] == "ok":
         break
      else:
         try:
            dat = int(content[idx],16)
         except:
            print "Warning: received data ", content[idx]
            print "         assuming 0x0" 
            dat = 0
         data.append(dat)
         idx += 1
   print "UCP " + "response:"
   print "   psn",psn,"add",hex(add)
   for n in data:
      print "   data:", hex(n)
   data = [psn,add] + data
   return data
      
def write_swap_file(file_name,data):
   psn,op,num,add,data = ucp_cmd_parse(data)
   to_file = "to_vhdl" + " " + str(int(psn)) + " " + op + " " + str(int(num)) + " " + hex(int(add))[2:]  + "\n"    
   for n in data:
      to_file = to_file + hex(n)[2:] + "\n"
   sim_file = open(file_name, "w")
   sim_file.write(to_file)
   sim_file.close()
   
def ucp_resp_forge(data):
   pkt = array.array('I')
   for n in range(len(data)):
      pkt.append(int(data[n]))
   return pkt
   
   
parser = OptionParser()
parser.add_option("--i", 
                  dest="src", 
                  default = "",
                  help="Incoming UCP requests listening IP address.")
parser.add_option("--o", 
                  dest="dst", 
                  default = "",
                  help="FPGA IP address.")
parser.add_option("--f", 
                  dest="fwd", 
                  default = "",
                  help="UCP forward packets IP.")
parser.add_option("-m", "--sim_mode", 
                  dest="sim_mode", 
                  default = "",
                  help="Simulation mode. 0 forces network mode, any other value forces simulation mode. I this parameter is not specified the mode is retrieved from configuration file.")
parser.add_option("-t", "--timeout", 
                  dest="timeout", 
                  default = "",
                  help="UDP socket timeout.")
parser.add_option("-p", "--port", 
                  dest="port", 
                  default = "",
                  help="UCP port.")
parser.add_option("-d","--design",
                  dest="design", 
                  default = "",
                  help="Design")
(options, args) = parser.parse_args()


config = config_man.get_config_from_file(config_file="../config/config.txt",design=options.design,display=False,check=True,sim=options.sim_mode)

if options.sim_mode == "1":
   if options.src == "":
      SRC      = ""
   else:
      SRC      = options.src
   if options.dst == "":
      DST      = config['FPGA_IP']
   else:
      DST      = options.dst
   if options.timeout == "":
      TIMEOUT  = config['UDP_TIMEOUT']
   else:
      TIMEOUT  = options.timeout
   if options.port == "":
      UDP_PORT = config['UDP_PORT']
   else:
      UDP_PORT = options.port
   SWP      = config['SWP_FILE']
   FWD      = "0.0.0.0"
   
else:
   if options.src == "":
      print "Unspecified source IP in network mode!"
      sys.exit(1)
   else:
      SRC   = options.src
   if options.dst == "":
      DST      = config['FPGA_IP']
   else:
      DST      = options.dst
   if options.timeout == "":
      TIMEOUT  = config['UDP_TIMEOUT']
   else:
      TIMEOUT  = options.timeout
   if options.port == "":
      UDP_PORT = config['UDP_PORT']
   else:
      UDP_PORT = options.port
   SWP      = ""
   if options.fwd == "":
      FWD   = ""
   else:
      FWD   = options.fwd  

if options.sim_mode == "1":
   print "Running in simulation mode..."
   print "src IP ", SRC
   print "swap file ", SWP
else:
   print "Running in network mode..."
   print "src IP ", SRC
   print "dst IP ", DST
   print "fwd IP ", FWD
print "UDP port ", UDP_PORT
print "UDP timeout ", TIMEOUT

if TIMEOUT == 0:
   TIMEOUT = None
   
sock1 = socket.socket(socket.AF_INET,      # Internet
                      socket.SOCK_DGRAM)   # UDP   
sock1.settimeout(1)
sock1.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024*1024)
sock1.bind((SRC, UDP_PORT))

if options.sim_mode != "1":
   sock2 = socket.socket(socket.AF_INET,      # Internet
                         socket.SOCK_DGRAM)   # UDP   
   sock2.settimeout(None)
   sock2.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024*1024)
   sock2.bind((FWD, UDP_PORT))

   print "Waiting for packets..."
   while(1):
      try:
         #print "receiving request"
         data, addr1 = sock1.recvfrom(10240)
         #print "forwarding request"
         sock2.sendto(bytes(data),(DST,UDP_PORT))
         #print "receiving response"
         data, addr2 = sock2.recvfrom(10240)
         #print "forwarding response"
         sock1.sendto(bytes(data),addr1)
      except socket.timeout:
         print "socket timeout! Waiting for packets..."
else:
   while(1):
      try:
         #print "receiving request"
         data, addr1 = sock1.recvfrom(10240)
         #writing swap file
         write_swap_file(SWP,data)
         #reading swap files
         data = read_swap_file(SWP)
         #forwarding response
         sock1.sendto(bytes(ucp_resp_forge(data).tostring()),addr1)
      except socket.timeout:
         print "socket timeout! Waiting for packets..."

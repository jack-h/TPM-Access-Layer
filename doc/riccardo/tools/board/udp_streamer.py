import os
import re
import sys
import socket
import array
import binascii
from struct import *
from time import sleep
from optparse import OptionParser
sys.path.append("../")
import config.manager as config_man
from repo_utils.functions import *   
   
def swap16(text):
   new_text = ""
   for n in range(len(text)/4):
      word = text[0+4*n:4+4*n]
      word = word[2:4] + word[0:2]
      new_text += word
   return new_text
   
   
parser = OptionParser()
parser.add_option("-i", 
                  dest="src", 
                  default = "",
                  help="c2c streamer log file")
parser.add_option("-f", 
                  dest="fwd", 
                  default = "",
                  help="UCP forward packets IP.")
parser.add_option("-p", "--port", 
                  dest="port", 
                  default = "",
                  help="UCP port.")
parser.add_option("-d","--design",
                  dest="design", 
                  default = "",
                  help="Design")
(options, args) = parser.parse_args()

config = config_man.get_config_from_file(config_file= "../config/config.txt",design=options.design,display=True,check=True)

#config = config_man.get_config_from_file(config_file="../config/config.txt",design=options.design,display=False,check=True,sim=options.sim_mode)

if options.src == "":
   SRC      = config['STREAM_FILE']
else:
   SRC      = options.src
if options.port == "":
   UDP_PORT = 4660#config['UDP_PORT']
else:
   UDP_PORT = int(options.port)
if options.fwd == "":
   FWD      = "127.0.0.1"
else:
   FWD      = options.fwd
   

print "src file ", SRC
print "fwd IP   ", FWD
print "UDP port ", UDP_PORT
   
sock1 = socket.socket(socket.AF_INET,      # Internet
                      socket.SOCK_DGRAM)   # UDP   

seq_num = 0
frame_num = 0
file_name = normalize_path(SRC)
while(1):
   #print "Waiting for new log file..."
   
   if os.path.isfile(file_name):
      text = read_file(file_name)
      if re.search(r"stop",text) != None:
         os.remove(file_name)
         if re.search(r"packet",text) != None:
            flag = "1234"
         else:
            flag = "CDEF"
         header = flag + format(int(frame_num),'04x') + format(int(seq_num),'04x')
         #remove "stop" at the end
         list = text.split("\n")[:-2]
         hex_list = []
         for n in list:
            hex_list.append(format(int(n),'02x'))
         #hex_list.append(format(int(n),'02x'))
         if seq_num == 0:
            hdr_list = hex_list[0:4]
         else:
            hex_list = hdr_list + hex_list
         text = "".join(hex_list)
         text = swap16(header) + text
         print text
         text = binascii.unhexlify(text)
         sock1.sendto(text,(FWD,UDP_PORT))
         print "Packet transmitted..."
         if flag == "CDEF":
            seq_num = 0
            frame_num += 1
            frame_num = frame_num & 0xFFFF
            print "Frame completed!"
         else:
            seq_num += 1
            seq_num = seq_num & 0xFFFF
   else:
      "not found!"
   sleep(0.1)   
   
   


import numpy as np
import pylab
from matplotlib import pyplot as plt   # pylab is the easiest approach to any plotting
import time,datetime                            # we'll do this rendering i real time
import socket
import netproto.sdp as sdp
from struct import *
import sys
import os
from optparse import OptionParser
#import threading
#import Queue

def ByteToHex( byteStr ):
    #"""
    #Convert a byte string to it's hex string representation e.g. for output.
    #"""
    
    # Uses list comprehension which is a fractionally faster implementation than
    # the alternative, more readable, implementation below
    #   
    #    hex = []
    #    for aChar in byteStr:
    #        hex.append( "%02X " % ord( aChar ) )
    #
    #    return ''.join( hex ).strip()        
    return ''.join( [ "%02X " % ord( x ) for x in byteStr ] ).strip()


def fft(input):
   window = np.hanning(len(input))
   output = np.fft.rfft(input*window)
   N = len(output)
   acf = 2  #amplitude correction factor
   output = abs((acf*output)/N)
   output = 20*np.log10(output/127.0)
   return output

   # output = np.fft.rfft(input)
   # output = output/len(output)
   # output = abs(output)
   # output = 20*np.log10(output/127.0)
   # return output
   
def modulo(input):
   #for n in range(len(input)):
   #   print n,input[n]
   mult = 1
   output = np.zeros(len(input)/2, dtype=np.float)
   re = 0.0
   im = 0.0
   x=complex(0,0)
   for n in range(len(input)):
      if n % 4 == 0:
         re = input[n]/(128.0*mult)
      elif n % 4 == 1:
         im = input[n]/(128.0*mult)
         x = complex(re,im)
         p = abs(x)
         output[n/4] = p
      elif n % 4 == 2:
         re = input[n]/(128.0*mult)
      elif n % 4 == 3:
         im = input[n]/(128.0*mult)
         x = complex(re,im)
         p = abs(x)
         output[len(input)/2-n/4-1] = p
   return output
      
def check_pattern(input):
   seed = input[0]
   for n in range(len(input)):
      recv = input[n] + 128
      if n >= 0 and n <= 11:
         exp = (seed + 128 + n%4) & 0xFF
      else:
         exp = (seed + 128 + (n-12))  & 0xFF
      if recv != exp:
         print "error at index " + str(n)
         print "expected " + str(exp)
         print "received " + str(recv)
         xx = pylab.waitforbuttonpress(timeout=0.1)
         exit()
   print "test pattern is good!"

class plot():
   def __init__(self, idx, options):
      self.fig_idx = idx
      self.len_data = 0
      self.active = 1
      self.freq = int(options.frequency)
      self.fft = not options.channelized # 0: Raw Data 1: FFT
      self.save = not options.no_save
      self.output_folder = options.output_folder
      if self.output_folder != "" and self.save == True:
         if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
      self.average = options.average
      self.display = options.display
      self.line = plt.plot(idx,idx)
      self.mngr = plt.get_current_fig_manager()
      self.geom = self.mngr.window.geometry()
      #self.x,self.y,self.dx,self.dy = self.geom.getRect()
      self.x = 50
      self.y = 50
      self.dx = 50
      self.dy = 50
      self.sp0_acc = np.array(0)
      self.times = 0
   def calc(self,data):
      self.times += 1
      if self.display == True:
         #print "len: " + str(len(data))
         plt.figure(self.fig_idx)
         if self.fft == True:
            if self.len_data != len(data):   #1024
               self.len_data = len(data)     #1024
               #print self.len_data
               x = np.arange(0,self.len_data,1)
               freq = np.fft.rfftfreq(x.shape[-1])
               freq = freq*self.freq
               plt.clf()
               self.line, = plt.plot(freq,freq)
               #self.position_calc()
               plt.ylim(-140.0,1.0)  # set the range for our plot
         else:
            L = 1024
            if self.len_data != L/2:
               self.len_data = L/2
               x = np.arange(0,self.len_data,1)
               plt.clf()
               self.line, = plt.plot(x,x)
               #self.position_calc()
               #plt.ylim(-140,1.0)
               plt.ylim(0,1)
         if self.fft == True: 
            sp0 = fft(data)
            #sp0 = fft(data[0:1024])
         else:
            sp0 = modulo(data[0:L])# 20*np.log10(modulo(data[0:L])) #
            for n in range(len(sp0)):
               if sp0[n] < -140:
                  sp0[n] = -150
            #print sp0
         print self.fig_idx," signal level: ",max(sp0[10:-10]),"dBm"
         if self.average == True:
            self.sp0_acc = self.sp0_acc + sp0
            self.line.set_ydata(self.sp0_acc/float(self.times))     ##average
         else:
            self.line.set_ydata(sp0)                                ##real-time
         if self.average == True:
            title_str = "Input: " + str(self.fig_idx) + " - Acq: " + str(self.times) + " - Averaged"
         else:
            title_str = "Input: " + str(self.fig_idx) + " - Acq: " + str(self.times)
         plt.title(title_str)
         plt.draw()
         self.active = 1;
      if self.save == True:
         #if self.display == True:
            #fig_filename = self.output_folder + "fft_input_" + str(self.fig_idx) + ".png"
            #plt.savefig(fig_filename)
         raw_filename = self.output_folder + "input_" + str(self.fig_idx) + "_" + str(self.times-1) + ".bin"
         raw_file = open(raw_filename, "wb")
         raw_file.write(data)
         raw_file.close()
      xx = pylab.waitforbuttonpress(timeout=0.001)
   def close(self):
      if self.active == 1:
         plt.figure(self.fig_idx)
         plt.close()
         self.active = 0;
         self.len_data = 0
   def position_calc(self):
      self.mngr = plt.get_current_fig_manager()
      self.geom = self.mngr.window.geometry()
      plt.figure(self.fig_idx)
      self.dx = 320
      self.dy = 240
      x=50
      y=50
      offset_x=16
      offset_y=40
      if self.fig_idx < 4:
          if   self.fig_idx % 4 == 0:
             self.mngr.window.setGeometry(x                  , y                  , self.dx, self.dy)
          elif self.fig_idx % 4 == 1:
             self.mngr.window.setGeometry(x+self.dx+offset_x , y                  , self.dx, self.dy)
          elif self.fig_idx % 4 == 2:
             self.mngr.window.setGeometry(x                  , y+self.dy+offset_y , self.dx, self.dy)
          elif self.fig_idx % 4 == 3:
             self.mngr.window.setGeometry(x+self.dx+offset_x , y+self.dy+offset_y , self.dx, self.dy)
      else:
          if   self.fig_idx % 4 == 0:
             self.mngr.window.setGeometry(x+640+32                  , y                  , self.dx, self.dy)
          elif self.fig_idx % 4 == 1:
             self.mngr.window.setGeometry(x+640+32+self.dx+offset_x , y                  , self.dx, self.dy)
          elif self.fig_idx % 4 == 2:
             self.mngr.window.setGeometry(x+640+32                  , y+self.dy+offset_y , self.dx, self.dy)
          elif self.fig_idx % 4 == 3:
             self.mngr.window.setGeometry(x+640+32+self.dx+offset_x , y+self.dy+offset_y , self.dx, self.dy)
     
def is_first(channel_id,channel_disable):
   ret = 0
   disable = channel_disable
   for n in range(16):
      if disable & 0x1 == 0:
         if channel_id == n:
            ret = 1
         break
      disable = disable >> 1
   return ret

def is_last(channel_id,channel_disable):
   ret = 0
   disable = channel_disable
   for n in reversed(range(16)):
      if disable & 0x8000 == 0:
         if channel_id == n:
            ret = 1
         break
      disable = disable << 1
   return ret
   
def set_channel(channel_ok,channel_id):
   mask = 1 << channel_id
   channel_ok = channel_ok | mask;
   return channel_ok
      
     
plt.ion()                                 # interaction mode needs to be turned off

parser = OptionParser()
parser.add_option("-o", "--object",  
                  dest="output_folder",
                  default = "",
                  help="a mnemonic of the acquisition appended to the directory path")
parser.add_option("-f", "--freq", 
                  dest="frequency", 
                  default = 700,
                  help="sampling frequency")
parser.add_option("--na", 
                  action="store_false",
                  dest="average", 
                  default = True,
                  help="don't average acquired data")
parser.add_option("--nd", 
                  action="store_false",
                  dest="display", 
                  default = True,
                  help="don't display FFT")
parser.add_option("--ns", 
                  action="store_false",
                  dest="no_save", 
                  default = True,
                  help="don't write output files")
parser.add_option("-n", "--num", 
                  dest="acq_num", 
                  default = 0,
                  help="Number of acquisition")
parser.add_option("-c", "--channelized",
                  action="store_true",
                  dest="channelized", 
                  default = False,
                  help="Plot channelized data")
                  
(options, args) = parser.parse_args()


THIS_UDP_IP = ""
UDP_PORT = 0x1234

print "THIS IP:", THIS_UDP_IP
print "UDP port:", UDP_PORT
if options.no_save == True:
   options.output_folder = ""
else:
   if options.output_folder != "":
      options.output_folder = "_" + options.output_folder
   options.output_folder =  "DATA/"+datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()),"%Y-%m-%d_%H%M%S") + options.output_folder 
   if options.output_folder[-1] != "/":
      options.output_folder += "/"
   print "OUTPUT FOLDER:",options.output_folder

sock = socket.socket(socket.AF_INET,      # Internet
                     socket.SOCK_DGRAM)   # UDP    
sock.settimeout(1);
sock.bind((THIS_UDP_IP, UDP_PORT));
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 3*1024*1024)
#sock.setblocking(0)

plot_list = []
channel_list = []
channel_id_list = np.zeros(16, dtype=np.int)
for i in range(0,16):
   plot_list.append(plot(i,options))
   channel_list.append("")

first_time = 1
frame_exp = 0
channel_ok = 0
num = int(options.acq_num)
done = 0
while(done != num or num == 0):
   frame_num, channel_disable, channel_id, bit_per_sample, reassembled_header_data = sdp.reassemble(sock)
   print "frame_num:" + str(frame_num)
   print "channel_id:" + str(channel_id)
   print "channel_disable:" + hex(channel_disable)
   print "bit_per_sample:" + str(bit_per_sample)
   
   reassembled_header = reassembled_header_data[0:4096]
   reassembled_data   = reassembled_header_data[4096:]
   
   if first_time == 1:
      print "TAG RAM is: "
      print reassembled_header
      first_time = 0

   if is_first(channel_id,channel_disable) == 1:
      channel_ok = 0
   
   if frame_exp == frame_num:
      channel_list.insert(channel_id,reassembled_data)
      channel_list.pop(channel_id+1)
      channel_id_list[channel_id] = 1
      channel_ok = set_channel(channel_ok,channel_id)
   else:
      channel_ok = 0
      channel_id_list = np.zeros(16, dtype=np.int)
   frame_exp = frame_num + 1
   
   if channel_disable == (~channel_ok & 0xFFFF):
      done += 1
      print "Number of Acquisition: " + str(done)
      for n in range(16):
         if channel_id_list[n] == 1:
            plot_list[n].calc(np.frombuffer(channel_list[n], dtype=np.int8))

   #plot_list[channel_id].position_calc()

print "Done!"
   
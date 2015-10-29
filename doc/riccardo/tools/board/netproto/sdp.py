import socket
from struct import *
import numpy as np
import time


def reassemble(sock):
   seq_num_exp = 0;
   frame_num_exp = 0;
   channel_id_exp = 0;
   write = 0;
   reassembled = ""
   while(True):
      while(True):
         try: 
            data, addr = sock.recvfrom(10240)
            break
         except:
            pass
      #print "pkt!"
      #data, addr = sock.recvfrom(10240)
      magic, frame_num, seq_num, channel_id, channel_disable  = unpack('HHHHH',data[0:10])
      bit_per_sample = (channel_id & 0x0F00) >> 4
      channel_id = channel_id & 0x001F
      print "frame_num", frame_num
      print "seq_num", seq_num
      print "magic", hex(magic)
      print "channel_id", channel_id_exp
      print "channel_disable", channel_disable
      
      if seq_num == 0: 
         channel_id_exp = channel_id
         frame_num_exp = frame_num
         seq_num_exp = 1
         write = 1;
         reassembled = ""
      elif (seq_num_exp == seq_num and frame_num_exp == frame_num and channel_id_exp == channel_id):
         seq_num_exp = seq_num + 1
         write = 1;
      else:
         #print "lost!"
         seq_num_exp = 0
         write = 0;
         reassembled = ""

      if write == 1:
         reassembled = reassembled + data[6+4:len(data)]
         if magic == 0xCDEF:
            return frame_num, channel_disable, channel_id, bit_per_sample, reassembled
            
def channel_demux(channel_disable,bit_per_sample,reassembled):
   channel_enabled_list = []
   channel_data_list = []
   channel_done = 0
   channel_num = 0
   if bit_per_sample == 8:
      for n in range(0,16):
         if ((channel_disable >> n) & 0x1) == 0:
            channel_enabled_list.append(n)
            channel_num += 1
            
      #print len(reassembled)
      #print channel_num
      
      for n in range(0,16):
         if ((channel_disable >> n) & 0x1) == 0:
            single_channel_data = ""
            for m in range(0,len(reassembled)/(4*channel_num)):
               single_channel_data += reassembled[(4*m*channel_num)+(4*channel_done):(4*m*channel_num)+(4*channel_done)+4]
            channel_done += 1
            channel_data_list.append(np.frombuffer(single_channel_data, dtype=np.int8))
            #channel_data_list.append(single_channel_data)
      return channel_data_list, channel_enabled_list
   else:
      print "Yet to do!"
      return 


   



      
  
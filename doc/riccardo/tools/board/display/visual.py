import numpy as np
from multiprocessing import Process

import matplotlib.pyplot as plt

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

class DataVisualProcess(Process):
   def __init__(self, connec, idx , options, *args, **kwargs):
      print "initializing visual process with idx ",idx
      self.connec = connec
      self.fig_idx_list = idx
      self.options = options
      Process.__init__(self, *args, **kwargs)

   def run(self):
      plot_list = []
      for n in range(len(self.fig_idx_list)):
         plot = plt_window(self.fig_idx_list[n],self.options)
         plot_list.append(plot)
      while(True):
         try:
            if self.connec.poll(0.01) == False:
               for n in range(len(self.fig_idx_list)):
                  plot_list[n].refresh()
            else:
               data = self.connec.recv()
               idx = int(data[0])
               plot_list[self.fig_idx_list.index(idx)].vis(data[1:])
         except:
            pass

class plt_window():
   def __init__(self, idx, options):
      print "initializing plt_window with idx ",idx
      print options
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
      self.average = False#options.average
      self.display = options.display
      self.x = 50
      self.y = 50
      self.dx = 50
      self.dy = 50
      self.sp0_acc = np.array(0)
      self.times = 0
   def vis(self,data):
      self.times += 1
      if self.display == True:
         #print "len: " + str(len(data))
         plt.figure(self.fig_idx)
         if self.fft == True:
            if self.len_data != len(data):
               self.len_data = len(data)
               x = np.arange(0,1,1.0/self.len_data)
               x = x*(self.freq/2.0)
               plt.clf()
               self.line, = plt.plot(x,x)
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
               plt.ylim(0,1)
         if self.fft == True:
            sp0 = data#fft(data)
         else:
            sp0 = modulo(data[0:L])# 20*np.log10(modulo(data[0:L])) #
            for n in range(len(sp0)):
               if sp0[n] < -140:
                  sp0[n] = -150
         print self.fig_idx," signal level: ",max(sp0[10:-10]),"dBm"
         #print "len: " + str(len(sp0))
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
         self.active = 2;
      if self.save == True:
         raw_filename = self.output_folder + "input_" + str(self.fig_idx) + "_" + str(self.times-1) + ".bin"
         raw_file = open(raw_filename, "wb")
         raw_file.write(data)
         raw_file.close()
      plt.pause(0.01)

   def close(self):
      if self.active > 0:
         plt.figure(self.fig_idx)
         plt.close()
         self.active = 0;
         self.len_data = 0

   def refresh(self):
      if self.active == 2:
         plt.figure(self.fig_idx)
         plt.pause(0.01)

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



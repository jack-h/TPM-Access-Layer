import time
from multiprocessing import Process, Pipe

import numpy as np
import matplotlib.pyplot as plt

from display.visual import plt_window


class DataStreamProcess(Process):
    def __init__(self, connec, *args, **kwargs):
        self.connec = connec
        Process.__init__(self, *args, **kwargs)

    def run(self):
        random_gen = np.random.mtrand.RandomState(seed=127260)
        for _ in range(80):
            time.sleep(1)
            new_pt = [random_gen.uniform(-1., 1., size=256),random_gen.uniform(-1., 1., size=256)]
            self.connec.send(new_pt)
           

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
           
def main():
    conn1, conn2  = Pipe()
    data_stream = DataStreamProcess(conn1)
    data_stream.start()
    
    plt.ion()
    plot = []
    for n in range(8):
      plot.append(plt_window(n))
   
    pt = None
    while True:
        if conn2.poll(0.1) == True:
            new_pt = conn2.recv()
            pt = new_pt
            if pt is not None:
                for n in range(8):
                  plot[n].calc(pt[0])                  
        else:
            plt.pause(0.01)

    plt.title("Terminated.")
    plt.draw()
    plt.show(block=True)

if __name__ == '__main__':
    main()
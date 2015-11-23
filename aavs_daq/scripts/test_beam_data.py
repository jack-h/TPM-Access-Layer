from matplotlib import pyplot as plt
import numpy as np
import struct
import pylab
import sys

ntile  = 1
nchans = 512
npol   = 2

if __name__ == "__main__":
   # if len(sys.argv) < 2:
   #     print "Need file as input argument"

#    fp = open(sys.argv[1])

    fp = open("/home/lessju/Code/AAVS/aavs_daq/src/build/beam_output.dat", "rb")
    data = fp.read()
    nsamp = len(data) / (nchans * npol * 2)
    print nsamp
    data = np.array(struct.unpack(len(data) * 'b', data))

    data = data[::2] + data[1::2] * 1j

    print data

    data = np.reshape(data, (npol, nsamp, nchans))

    for i in range(nsamp):
        plt.plot(np.abs(data[0,i,:]))
    plt.show()
    


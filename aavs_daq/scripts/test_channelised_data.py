from matplotlib import pyplot as plt
import numpy as np
import struct
import pylab
import sys

nstation = 1
ntile    = 1
nchans   = 512
nant     = 16
npol     = 2

if __name__ == "__main__":
   # if len(sys.argv) < 2:
   #     print "Need file as input argument"

#    fp = open(sys.argv[1])

    fp = open("/home/lessju/Code/AAVS/aavs_daq/src/build/channel_output.dat", "rb")
    data = fp.read()
    data = np.array(struct.unpack(len(data) * 'b', data))
    data = data[::2] + data[1::2] * 1j	
    nsamp = len(data) / (nstation * ntile * nant * nchans * npol)
    data = np.reshape(data, (nstation, ntile, nchans, nsamp, nant, npol))

    print data[0,0,100,:,1,1]

    for i in range(nant):
        plt.figure()
        plt.imshow(np.abs(data[0,0,:,:,i,1]), aspect='auto')
    plt.show()

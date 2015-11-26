from matplotlib import pyplot as plt
import numpy as np
import struct
import pylab
import sys

nstation = 1
ntile    = 1
nchans   = 1
nant     = 16
npol     = 2

if __name__ == "__main__":
   # if len(sys.argv) < 2:
   #     print "Need file as input argument"

#    fp = open(sys.argv[1])

    fp = open("/home/lessju/Code/TPM-Access-Layer/aavs_daq/src/build/channel_output.dat", "rb")

    # Read in chunks of 67108864 bytes
    while True:
        data = fp.read(65536 * 128)
        data = np.array(struct.unpack(len(data) * 'b', data))
        data = data[::2] + data[1::2] * 1j	
        nsamp = len(data) / (nstation * ntile * nant * nchans * npol)
        data = np.reshape(data, (nstation, ntile, nchans, nsamp, nant, npol))

        print data[0,0,0,0,:,0]
        print data[0,0,0,1,:,0]
        print data[0,0,0,2,:,0]
        print data[0,0,0,3,:,0]
        print data[0,0,0,4,:,0]

#        for i in range(nant):
#            plt.figure()
#            plt.imshow(np.abs(data[0,0,:,:,i,1]), aspect='auto')
#        plt.show()
        plt.imshow(np.abs(data[0,0,0,:,:,0]), aspect='auto')
        plt.show()

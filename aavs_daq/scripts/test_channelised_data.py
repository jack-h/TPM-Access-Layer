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

    fp = open("/home/lessju/Code/TPM-Access-Layer/aavs_daq/src/build/channel_output.dat", "rb")

    # Read in chunks of 67108864 bytes
    data = fp.read()
    data = np.array(struct.unpack(len(data) * 'b', data))
    data = data[::2] + data[1::2] * 1j	
    nsamp = len(data) / (nstation * ntile * nant * nchans * npol)
    data = np.reshape(data, (nstation, ntile, nchans, nsamp, nant, npol))

    for i in range(nant):
        plt.figure()
        plt.imshow(np.abs(data[0,0,:,:,i,0]), aspect='auto')
        plt.colorbar()
    plt.show()

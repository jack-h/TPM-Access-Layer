from matplotlib import pyplot as plt
import numpy as np
import struct
import pylab
import sys

nstation = 1
ntile    = 1
nants    = 16
npol     = 2

if __name__ == "__main__":
   # if len(sys.argv) < 2:
   #     print "Need file as input argument"

#    fp = open(sys.argv[1])

    fp = open("/home/lessju/Code/TPM-Access-Layer/aavs_daq/src/build/antenna_output.dat", "rb")
    data = fp.read()
    nsamp = len(data) / (nstation * ntile * nants * npol)
    print nsamp, len(data)
    data = np.array(struct.unpack(len(data) * 'B', data))
    data = np.reshape(data, (nstation, ntile, nants, nsamp, npol))

    fig = pylab.figure(figsize=(8*3, 6*3))
    ax1 = fig.add_subplot(411)
    ax1.plot(data[0,0,10,:,0])

    ax1 = fig.add_subplot(412)
    ax1.plot(data[0,0,10,:,1])

    ax1 = fig.add_subplot(413)
    ax1.plot(data[0,0,12,:,0])

    ax1 = fig.add_subplot(414)
    ax1.plot(data[0,0,12,:,1])
    # plt.plot(data)
    plt.show()

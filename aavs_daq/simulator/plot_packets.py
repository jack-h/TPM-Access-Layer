from matplotlib import pyplot as plt
import numpy as np
import struct
import sys
import os

nchans = 1
nants  = 16
npol   = 2

if __name__ == "__main__":

    # Check if filename available
    if len(sys.argv) < 2:
        print "Filename required"
        exit(-1)

    # Check if filename exist
    if not os.path.exists(sys.argv[1]):
        print "Invalid file: " + sys.argv[1]

    # Open and process file
    ntime = 0
    with open(sys.argv[1], 'rb') as f:
        data = f.read()
        data = np.array(struct.unpack('H' * (len(data) / 2), data))
        ntime = len(data) / (nchans * nants * npol)
        data = np.reshape(data, (ntime, nants, npol))

    print "Number of time samples: %d" % ntime
    plt.imshow(data[:,:,0], aspect='auto')
    plt.xlabel('ants')
    plt.ylabel('time')
    plt.colorbar()
    plt.show()


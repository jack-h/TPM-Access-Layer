# Manually add module file for now
from time import sleep
import sys
sys.path.append("../python")

from tpm import *

tpm = TPM(ip="10.62.14.234", port=15000)
ID = tpm.id

ret = tpm.loadFirmwareBlocking(ID, Device.FPGA_1, "/home/lessju/MemoryMap.xml")
if ret == Error.Failure:
    print "Load firmware blocking failed"
    exit(-1)

registers = tpm.getRegisterList(ID)
print tpm['register1']
tpm['register'] = 69

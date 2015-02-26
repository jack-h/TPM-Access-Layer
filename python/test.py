from time import sleep
from tpm import *

tpm = TPM()

ID = tpm.connect("10.62.14.234", 15000)
if ID == Error.Failure:
    print "Connect failed"
    exit(-1)

ret = tpm.loadFirmwareBlocking(ID, Device.FPGA_1, "/home/lessju/MemoryMap.xml")
if ret == Error.Failure:
    print "Load firmware blocking failed"
    exit(-1)

registers = tpm.getRegisterList(ID)
curr_key = registers.keys()[0]
print curr_key

val = tpm.getRegisterValue(ID, registers[curr_key]['device'], curr_key)
print val.value, val.error.value

tpm.setRegisterValue(ID, registers[curr_key]['device'], curr_key, 69)


sleep(220)

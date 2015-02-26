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

val = tpm.getRegisterValue(ID, registers[0]['device'], registers[0]['name'])
print val.value, val.error.value

tpm.setRegisterValue(ID, registers[0]['device'], registers[0]['name'], 69)


sleep(220)

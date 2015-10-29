import sys
sys.path.append("../")
import config.manager as config_man

from bsp.tpm import *
from mytest.c2c_test import *

design = "tpm_test"
config = config_man.get_config_from_file("../config/config.txt",design,True)

inst = TPM(ip=config['FPGA_IP'],port=config['UDP_PORT'],board="kcu105")
#inst.load_firmware_blocking(Device.FPGA_1,config['XML_FILE'])
inst.load_firmware_blocking(Device.FPGA_1)

print "Print list of registers:"
inst.list_register_names()
print "-----------------------------------------------------------------"

print "Print list of registers:"
print inst
print "-----------------------------------------------------------------"

print "Print number of registers:"
print "len is",len(inst)
print 

print "Read a register:"
print hex(inst["tpm_test.regfile.rev"])
print 

print "Read a register:"
print hex(inst["tpm_test.regfile"])
print 

print "Search a register by name and display information:"
inst.find_register("rev",True)
print 

print "Read a register obtaining its address from a search:"
print hex(inst[inst.find_register_names("rev",False)[0]])
print 

print "Read from a specific address:"
print hex(inst[0x0])
print 

# print "Write a register:"
# inst['tpm_test.regfile.size2048b'] = 0x1234
# print hex(inst['tpm_test.regfile.size2048b'])
# print

# print "Write a multiple registers:"
# inst['tpm_test.regfile.size2048b'] = [0x5678] * 16
# print hex(inst['tpm_test.regfile.size2048b'])
# print

# print "Write a block at specific offset:"
# inst.write_register('tpm_test.regfile.size2048b',0x12345678,offset=0x10)
# print inst.read_register('tpm_test.regfile.size2048b',n=32,offset=0)
# print

# print "BITFIELD"
# print "Reset entire register:"
# inst['tpm_test.jesd204_if.regfile_ctrl'] = 0
# print "Write bitfield 0:"
# inst['tpm_test.jesd204_if.regfile_ctrl.reset_n'] = 1
# print "Read register:"
# print inst['tpm_test.jesd204_if.regfile_ctrl'] 
# print "Write bitfield 1:"
# inst['tpm_test.jesd204_if.regfile_ctrl.ext_trig_en'] = 1
# print "Read register:"
# print inst['tpm_test.jesd204_if.regfile_ctrl']
# print "Read bitfield 0:"
# print inst['tpm_test.jesd204_if.regfile_ctrl.reset_n']
# print "Read bitfield 1:"
# print inst['tpm_test.jesd204_if.regfile_ctrl.ext_trig_en']
# print

print "Read SPI devices:"
print inst.read_device("pll",0xC)
print inst.read_device("adc0",0xC)
print inst.read_device("adc1",0xC)

#c2c_test = c2cTest(inst)
#c2c_test.start(1000)

inst.disconnect()

inst2 = TPM(ip=config['FPGA_IP'])
inst2.load_firmware_blocking(Device.FPGA_1,config['XML_FILE'])
inst2.bsp.acq_start(700,8,[0,1],False)
inst2.disconnect()


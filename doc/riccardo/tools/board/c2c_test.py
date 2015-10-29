import sys
sys.path.append("../")
import config.manager as config_man
from bsp.tpm import *
from mytest.c2c_test import *

config = config_man.get_config_from_file("../config/config.txt","tpm_test",True)
inst = TPM(ip=config['FPGA_IP'],port=config['UDP_PORT'],board="kcu105",timeout=5)
inst.load_firmware_blocking(Device.FPGA_1,config['XML_FILE'])

c2c_test = c2cTest(inst)
c2c_test.start(1000)

inst.disconnect()



import sys
import time
sys.path.append("../")
import config.manager as config_man
from bsp.tpm import *
from optparse import OptionParser

design = "tpm_test"
config = config_man.get_config_from_file("../config/config.txt",design,True)

XML_FILE = config['XML_FILE']
FPGA_IP  = config['FPGA_IP']

parser = OptionParser()
parser.add_option("-f", "--freq", 
                  dest="frequency", 
                  default = 700,
                  help="sampling frequency")
parser.add_option("-i", "--input", 
                  dest="input_list", 
                  default = "0,1",
                  help="input list")
parser.add_option("--ada", 
                  action="store_true",
                  dest="ada", 
                  default = False,
                  help="Enable ADA")
parser.add_option("-t", "--tag", 
                  dest="tag_string", 
                  default = "No TAG!",
                  help="TAG RAM value, 4096 bytes maximum size!")
                  
(options, args) = parser.parse_args()

tpm_inst = TPM(ip=FPGA_IP)
tpm_inst.load_firmware_blocking(Device.FPGA_1,XML_FILE)

bit = 8
freq = int(options.frequency)
ada = options.ada
input_list = [int(i) for i in (options.input_list).split(",")]

tpm_inst.bsp.write_tag_ram(options.tag_string)

print "------------------- Frequency " + str(freq) + " MHz, " + str(bit) + " bit ------------------"
tpm_inst.bsp.acq_start(freq,bit,input_list,ada)
tpm_inst.disconnect()
sys.exit()

   

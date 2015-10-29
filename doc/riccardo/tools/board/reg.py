import netproto.rmp as rmp
import sys
import socket
import struct
import binascii
sys.path.append("../")
import config.manager as config_man
from bsp.tpm import *
import lxml.etree as ET
from optparse import OptionParser

def format_num(num):
		"""Format a number according to given places.  Adds commas, etc. Will truncate floats into ints!"""
		#try:
		#	inum = int(num)
		#	return locale.format("%.*f", (0, inum), True)
		#except (ValueError, TypeError):
		return str(num)
      
def get_max_width(table1, index1):
   """Get the maximum width of the given column index"""
   return max([len(format(row1[index1])) for row1 in table1])

def pprint_table(table):
   #"""Prints out a table of data, padded for alignment
   #@param table: The table to print. A list of lists.
   #Each row must have the same number of columns. """

   col_paddings = []

   for i in range(len(table[0])):
      col_paddings.append(get_max_width(table, i))

   for row in table:
      #print row
      # left col
      print row[0].ljust(col_paddings[0] + 1),
      # rest of the cols
      for i in range(1, len(row)):
         col = format_num(row[i]).rjust(col_paddings[i] + 2)
         print  col,
      print 

if __name__ == "__main__":  
   parser = OptionParser()
   parser.add_option("-s", "--search", 
                     dest="search", 
                     default = "*",
                     help="Search the register map")
   parser.add_option("-n", "--num", 
                     dest="num", 
                     default = 1,
                     help="Number of 32 bits words")
   parser.add_option("--spi", 
                     dest="spi", 
                     default = "",
                     help="Access SPI device")
   parser.add_option("-d", "--design", 
                     dest="design", 
                     default = "tpm_test",
                     help="Number of 32 bits words")
   parser.add_option("-x", "--get_xml", 
                     action = "store_true",
                     dest="get_xml", 
                     default = False,
                     help="Download XML memory map from connected board")
   parser.add_option("-e", "--get_extended_info", 
                     action = "store_true",
                     dest="get_info", 
                     default = False,
                     help="Download XML memory map from connected board")
   parser.add_option("-m", "--sim_mode", 
                     dest="sim_mode", 
                     default = "",
                     help="Simulation mode. 0 forces network mode, any other value forces simulation mode. I this parameter is not specified the mode is retrieved from configuration file.")
      
   (options, args) = parser.parse_args()
   
   config = config_man.get_config_from_file(config_file="../config/config.txt",design=options.design,display=False,check=True,sim=options.sim_mode)
   
   if options.search != "*":
      tree = ET.parse(config['XML_FILE'])
      root = tree.getroot()
      reg_list = []
      for node in root.iter('node'):
         id = node.get("absolute_id")
         if id != None:
            if id.find(options.search) != -1:
               reg_list.append([id,"0x" + node.get("absolute_offset"),node.get("mask")])
      if reg_list != []:
         pprint_table(reg_list)
         sys.exit()
      else:
         print "Not found!"
         sys.exit()
   else:
      
      if options.get_xml == True:
         tpm_inst = TPM(ip=config['FPGA_IP'],port=config['UDP_PORT'],timeout=config['UDP_TIMEOUT'])
         print tpm_inst.get_xml_from_board(0x8)
         tpm_inst.disconnect()
         sys.exit()
      elif options.get_info == True:
         tpm_inst = TPM(ip=config['FPGA_IP'],port=config['UDP_PORT'],timeout=config['UDP_TIMEOUT'])
         print tpm_inst.get_extended_info(0x10)
         tpm_inst.disconnect()
         sys.exit()
      else:
         tpm_inst = TPM(ip=config['FPGA_IP'],port=config['UDP_PORT'],timeout=config['UDP_TIMEOUT'],board="KCU1")
         tpm_inst.load_firmware_blocking(Device.FPGA_1,config['XML_FILE'])
         if options.spi != "":
            if len(args) == 1:
               dat = tpm_inst.read_device(options.spi,int(args[0],16))
               print hex(dat)
            elif len(args) == 2:
               str_list = args[1].split(".")
               dat_list = []
               for s in str_list:
                  dat_list.append(int(s,16))
                  tpm_inst.write_device(options.spi,int(args[0],16),dat_list[0])
            else:
               "input error!"
         else:   
            if len(args) == 1:
               dat = tpm_inst.read_register(int(args[0],16),n=int(options.num))
               if type(dat) == list:
                  for d in dat:
                     print hex(d)
               else:
                  print hex(dat)
            elif len(args) == 2:
               str_list = args[1].split(".")
               dat_list = []
               for s in str_list:
                  dat_list.append(int(s,16))
               tpm_inst.write_register(int(args[0],16),dat_list)
            else:
               "input error!"
         rmp.CloseNetwork()
   
   
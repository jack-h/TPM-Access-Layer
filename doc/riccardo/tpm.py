import re
import sys
import netproto.rmp as rmp
import lxml.etree as ET
from bsp.tpm_bsp import TPM_BSP
from enum import Enum
from pyfabil.base.definitions import *
import zlib
import binascii

def hexstring2ascii(hexstring, xor=0):
    """ Convert a hexstring to an ASCII-String. If you like to XOR it, give the
        xor value as an integer. If not, leave it blank """
    ascii = ""
    for i in xrange(0, len(hexstring)/2):
        ascii = ascii + chr(int(hexstring[2*i:2*i+2],16)^xor) 
    return ascii

def format_num(num):
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

def filter_list_by_level(reg_name_list,reg_name):
   filter_list = []
   level_num = len(reg_name.split("."))
   for reg in reg_name_list:
      if len(reg.split(".")) == level_num and reg != reg_name:
         filter_list.append(reg)
   return filter_list
   
def get_shift_from_mask(mask):
   mask = int(mask,16)
   shift = 0
   while(mask & 0x1 != 1):
      shift += 1
      mask = mask >> 1
   return shift
   
class TPM():
   def __init__(self, **kwargs):
      self.reg_list = []
      self.reg_dict = {}
      self.reg_sel_list = []
      self.reg_sel_dict = {}
      self.board = ""
      self.state = "Created"
      self.extended_info = ""
      if not 'ip' in kwargs.keys():
         print "Error! An IP address must be specified!"
         sys.exit()
      else:
         ip   = kwargs['ip']
      if not 'port' in kwargs.keys():
         print "Assuming UDP port 10000"
         port = 10000
      else:
         port = int(kwargs['port']) 
      if not 'timeout' in kwargs.keys():
         print "Assuming UDP socket timeout 1 second"
         timeout = 1
      else:      
         timeout = int(kwargs['timeout'])
      rmp.InitNetwork("",ip,port,timeout)
      self.state = "Connected"
      if 'board_reg' in kwargs.keys():
         raise NameError("board_reg is not supported, board name must be retrived from extended info string!")
      elif 'board' in kwargs.keys():
         self.board = kwargs['board']
      else:
         self.board = self.get_board(0x10)
      #print      
      #print "Using board", self.board
      self.bsp = TPM_BSP(self.board)
      
   def __getitem__(self, key):
      """ Override __getitem__, return value from board """
      return self.read_register(key)
      
   def __setitem__(self, key, value):
      """ Override __setitem__, set value on board"""
      self.write_register(key,value)
      return
      
   def __len__(self):
      """ Override __len__, return number of registers """
      self.checkLoad()
      return len(self.reg_dict.keys())
      
   def __repr__(self):
      self.list_register_names()
      return ""
         
   def get_xml_from_board(self, xml_map_offset):
      # read the offset where the zipped XML is stored
      xml_off = self.read_register(xml_map_offset)
      # first 4 bytes are the zipped XML file length in byte
      xml_len = self.read_register(xml_off)
      # read the zipped XML, this should be optimized using larger accesses
      xml_hex_str = ""
      byte_to_read = xml_len
      byte_offset = xml_off + 4
      req_len = 256 
      while(True):
         if byte_to_read < req_len*4:
            rd = self.read_register(byte_offset,n=byte_to_read/4+1)
            byte_to_read = 0
         else:
            rd = self.read_register(byte_offset,n=req_len)
            byte_to_read -= req_len*4
            byte_offset += req_len*4 
         if type(rd) == list:
            for n in rd:
               xml_hex_str += format(n,'08x')
         else:
            print rd
            xml_hex_str += format(rd,'08x')
         if byte_to_read == 0:
            break
      #for n in range(xml_len/(8)+1):
      #   xml_hex_str += format(self.read_register(xml_off+4*(n+1)),'08x')
      # decompress zipped XML
      xml = zlib.decompress(binascii.unhexlify(xml_hex_str[:2*xml_len]))
      # this string contains the decompressed XML
      return xml
      
   def get_extended_info(self, ext_info_offset=0x10):
      # read the offset where the extended info string is stored
      ext_off = self.read_register(ext_info_offset)
      # first 4 bytes are the zipped XML file length in byte
      ext_len = self.read_register(ext_off)
      # read the zipped XML, this should be optimized using larger accesses
      hex_str = ""
      byte_to_read = ext_len
      byte_offset = ext_off + 4
      req_len = 256 
      while(True):
         if byte_to_read < req_len*4:
            rd = self.read_register(byte_offset,n=byte_to_read/4+1)
            byte_to_read = 0
         else:
            rd = self.read_register(byte_offset,n=req_len)
            byte_to_read -= req_len*4
            byte_offset += req_len*4 
         if type(rd) == list:
            for n in rd:
               hex_str += format(n,'08x')
         else:
            print rd
            hex_str += format(rd,'08x')
         if byte_to_read == 0:
            break
      info = binascii.unhexlify(hex_str[:2*ext_len])
      #print info
      return info
      
   def get_board(self, ext_info_offset=0x10):
      self.extended_info = self.get_extended_info(ext_info_offset=0x10)
      my_regex = r"" + re.escape("BOARD: ") + r"\s*(\w+)"
      m = re.search(my_regex,self.extended_info)
      if m != None:
         return m.group(1)
      else:
         print field + " doesn't exist" 
         sys.exit(1)
      
   def load_firmware_blocking(self, Device, path_to_xml_file="", xml_map_offset=0x8):
   
      if path_to_xml_file == "":
         xml_str  = self.get_xml_from_board(xml_map_offset)
         root = ET.fromstring(xml_str)
      else:
         tree = ET.parse(path_to_xml_file)
         root = tree.getroot()

      for node in root.iter('node'):
         if node.get("absolute_id") != None:
            # reg = {
               # 'name'        : '%s.%s' % (names[dev], registers[i].name),
               # 'address'     : registers[i].address,
               # 'type'        : RegisterType(registers[i].type),
               # 'device'      : dev,
               # 'permission'  : Permission(registers[i].permission),
               # 'size'        : registers[i].size,
               # 'bitmask'     : registers[i].bitmask,
               # 'bits'        : registers[i].bits,
               # 'value'       : registers[i].value,
               # 'description' : registers[i].description
            # }

            local_dict = {}
            local_dict['name'] = None
            local_dict['address'] = "None"
            local_dict['bitmask'] = "None"
            local_dict['size'] = "None"
            local_dict['permission'] = "None"
            local_dict['description'] = "None"
            
            if node.get("absolute_id") != None:
               local_dict['name'] = node.get("absolute_id")
            if node.get("absolute_offset") != None:
               local_dict['address'] = node.get("absolute_offset")
            if node.get("mask") != None:
               local_dict['bitmask'] = node.get("mask")
            if node.get("size") != None:
               local_dict['size'] = node.get("size")
            if node.get("permission") != None:
               local_dict['permission'] = node.get("permission")
            if node.get("description") != None:
               local_dict['description'] = node.get("description")

            self.reg_list.append(local_dict)
            self.reg_dict[node.get("absolute_id")] = local_dict
            
      for reg in self.reg_list:
         if reg['name'] != None and reg['bitmask'] != "None" and reg['size'] != "None":
            self.reg_sel_list.append(reg)
            self.reg_sel_dict[reg['name'] ] = reg
      for register in self.reg_dict.keys():
         if register != None:
            reg_str = "."
            reg_str = reg_str.join(register.split(".")[:-1])
            regs = self.find_register_names(reg_str,display=False)
            regs = filter_list_by_level(regs,register)
            is_bitfield = 0
            for reg in regs:
               if self.reg_dict[reg]['address'] == self.reg_dict[register]['address']:
                  is_bitfield = 1
            self.reg_dict[register]['is_bitfield'] = is_bitfield
      self.bsp.set_spi_if_base_address(0x20000000)
      
   def checkLoad(self):
      if self.reg_list == []:
         print "Registers not loaded!"
         sys.exit()
      if self.state != "Connected":
         print "Board not connected!"
         sys.exit()
      
   def list_register_names(self):
      self.checkLoad()
      lines = []
      for reg in self.reg_list:
         if reg['name'] != None:
            if lines == []:
               lines.append(["Name","Address","Bitmask","Size"])
            lines.append([reg['name'],"0x" + reg['address'],reg['bitmask'],reg['size']])
      if lines != []:
         pprint_table(lines)
               
   def find_register(self, register_name, display = False):
      """ Return register information for provided search string
         :param register_name: Regular expression to search against
         :param display: True to output result to console
         :return: List of found registers
         """
      # Run checks
      self.checkLoad()
      # Go through all registers and store the name of registers
      # which generate a match
      matches = []
      for reg in self.reg_list:
         if reg['name'] != None:
            if re.search(register_name, reg['name']) != None:
               matches.append(reg)
      # Display to screen if required
      if display:
         lines = []
         for m in matches:
            if lines == []:
               lines.append(["Name","Address","Mask","Size"])
            print m
            lines.append([m['name'],"0x" + m['address'],m['bitmask'],m['size']])
         if lines != []:
            pprint_table(lines)
      # Return matches
      return matches
      
   def find_register_names(self, register_name, display = False):
      found_reg = self.find_register(register_name, False)
      name_list = []
      for n in found_reg:
         name_list.append(n['name'])
         if display == True:
            print n['name']
      return name_list
   
   def read_register(self, register, n = 1, offset = 0, device = None):
      """ Get register value
      :param register: Register name
      :param n: Number of words to read
      :param offset: Memory address offset to read from
      :param device: Device/node can be explicitly specified
      :return: Values
      """
      
      if type(register) == int:
         return rmp.rd32(register+offset,n)
      else:
         self.checkLoad()
         if not register in self.reg_dict.keys():
            print register
            print "Error: register " + register + " not found!"
         else:
            #check if it is a bitfield and other bitfields are present
            is_bitfield = self.reg_dict[register]['is_bitfield']
                  
            if is_bitfield == 0:
               return rmp.rd32(int(self.reg_dict[register]['address'],16)+offset,n)
            else:
               rd = rmp.rd32(int(self.reg_dict[register]['address'],16)+offset,1)
               rd = (rd & int(self.reg_dict[register]['bitmask'],16)) >> get_shift_from_mask(self.reg_dict[register]['bitmask'])
               return rd
   
   def write_register(self, register, values, offset = 0, device = None):
      """ Set register value
      :param register: Register name
      :param values: Values to write
      :param offset: Memory address offset to write to
      :param device: Device/node can be explicitly specified
      """
      if type(register) == int:
         rmp.wr32(register+offset,values)
      else:
         self.checkLoad()
         if not register in self.reg_dict.keys():
            print "Error: register " + register + " not found!"
         else:
            #check if it is a bitfield and other bitfields are present
            is_bitfield = self.reg_dict[register]['is_bitfield']
            
            if is_bitfield == 0:
               rmp.wr32(int(self.reg_dict[register]['address'],16)+offset,values)
            else:
               rd = rmp.rd32(int(self.reg_dict[register]['address'],16)+offset,1)
               if type(values) == list:
                  wdat = values[0]
               else:
                  wdat = values
               wdat = wdat << get_shift_from_mask(self.reg_dict[register]['bitmask'])
               rmp.wr32(int(self.reg_dict[register]['address'],16)+offset,wdat | rd)
            return

   def read_device(self, device, address):
      if device == "pll":
         return self.bsp.rd_pll(address)
      elif device.find("adc") != None:
         try:
            idx = int(device.replace("adc",""))
            return self.bsp.rd_adc(int(device.replace("adc","")),address)
         except:
            "SPI device not found:", device
            sys.exit()
      else:
         "Unrecognised SPI device:", device
         sys.exit()
         
   def write_device(self, device, address, value):
      if device == "pll":
         self.bsp.wr_pll(address,value)
      elif device.find("adc") != None:
         try:
            idx = int(device.replace("adc",""))
            self.bsp.wr_adc(int(device.replace("adc","")),value)
         except:
            "SPI device not found:", device
            sys.exit()
      else:
         "Unrecognised SPI device:", device
         sys.exit()

   # def read_address
   # def write_adress
      
   def disconnect(self):
      rmp.CloseNetwork()
      self.state = "Unconnected"

      
         

      
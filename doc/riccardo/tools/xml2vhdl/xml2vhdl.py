#TODO:
#  - reset record value
#  - error checking
#  - documentation
#  - regression test
import re
import os
import sys
import copy
import math
import string
import textwrap
import numpy as np
import xml.dom.minidom
import xml.etree.ElementTree as ET
from optparse import OptionParser

version = [
           1.9  ,"corrected single char input from user",
           1.8  ,"print BRAM check, check of BRAM init file in VHDL",
           1.7  ,"hw_dp_ram_init_file_check attribute for skipping ram init file existence check",
           1.6  ,"converted sys.exit() to sys.exit(1)",
           1.5  ,"dp_ram initilaization from bin/hex file TBT",
           1.4  ,"dp_ram implementation, simple test bench creation, history log, commented \"hw_ignore\" attribute,\
                 recursive iteration on links, command line parameters, generic reset values, \
                 templates modification for consistent line spacing, rearranged template files read/write",  
           1.3  ,"ipb mapping correction, substituted \".\" with \"_\"", 
           1.2  ,"newline character management",
           1.1  ,"bus library reference correction", 
           1.0  ,"first release",
          ]
          
vhdl_reserved_words = [ "abs","access","after","alias","all","and","architecture","array","assert","attribute","begin","block","body","buffer","bus","case","component",
                        "configuration","constant","disconnect","downto","else","elsif","end","entity","exit","file","for","function","generate","generic","group","guarded",
                        "if","impure","in","inertial","inout","is","label","library","linkage","literal","loop","map","mod","nand","new","next","nor","not","null","of","on","open",
                        "or","others","out","package","port","postponed","procedure","process","pure","range","record","register","reject","return","rol","ror","select","severity",
                        "signal","shared","sla","sli","sra","srl","subtype","then","to","transport","type","unaffected","units","until","use","variable","wait","when","while",
                        "with","xnor","xor"]

allowed_attribute_value = {}
allowed_attribute_value['link'] = ["string"]
allowed_attribute_value['address'] = ["hex_value"]
allowed_attribute_value['mask'] = ["hex_value"]
allowed_attribute_value['permission'] = ['r','w','rw']
allowed_attribute_value['hw_permission'] = ['w','we','no']
allowed_attribute_value['hw_rst'] = ['no','hex_value','vhdl_name']
allowed_attribute_value['hw_prio'] = ['bus','logic']
allowed_attribute_value['array'] = ["int_value"]
allowed_attribute_value['array_offset'] = ["hex_value"]
allowed_attribute_value['size'] = ["int_value"]
allowed_attribute_value['description'] = ["string"]
allowed_attribute_value['hw_dp_ram'] = ['yes','no']
allowed_attribute_value['hw_dp_ram_bus_lat'] = ['1','2']
allowed_attribute_value['hw_dp_ram_logic_lat'] = ['1','2']
allowed_attribute_value['hw_dp_ram_width'] = ['1 to 32']
allowed_attribute_value['hw_dp_ram_init_file'] = ["string"]
allowed_attribute_value['hw_dp_ram_init_file_check'] = ['yes','no']
allowed_attribute_value['hw_dp_ram_init_file_format'] = ["hex","bin"]
#allowed_attribute_value['hw_ignore'] = ['yes','no']

default_attribute_value = {}
default_attribute_value['link'] = "\"\""
default_attribute_value['address'] = "0x0"
default_attribute_value['mask'] = "No default value. It must be specified"
default_attribute_value['permission'] = "'rw'"
default_attribute_value['hw_permission'] = "no"
default_attribute_value['hw_rst'] = "0x0"
default_attribute_value['hw_prio'] = "logic"
default_attribute_value['array'] = "Must be specified if this attribute is used"
default_attribute_value['array_offset'] = "Must be specified if 'array' attribute is used"
default_attribute_value['size'] = "1"
default_attribute_value['description'] = "\"\""
default_attribute_value['hw_dp_ram'] = "no"
default_attribute_value['hw_dp_ram_bus_lat'] = "1"
default_attribute_value['hw_dp_ram_logic_lat'] = "1"
default_attribute_value['hw_dp_ram_width'] = "32"
default_attribute_value['hw_dp_ram_init_file'] = "\"\""
default_attribute_value['hw_dp_ram_init_file_check'] = "yes"
default_attribute_value['hw_dp_ram_init_file_format'] = "hex"

attribute_description = {}
attribute_description['link'] = "It links the specified XML file to the current node."
attribute_description['address'] = "Current node relative offset. The absolute offset is calculated walking from the current node \
                                    to the root node and accumulating 'address' of each encountered node."
attribute_description['mask'] = "It specifies the number of bits and their position in a register. This attribute must be specified \
                                 for nodes that are registers or bit-field."
attribute_description['permission'] = "It controls the access type from the bus side."
attribute_description['hw_permission'] = "It controls the access type from logic side. When 'w', the logic continuously write into \
                                          the registers. When 'we', the logic writes to the register by asserting a write enable.\
                                          When 'no' the logic cannot write to the register. The logic can always read the register"
attribute_description['hw_rst'] = "It specifies the reset value of the register. When 'no' the register is not reset. In case the node is \
                                   a bit-field and its 'hw_rst' value is not specified, the node inherits 'hw_rst' from its parent. When the \
                                   specified value is a name, the script generates a a VHDL generic that is used to assign the reset value to \
                                   corresponding register."
attribute_description['hw_prio'] = "It controls the priority between logic and bus when a simultaneous write (at the same clock edge) occurs."
attribute_description['array'] = "It replicates the underlying node structure by the specified number of times. The offset between each array element \
                                  is specified by attribute 'array_offset'"
attribute_description['array_offset'] = "It specifies the offset between each element in the array."
attribute_description['size'] = "It specifies the node size in terms of 32 bits words. A size greater than 1 implies the instantiation of an\
                                independent ipb bus that can be connected to a user supplied component or alternatively to an automatically generated dual port RAM \
                                when hw_dp_ram=\"yes\"."
attribute_description['description'] = "Node description"
attribute_description['hw_dp_ram'] = "When 'yes' it instantiates a dual port RAM using the related ipb bus in the generated top level."
attribute_description['hw_dp_ram_bus_lat'] = "Bus side read latency of instantiated dual port RAM"
attribute_description['hw_dp_ram_logic_lat'] = "User logic side read latency of instantiated dual port RAM"
attribute_description['hw_dp_ram_width'] = "RAM data width"
attribute_description['hw_dp_ram_init_file'] = "Initialize instantiated BRAM with supplied initialization file"
attribute_description['hw_dp_ram_init_file_check'] = "Check if linked initialization file exists"
attribute_description['hw_dp_ram_init_file_format'] = "Initialization file format. Supported formats are binary and hexadecimal.\
                                                         Each line in the initialization file corresponds to a memory location, the number\
                                                         of bits and of each initialization word must match the memory width."
#attribute_description['hw_ignore'] = "When 'yes' it disables VHDL generation for current node and all child nodes."

# global dictionary
global_dict = {}
key_table = {}
# number of nodes
node_num = 0

bus = "axi4lite"
bus_clock = "axi4lite_aclk"
bus_reset = "axi4lite_aresetn"
bus_reset_val = "0"

class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()

class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

#format an hexadecimal as 32 bit with leading 0's
def hex_format(input):
   return format(input,'08x')
   
#normalize a path name substituting back-slashes with slashes
def normalize_path(input):
   input = re.sub(r"\\","/",input)
   input = re.sub(r"/+","/",input)
   return input
   
#normalize a text substituting "\r\n" with "\n"
def normalize_template(input):
   input = re.sub(r"\r\n","\n",input)
   return input
 
#normalize ad create output sub-folder
def normalize_output_folder(input):
   output_folder = normalize_path(input)
   if output_folder != "":
      if not os.path.exists(output_folder):
         print "Folder \"" + output_folder + "\" doesn't exist! Press [Y | y] to create it, any other key to abort"
         key = _Getch()
         if key().lower() == "y":
            print "Creating \"" + output_folder + "\" folder" 
            os.makedirs(output_folder)
         else:
            print "Exiting..."
            sys.exit(1)
      output_folder += "/"
   return output_folder
   
#generate a list of files having ext extension contained in the path_list list of folder
def file_list_generate(path_list,ext):
    ret = []    
    for p in path_list:
        result = [os.path.join(dp, f) for dp, dn, fn in os.walk(normalize_path(p)) for f in fn if os.path.splitext(f)[1] == ext]  
        for n in result:
            ret.append(normalize_path(n))
    return ret
   
#read template file
def read_template_file(file_name):
   template_file = open(file_name, "rU")
   text = template_file.read()
   text = normalize_template(text)
   template_file.close()
   return text

#write VHDL output file
def write_vhdl_file(file_name,vhdl_output_folder,text):
   file_name = normalize_path(vhdl_output_folder + file_name) 
   print "Writing VHDL output file: \"" + file_name + "\""
   vhdl_file = open(file_name, "w")
   vhdl_file.write(text)
   vhdl_file.close()
   
#return the maximum length in a list of string
def get_max_len(name_list):
   length = 0
   for name in name_list:
      if length < len(name):
         length = len(name)
   return length
   
#add a blanks to after the string name, final string length is max_name_len
def add_space(name,max_name_len):
   target = max_name_len + 1;
   space_num = target - len(name)
   return " "*space_num
   
#format a string adding suitable number of blank characters
def str_format(name,len):
   return add_space(name,len-1) + name
   
#indent a block with tab_num tabs, the empty string is not indented
def indent(string,tab_num):
   stripped = ""
   tabs = "\t"*tab_num
   if string == "":
      return string
   if string[-1] == "\n":
      stripped = "\n"
      string = string[:-1]
   indented = tabs + string
   indented = indented.replace("\n","\n" + tabs)
   if stripped != "":
      indented += stripped
   return indented
   
#return maximum addressable_id length
def get_max_id_len(dict):
   length = 0
   for node_id in reverse_key_order(dict):
      str = dict[node_id]['addressable_id']
      str = re.sub(r"\|","",str)
      str = re.sub(r"/","",str)
      str = re.sub(r"\*","",str)
      str = re.sub(r"<<","_",str)
      str = re.sub(r">>","",str)
      if len(str) > length:
         length = len(str)
   return length
   
#return range from mask
def get_range_from_mask(mask):
   mask_int = int(mask,16)
   n = 0
   range_lo = -1
   range_hi = -1
   while(mask_int != 0):
      if (mask_int & 0x1) != 0:
         if range_lo == -1:
            range_lo = n
         else:
            range_hi = n
      mask_int /= 2
      n += 1
   return range_hi, range_lo
   
#return position of not-equal bit among addresses in add_list, returns -1 if there are not different bits
def dec_check_bit(add_list,bit):
   for b in reversed(range(0,bit)):
      for add0 in add_list: 
         for add1 in add_list:
            if add0[b] != add1[b]:
               return b
   return -1
   
def dec_get_last_bit(bit_path):
   bit_list = bit_path.split("_")
   ret = bit_list[len(bit_list)-1]
   ret = re.sub(r'v.*',"",ret)
   ret = int(ret)
   #print "get_last_bit input: " + str(ret)
   #print "get_last_bit output: " + bit_path
   if ret == -1:
      ret = 32
   return ret
  
def dec_route_add(tree_dict):
   done = 0
   #print tree_dict
   for path in tree_dict.keys():
      add_list = tree_dict[path]
      b = dec_check_bit(add_list,dec_get_last_bit(path))       
      if b > -1:
         list_0 = []
         list_1 = []
         for add in add_list:
            bit_dict = {}
            if add[b] == 0:
               list_0.append(add)
            else:
               list_1.append(add)
         #print path + " XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
         #print len(add_list)
         #print len(list_0)
         #print len(list_1)
         #print len(list_0) + len(list_1)
         bit_dict["0"] = list_0
         bit_dict["1"] = list_1
         tree_dict[path + "_" + str(b) + "v0"] = list_0
         tree_dict[path + "_" + str(b) + "v1"] = list_1
         tree_dict[path] = []
         done = 1
   #print tree_dict
   return done,tree_dict

def get_decoder_mask(dict):
   addresses = []
   for x in get_object(["block","register_with_bitfield","register_without_bitfield"]):
      addresses.append(global_dict[str(x)]['addressable'])

   add_num = len(addresses)
   print "Addresses are " + str(add_num)
   baddr = np.zeros((add_num, 32), dtype=np.int)
   decode_dict = {}
   tree_dict = {}
   
   #building address array
   a = 0
   for add in sorted(addresses):
      bit_mask = 0x80000000
      for n in range(32):
         if add & bit_mask != 0:
            baddr[a,31-n] = 1
         bit_mask = bit_mask >> 1
      a = a + 1
   #print baddr
   
   tree_dict["-1v0"] = baddr
   
   while(True):
      done,tree_dict = dec_route_add(tree_dict)
      if done == 0:
         break
  
   for bit_path in tree_dict:
      if tree_dict[bit_path] != []:
         add_bits = tree_dict[bit_path][0]
         add = ""
         for n in reversed(range(32)):
            add = add + str(add_bits[n])
         bit_list = bit_path.split("_")
         mask = 0
         for bit in bit_list:
            x = int(re.sub(r'v.*',"",bit))
            if x >= 0:
               mask = mask | (1 << x)
         decode_dict[str(int(add,2))] = mask

   #for address in sorted(decode_dict.keys()):
   #   print "add:"
   #   print address
   #   print "mask:"
   #   print hex(decode_dict[address])
   return decode_dict

#return the slave total size
def slave_size_calc():
   add_max = 0
   for node_id in get_object(["all"]):
      node_dict = global_dict[node_id]
      add = node_dict['addressable']
      #print add
      #if add == None:
      #   print node_dict['complete_id']
      #   print node_dict['type']
      if int(node_dict['size']) > 1:
         add += int(node_dict['size'])*4
      if abs(add) > abs(add_max):
         add_max = add
   n = 0;
   while(True):
      if abs(2**n) >= abs(add_max):
         break
      else:
         n += 1
   return 2**n
      
#populate the node dictionary
def populate_node_dictionary(this,parent,hier_level):
   this_dict = {}
   this_dict['hier_level']       = hier_level
   this_dict['this_node']        = this
   this_dict['parent_node']      = parent
   this_dict['this_id']          = this.get('id')
   if parent != None:
      this_dict['parent_id']     = parent.get('id')
   else:
      this_dict['parent_id']     = None
   this_dict['complete_id']      = None
   this_dict['addressable_id']   = None
   this_dict['prev_id']          = None
   this_dict['address']          = this.get('address')
   this_dict['decoder_mask']     = None
   this_dict['absolute_offset']  = None
   this_dict['mask']             = this.get('mask')
   this_dict['permission']       = this.get('permission')
   this_dict['hw_permission']    = this.get('hw_permission')
   this_dict['hw_rst']           = this.get('hw_rst')
   if this.get('mask') != None:
      this_dict['range']         = get_range_from_mask(this.get('mask'))
   else:
      this_dict['range']         = [31,0]
   if this.get('hw_prio') == "bus":
      this_dict['hw_prio']       = False
   else:
      this_dict['hw_prio']       = True 
   child_list = []
   for child in this:
      child_list.append(child.get('id')) 
   this_dict['child_id']         = child_list
   this_dict['parent_key']       = None
   this_dict['child_key']        = []
   this_dict['addressable']      = None
   this_dict['link']             = this.get('link')
   this_dict['array']            = this.get('array')
   this_dict['array_offset']     = this.get('array_offset')
   this_dict['array_idx']        = this.get('array_idx')
   if this.get('size') == None:
      this_dict['size']          = "1"
   else:
      this_dict['size']          = this.get('size')
   this_dict['type']             = "undef"
   if this.get('description') == None:
      this_dict['description']   = "Missing description"
   else:
      this_dict['description']   = this.get('description')
   this_dict['hw_dp_ram']        = this.get('hw_dp_ram')
   if this.get('hw_dp_ram_bus_lat') == None:
      this_dict['hw_dp_ram_bus_lat']= "1"
   else:
      this_dict['hw_dp_ram_bus_lat']= this.get('hw_dp_ram_bus_lat')
   if this.get('hw_dp_ram_logic_lat') == None:
      this_dict['hw_dp_ram_logic_lat']= "1"
   else:
      this_dict['hw_dp_ram_logic_lat']= this.get('hw_dp_ram_logic_lat')
   if this.get('hw_dp_ram_width') == None:
      this_dict['hw_dp_ram_width']= "32"
   else:
      this_dict['hw_dp_ram_width']= this.get('hw_dp_ram_width')
   if this.get('hw_dp_ram_init_file') == None:
      this_dict['hw_dp_ram_init_file']= ""
   else:
      this_dict['hw_dp_ram_init_file']= this.get('hw_dp_ram_init_file')
   if this.get('hw_dp_ram_init_file_format') == None:
      this_dict['hw_dp_ram_init_file_format']= "hex"
   else:
      this_dict['hw_dp_ram_init_file_format']= this.get('hw_dp_ram_init_file_format')      
      
   this_dict['hw_ignore']        = "no"#this.get('hw_ignore') hw_ignore feature can be enabled here
   return this_dict
                
#populate all subnodes of a node of hierarchical level defined by target_level 
def populate_subnodes(node,target_level,current_level):
   global node_num
   global global_dict
   global key_table
   if node == None:
      return -1
   else:
      for subnode in node:
         if subnode.get('hw_ignore') != "yes":
            if current_level == target_level:
               global_dict[str(node_num)] = populate_node_dictionary(subnode,node,current_level+1)
               key_table[str(subnode)] = int(node_num)
               node_num += 1
               #print subnode.get('id')
            else:
               populate_subnodes(subnode,target_level,current_level+1)

#fill child/parent fields
def fill_child(dict):
   for this_node in dict:
      if dict[this_node]['parent_node'] != None:
         parent_key = key_table[str(dict[this_node]['parent_node'])]
         dict[this_node]['parent_key'] = str(parent_key)
         dict[str(parent_key)]['child_key'].append(int(this_node))               
        
#fill absolute offset field walking from current node to root and accumulating offset
def fill_absolute_offset(dict):
   absolute_offset = 0
   for node_id in reverse_key_order(dict):
      if dict[node_id]['address'] != None:
         absolute_offset = int(dict[node_id]['address'],16)
         test_node = node_id
         while(True):
            parent_id = dict[test_node]['parent_key'];
            if parent_id == None:
               break
            else:
               if dict[parent_id]['address'] != None:
                  absolute_offset += int(dict[parent_id]['address'],16)
            test_node = parent_id
         dict[node_id]['absolute_offset'] = absolute_offset

#fill decoder mask field         
def fill_decoder_mask(dict,decode_dict):
   for node_id in reverse_key_order(dict):
      if dict[node_id]['addressable'] != None:
         #hex_add = hex(dict[node_id]['addressable'])
         #print str(dict[node_id]['addressable'])
         add = str(dict[node_id]['addressable'])
         add = str(int(add))
         dict[node_id]['decoder_mask'] = decode_dict[add]
         
#fill complete id field
def fill_complete_id(dict):
   for node_id in reverse_key_order(dict):
      current_node = node_id
      complete_id = dict[current_node]['this_id']
      prev_id = ""
      while(True):
         if dict[current_node]['parent_key'] == None:
            break
         else:
            complete_id = dict[current_node]['parent_id'] + "." + complete_id
            if prev_id == "":
               prev_id = dict[current_node]['parent_id']
            else:
               prev_id = dict[current_node]['parent_id'] + "." +  prev_id
         current_node = str(dict[current_node]['parent_key'])
      dict[node_id]['complete_id'] = complete_id
      dict[node_id]['addressable_id'] = re.sub(r"^(\w*\.)","",complete_id)
      dict[node_id]['prev_id'] = prev_id
   
#propagate reset value to child nodes
def propagate_reset_value(dict):
   for node_id in get_object(["bitfield"]):
      parent_node_id = dict[node_id]['parent_key']
      if dict[node_id]['hw_rst'] == None and dict[parent_node_id]['hw_rst'] != None:
         try:
            rst_val = int(dict[parent_node_id]['hw_rst'],16)
            rst_val = rst_val & int(dict[node_id]['mask'],16)
            rst_val = rst_val >> int(dict[node_id]['range'][1])
            dict[node_id]['hw_rst'] = hex_format(rst_val)
         except:
            if dict[node_id]['range'][0] == -1:
               rst_val = dict[parent_node_id]['hw_rst'] + "(" + str(dict[node_id]['range'][1]) + ")"
            else:
               rst_val = dict[parent_node_id]['hw_rst'] + "(" + str(dict[node_id]['range'][0]) + " downto " + str(dict[node_id]['range'][1]) + ")"
            dict[node_id]['hw_rst'] = rst_val
          
#create generics resets dictionary          
def get_reset_generics(dict):
   reset_generics_dict = {}
   for node_id in get_object(["bitfield","register_with_bitfield","register_without_bitfield"]):
      if dict[node_id]['hw_rst'] != None:
         try:
            int(dict[node_id]['hw_rst'],16)
         except:
            #print dict[node_id]['hw_rst']
            if not "(" in dict[node_id]['hw_rst'] and dict[node_id]['hw_rst'] != "no":
               lo_idx = dict[node_id]['range'][1]
               hi_idx = dict[node_id]['range'][0]
               if hi_idx == -1:
                  reset_generics_dict[dict[node_id]['hw_rst']] = "std_logic"
               else:
                  reset_generics_dict[dict[node_id]['hw_rst']] = "std_logic_vector(" + str(hi_idx-lo_idx) + " downto 0)"
   return reset_generics_dict

#create command line parameters dictionary
def get_parameters_dict(constants):
   param_dict = {}
   for c in constants:
      x = c.split("=")
      if len(x) != 2:
         print "Constant not correctly specified. Expected format is \"constant=value\""
         sys.exit(1)
      else:
         param_dict[x[0]] = x[1]
   #print param_dict
   for key in param_dict.keys():
      if key in allowed_attribute_value.keys():
         print "Constant has not allowed name: " + key
         sys.exit(1)
      if param_dict[key] in allowed_attribute_value.keys():
         print "Constant has not allowed value: " + param_dict[key]
         sys.exit(1)
   return param_dict

# def fill_rst(dict):
   # done = 0
   # for node_id in reverse_key_order(dict):
      # if dict[node_id]['rst'] == None:
         # dict[node_id]['rst'] = "0x0"  
      # # for child in dict[node_id]['child_key']:
         # # if dict[str(child)]['rst'] == None:
            # # done = 1
            # # dict[str(child)]['rst'] = dict[node_id]['rst']
   # #print "---------------------------------"
   # #print dict
   # return done
            
# def fill_permission(dict):
   # done = 0
   # for node_id in reverse_key_order(dict):
      # if dict[node_id]['permission'] == None:
         # dict[node_id]['permission'] = "rw" 
      # # for child in dict[node_id]['child_key']:
         # # if dict[str(child)]['permission'] == None:
            # # done = 1
            # # dict[str(child)]['permission'] = dict[node_id]['permission']
   # return done
         
#write default permission where it is not specified
def default_permission(dict):
   for node_id in reverse_key_order(dict):
      if dict[node_id]['permission'] == None:
         dict[node_id]['permission'] = 'rw'
    
#write default permission where it is not specified    
def default_reset(dict):
   for node_id in reverse_key_order(dict):
      if dict[node_id]['hw_rst'] == None:
         dict[node_id]['hw_rst'] = "0x0"
    
#fill type field    
def fill_type(dict):
   for node_id in reverse_key_order(dict):
      if int(dict[node_id]['size']) > 1:
         dict[node_id]['type'] = "block"
      elif dict[node_id]['child_key'] == []:
         if dict[node_id]['absolute_offset'] != None:
            dict[node_id]['type'] = "register_without_bitfield"
         elif dict[node_id]['mask'] != None and int(dict[node_id]['size']) == 1:
            dict[node_id]['type'] = "bitfield"
            dict[dict[node_id]['parent_key']]['type'] = "register_with_bitfield"
         
#fill addressable field
def fill_addressable(dict):
   #An object is addressable if it is:
   #        - block
   #        - register_with_bitfield
   #        - register_without_bitfield
   #        - bitfield
   for node_id in reverse_key_order(dict):
      if dict[node_id]['type'] == "block":
         dict[node_id]['addressable'] = dict[node_id]['absolute_offset']
      elif dict[node_id]['type'] == "register_without_bitfield":
         dict[node_id]['addressable'] = dict[node_id]['absolute_offset']
      elif dict[node_id]['type'] == "bitfield":
         dict[node_id]['addressable'] = dict[dict[node_id]['parent_key']]['absolute_offset']
         dict[dict[node_id]['parent_key']]['addressable'] = dict[dict[node_id]['parent_key']]['absolute_offset']
            
#return a list of requested objects
def get_object(object_list):
   node_list = []
   sorted_list = []
   for node_id in reverse_key_order(global_dict):
      node_id = str(node_id)
      if (global_dict[node_id]['type'] in object_list) or (global_dict[node_id]['type'] != "undef" and object_list == ["all"]):
         node_list.append([global_dict[node_id]['addressable'],global_dict[node_id]['range'][1],node_id])
   for node_id in sorted(node_list):
      sorted_list.append(node_id[2])
   return sorted_list
   
#return number of registers
def get_nof_registers(dict):
   return len(get_object(["register_without_bitfield","register_with_bitfield"]))
   
#return number of blocks
def get_nof_blocks(dict):
   return len(get_object(["block"]))
   
#return a reversed ordered list of keys 
def reverse_key_order(dict):
   key_list = []
   for node_id in sorted([int(x) for x in dict.keys()]):
      key_list.append(str(node_id))
   return reversed(key_list)           

#check for clashing addresses
def check_offset():
   for x in get_object(["block","register_with_bitfield","register_without_bitfield"]):
      this_dict = global_dict[x]
      this_dict_size = int(this_dict['size'])*4 
      for y in get_object(["block","register_with_bitfield","register_without_bitfield"]):
         other_dict = global_dict[y]
         other_dict_size = int(other_dict['size'])*4
         if this_dict['complete_id'] != other_dict['complete_id']: 
            if this_dict['addressable'] >= other_dict['addressable'] and this_dict['addressable'] < other_dict['addressable'] + other_dict_size:
               print "Error1: conflicting offsets:"
               print this_dict['complete_id'] + " " + hex(this_dict['addressable'])
               print other_dict['complete_id'] + " " + hex(other_dict['addressable'])
               sys.exit(1)
            if this_dict['addressable'] + this_dict_size - 1 >= other_dict['addressable'] and this_dict['addressable']  + this_dict_size - 1  < other_dict['addressable'] + other_dict_size:
               print "Error2: conflicting offsets:"
               print this_dict['complete_id'] + " at offset " + hex(this_dict['addressable'])
               print other_dict['complete_id'] + " at offset " + hex(other_dict['addressable'])
               sys.exit(1)

def check_address_requirement():
   for x in get_object(["block"]):
      this_dict = global_dict[x]
      this_addr = this_dict['addressable']
      this_size = int(this_dict['size'])*4 
      if this_addr & (this_size-1) != 0:
         print "Error! It should be (absolute_offset & (size-1)) = 0"
         print this_dict['complete_id'] + " doesn't meet this requirement!"
         print this_dict['complete_id'] + " absolute offset is " + hex(this_addr)
         print this_dict['complete_id'] + " size is " + str(this_size) + " bytes"
         sys.exit(1)

#check for clashing bit-field           
def check_bitfield():
   for x in get_object(["register_with_bitfield"]):
      this_dict = global_dict[x] 
      for m in this_dict['child_key']:
         for n in this_dict['child_key']:
            if m != n:
               mask_0 = int(global_dict[str(m)]['mask'],16)
               mask_1 = int(global_dict[str(n)]['mask'],16)
               if mask_0 & mask_1 != 0:
                  print "Error: conflicting bitfields!"
                  print global_dict[str(m)]['complete_id']
                  print "conflicts with"
                  print global_dict[str(n)]['complete_id']
                  sys.exit(1)
                 
#check for reserved words occurrence                 
def check_reserved_words(dict):
   for node_id in dict.keys():
      if string.lower(dict[node_id]['this_id']) in vhdl_reserved_words:
         print "Error: Keyword \"" + dict[node_id]['this_id'] + "\" is used as node_id!"
         print "Exiting..."
         sys.exit(1)
            
#replace characters for signals            
def replace_sig(string):
   replaced = string
   replaced = re.sub(r"\|.*?/","",replaced)
   replaced = re.sub(r"\*","",replaced)
   replaced = re.sub(r"\.\.",".",replaced)
   replaced = re.sub(r"\. "," ",replaced)
   replaced = re.sub(r"\.;",";",replaced)
   replaced = re.sub(r"<<","(",replaced)
   replaced = re.sub(r">>",")",replaced)
   replaced = replaced.replace(").(",")(")
   replaced = replaced.replace(". "," ")
   return replaced

#replace characters for constants 
def replace_const(string):
   replaced = string
   replaced = re.sub(r"\|","",replaced)
   replaced = re.sub(r"/","",replaced)
   replaced = re.sub(r"\*","",replaced)
   replaced = re.sub(r"<<","_",replaced)
   replaced = re.sub(r">>","",replaced)
   replaced = replaced.replace(").(",")(")
   replaced = replaced.replace(". "," ")
   return replaced
   
#add a child to parent node
def xml_add(parent):
   #print parent
   sub = ET.SubElement(parent, 'node')
   #print sub
   return sub
   
#fill a node
def fill_node(node,key):
   root_id = global_dict["0"]['this_id']
   id = global_dict[str(key)]['complete_id']
   id = re.sub(r"\|.*?/","",id)
   id = replace_const(id)
   id = id.replace(".","_")
   id = re.sub(r"_+","_",id)
   id = re.sub(r"_$","",id)
   #print "root",root_id
   #print "this",id
   if id.find(root_id) == 0:
      id = id.replace(root_id + "_","",1)
   node.set('id',             id)
   if global_dict[str(key)]['address'] != None:
      node.set('address',        "0x" + hex_format(global_dict[str(key)]['absolute_offset']))
   if global_dict[str(key)]['mask'] != None:
      node.set('mask',           global_dict[str(key)]['mask'])
   node.set('size',           global_dict[str(key)]['size'])
   node.set('permission',     global_dict[str(key)]['permission'])
   node.set('hw_rst',         global_dict[str(key)]['hw_rst'])
   node.set('description',    global_dict[str(key)]['description'])
   
#build output XML
def build_output_tree(size):
   xml_root = ET.Element('node')
   xml_root.set('id',global_dict["0"]['this_id'])
   xml_root.set('byte_size',str(size))
   for x in get_object(["block","register_with_bitfield","register_without_bitfield"]):
      dict = global_dict[x]
      #print dict['complete_id']
      sub = xml_add(xml_root)
      fill_node(sub,x)
      if dict['type'] == "register_with_bitfield":
         for child in dict['child_key']:
            subsub = xml_add(sub)
            fill_node(subsub,child)
            subsub.set('id',global_dict[str(child)]['this_id'])

   myxml = xml.dom.minidom.parseString(ET.tostring(xml_root)) #or xml.dom.minidom.parse('xmlfile.xml') 
   xml_file_name = global_dict["0"]['this_id'] + "_output.xml"   
   xml_file_name = normalize_path(xml_output_folder + xml_file_name)
   xml_file = open(xml_file_name, "w")
   xml_file.write(myxml.toprettyxml())
   xml_file.close()
#
#
# MAIN STARTS HERE
#
#
parser = OptionParser()
parser.add_option("-a", "--attributes", 
                  action="store_true",
                  dest="xml_help", 
                  default = False,
                  help="Prints supported XML attributes and exits.")
parser.add_option("-l", "--log",
                  action="store_true",
                  dest="log", 
                  default = False,
                  help="Print version and history log.")
parser.add_option("-i", "--input_file", 
                  action="append",
                  dest="input_file", 
                  default = [],
                  help="XML input files. It is possible to specify several files repeating this option.")
parser.add_option("-d", "--input_folder", 
                  action="append",
                  dest="input_folder", 
                  default = [],
                  help="Paths to input files folders. It is possible to specify several folders repeating this option. The script runs on all XML files in included folders.")
parser.add_option("-p", "--path", 
                  action="append",
                  dest="path", 
                  default = [],
                  help="Paths to linked XML files. It is possible to specify multiple several files repeating this option.")
parser.add_option("-v", "--vhdl_output", 
                  dest="vhdl_output", 
                  default = "",
                  help="Generated VHDL output folder.")
parser.add_option("-x", "--xml_output", 
                  dest="xml_output", 
                  default = "",
                  help="Generated XML output folder.")
parser.add_option("-b", "--bus_library", 
                  dest="bus_library", 
                  default = "work",
                  help="Generated code will reference the specified bus VHDL library. Default is \"work\".")
parser.add_option("-s", "--slave_library", 
                  dest="slave_library", 
                  default = "work",
                  help="Generated code will reference the specified slave VHDL library. Default is \"work\".")
parser.add_option("-t", "--tb", 
                  action="store_true",
                  dest="tb", 
                  default = False,
                  help="Generate a simple test bench in sim sub-folder.")
parser.add_option("-c", "--constant", 
                  action="append",
                  dest="constant", 
                  default = [],
                  help="Constant passed to script. The script will substitute the specified constant value in the XML file. Example \"-c constant1=0x0000\". ")

(options, args) = parser.parse_args()

print "xml2vhdl.py version " + str(version[0])

if options.xml_help == True:
   print
   print "Supported XML attributes:"
   print
   for n in sorted(allowed_attribute_value.keys()):
      print "'" + n + "'"
      dedented_text = textwrap.dedent("Description: "  +  re.sub(r" +",' ',attribute_description[n])).strip()
      print textwrap.fill(dedented_text, initial_indent='      ', subsequent_indent='      '+' '*13, width=80)
      print "      Allowed values: "  +  " | ".join(allowed_attribute_value[n])
      print "      Default value:  "  +  default_attribute_value[n]
      print
   sys.exit()

if options.log == True:
   print 
   print "History Log:"
   print
   for n in range(len(version)/2):
      print "version " + str(version[2*n])
      dedented_text = textwrap.dedent(re.sub(r" +",' ',version[2*n+1])).strip()
      print textwrap.fill(dedented_text, width=80)
      print
   sys.exit()
   
vhdl_output_folder = normalize_output_folder(options.vhdl_output)
xml_output_folder = normalize_output_folder(options.xml_output)
if options.tb == True:
   sim_output_folder = normalize_output_folder(vhdl_output_folder + "sim")

input_file_list = []
input_folder_list = options.input_folder
if input_folder_list != []:
   input_file_list = file_list_generate(input_folder_list,'.xml')
for n in options.input_file:
   input_file_list.append(n)
    
if args != []:
   print "Unexpected argument:", args[0] 
   print "-h for help"
   print "-a for supported XML attributes"
   sys.exit(1)
   
if input_file_list == []:
   print "No input file!"
   print "-h for help"
   print "-a for supported XML attributes"
   sys.exit(1)
    
for input_file_name in input_file_list:
   print "-----------------------------------------------------------------"
   print "Analysing \"" +  input_file_name + "\""
   
   global_dict = {}
   key_table = {}
   node_num = 0

   tree = ET.parse(input_file_name)
   root = tree.getroot()
   #resolve link, iterate through nodes till there are no link more
   while(True):
      found = 0
      for node in root.iter('node'):
         if 'link' in node.attrib.keys():  
            found = 1
            link = node.attrib['link']
            link_found = ""
            for path in options.path:
               if path != "":
                  path += "/"
               if os.path.isfile(normalize_path(path + link)):
                  link_found = normalize_path(path + link)
                  break
            if link_found == "":
               if os.path.isfile(normalize_path(link)):
                  link_found = link
               else:
                  print "Error! Link \"" + link + "\" not found!"
                  sys.exit(1)
            node.set('link_done',node.attrib['link'])
            node.attrib.pop('link')
            link_tree = ET.parse(link_found)
            link_root = link_tree.getroot()
            node.extend(link_root)
      if found == 0:
         break
     
   #writing absolute path in ram init file attribute
   for node in root.iter('node'):
      if 'hw_dp_ram_init_file' in node.attrib.keys():  
         init_file = node.attrib['hw_dp_ram_init_file']
         abs_path = ""
         xml_path = os.path.dirname(os.path.abspath(input_file_name))
         for path in options.path:
            if path != "":
               path += "/"
            if os.path.isfile(normalize_path(path + init_file)):
               abs_path = normalize_path(os.path.abspath(normalize_path(path + init_file)))
               break
         if abs_path == "":
            abs_path = normalize_path(xml_path + "/" + init_file)
         if node.attrib['hw_dp_ram_init_file_check'] != "no":
            print "Checking if BRAM init file normalize_path " + abs_path + " exists"
            if os.path.isfile(abs_path) == False:
               print "Error! BRAM init file \"" + init_file + "\" not found!"
               sys.exit(1)
         else:
            print "Check of BRAM init file " + abs_path + " bypassed!"
         node.set('hw_dp_ram_init_file',abs_path)
     
   #resolve command line parameters
   param_dict = get_parameters_dict(options.constant)
   if param_dict != {}:
      for node0 in root.iter('node'):
         attrib_dict = node0.attrib
         for attrib in attrib_dict:
            if attrib_dict[attrib] in param_dict.keys():
               node0.set(attrib,param_dict[attrib_dict[attrib]])
               
   #exclude node with "hw_ignore" attribute set
   for node0 in root.iter('node'):
      if node0.get('hw_ignore') == "yes":
         for node1 in node0.iter('node'):
            node1.set('hw_ignore','yes')
            print "ignored!"
            
   #unroll arrays
   for node0 in root.iter('node'):
      for node1 in node0.findall('node'):
         if 'array' in node1.attrib.keys():
            array = int(node1.attrib['array'])
            if array > 0:
               #print "----------------------------------------------------"
               #print node0.get('id')
               #print array
               for n in range(1,array):
                  #nodex_tree = copy_tree(node1)
                  nodex = copy.deepcopy(node1)
                  #print "NODEX"
                  #print nodex
                  nodex.set('array_idx',str(n))
                  nodex.set('id',node1.get('id')+"<<"+str(n)+">>")
                  nodex.set('address',hex(int(node1.get('address'),16) + int(node1.get('array_offset'),16)*n))
                  for subnode in nodex.findall('node'):
                     subnode.set('id',"|"+subnode.get('id')+"/*");  
                  node0.append(nodex)
               node1.set('array_idx','0')
               node1.set('id',node1.get('id')+"<<0>>")
               for subnode in node1.findall('node'):
                  subnode.set('id',"|"+subnode.get('id')+"/"); 
                     
   #print root.get('id')
   #for child in root:
   #   print child.tag, child.attrib
   #for id in root.iter('node'):
   #   print id.attrib

   level = 0
   node_num = 1
   old_node_num = 1

   global_dict[str(0)] = populate_node_dictionary(root,None,0)
   key_table[str(root)] = 0
   while(True):
      populate_subnodes(root,level,0)
      if old_node_num != node_num:
         level += 1
         old_node_num = node_num
      else:
         break

   print "Hierarchical levels are " + str(level)
   print "Nodes are " + str(node_num)
   print "Checking reserved words..."
   check_reserved_words(global_dict)
   print "fill_child..."
   fill_child(global_dict)
   print "fill_complete_id..."
   fill_complete_id(global_dict)
   print "fill_absolute_offset..."
   fill_absolute_offset(global_dict)
   print "fill_type..."
   fill_type(global_dict)
   print "fill_addressable..."
   fill_addressable(global_dict)
   print "check_offset..."
   check_offset()
   check_address_requirement()
   print "check_bitfield..."
   check_bitfield()
   print "get_decoder_mask..."
   decode_dict = get_decoder_mask(global_dict)
   print "fill_decoder_mask..."
   fill_decoder_mask(global_dict,decode_dict)

   # print "fill_rst..."
   # fill_rst(global_dict)
   # # while(True):
      # # if fill_rst(global_dict) == 1:
         # # break
   # print "fill_permission..."
   # fill_permission(global_dict)
   # # while(True):
      # # if fill_permission(global_dict) == 1:
         # # break
         
   print "propagate_reset_value..."
   propagate_reset_value(global_dict)
   print "default_reset..."
   default_reset(global_dict)
   reset_generics_dict = get_reset_generics(global_dict)
   print "default_permission..."
   default_permission(global_dict)
   max_id_len = get_max_id_len(global_dict)
   if get_nof_registers(global_dict) == 0:
      nof_registers_block = 0
   else:
      nof_registers_block = 1
   nof_memory_block = get_nof_blocks(global_dict)
   nof_hw_dp_ram = 0
   total_byte_size = str(slave_size_calc())
   build_output_tree(total_byte_size)
   ##
   ## RECORDS and ARRAY        
   ##         
   records = ""
   snippet = ""
   for node_id in reverse_key_order(global_dict):
      node_dict = global_dict[node_id]
      if node_dict['child_key']:
         if node_dict['array']:
            if node_dict['array_idx'] == "0":
               if node_dict['complete_id'].find("*") == -1:
                  snippet = "\t" + "type t_" + bus + "_" + node_dict['complete_id'].replace(".","_") + " is array (0 to " + node_dict['array'] + "-1) of "
                  for child in [node_dict['child_key'][0]]:
                     child_dict = global_dict[str(child)]
                     if not child_dict['child_key']:
                        if child_dict['range'][0] == -1: 
                           snippet += "std_logic;\n"
                        else:
                           snippet += "std_logic_vector(" + str(child_dict['range'][0]-child_dict['range'][1]) + " downto 0);\n"
                     else:
                        snippet += "t_" + bus + "_" + child_dict['complete_id'].replace(".","_") + ";\n"
                  snippet += "\n"
                  records += snippet         
         else:
            if node_dict['complete_id'].find("*") == -1:
               to_be_done = 0
               for child in node_dict['child_key']:
                  child_dict = global_dict[str(child)]
                  if child_dict['size'] == "1":
                     to_be_done = 1
               if to_be_done == 1:
                  snippet = "\t" + "type t_" + bus + "_" + node_dict['complete_id'].replace(".","_") + " is record\n"
                  for child in sorted(node_dict['child_key']):
                     child_dict = global_dict[str(child)]
                     if child_dict['size'] == "1":
                     #if the child is a leaf, define it as base type (std_logic or std_logic_vector)
                        if not child_dict['child_key']:
                           if child_dict['range'][0] == -1: 
                              snippet += "\t\t" + child_dict['this_id'] + ": std_logic;\n"
                           else:
                              snippet += "\t\t" + child_dict['this_id'] + ": std_logic_vector(" + str(child_dict['range'][0]-child_dict['range'][1]) + " downto 0);\n"
                        else:
                           if child_dict['array_idx'] == "0" or child_dict['array_idx'] == None:
                              snippet += "\t\t" + child_dict['this_id'] + ": t_" + bus + "_" + child_dict['complete_id'].replace(".","_") + ";\n"
                     #else define another record
                  snippet += "\tend record;\n\n"
                  records += snippet
   records = re.sub(r"<<[0-9]*>>","",records)
   records = re.sub(r"\|","",records)
   records = re.sub(r"/","",records)
   ##
   ## RECORDS and ARRAY DECODED        
   ##         
   records_decoded = ""
   snippet = ""
   for node_id in reverse_key_order(global_dict):
      node_dict = global_dict[node_id]
      if node_dict['child_key']:
         if node_dict['array']:
            if node_dict['array_idx'] == "0":
               if node_dict['complete_id'].find("*") == -1:
                  snippet = "\t" + "type t_" + bus + "_" + node_dict['complete_id'].replace(".","_") + "_decoded is array (0 to " + node_dict['array'] + "-1) of "
                  for child in [node_dict['child_key'][0]]:
                     child_dict = global_dict[str(child)]
                     if not child_dict['child_key']: 
                        snippet += "std_logic;\n"
                     else:
                        snippet += "t_" + bus + "_" + child_dict['complete_id'].replace(".","_") + "_decoded;\n"
                  snippet += "\n"
                  records_decoded += snippet         
         else:
            if node_dict['complete_id'].find("*") == -1:
               snippet = "\t" + "type t_" + bus + "_" + node_dict['complete_id'].replace(".","_") + "_decoded is record\n"
               for child in sorted(node_dict['child_key']):
                  child_dict = global_dict[str(child)]
                  #if the child is a leaf, define it as base type (std_logic or std_logic_vector)
                  if not child_dict['child_key']: 
                     snippet += "\t\t" + child_dict['this_id'] + ": std_logic;\n"
                  else:
                     if child_dict['array_idx'] == "0" or child_dict['array_idx'] == None:
                        snippet += "\t\t" + child_dict['this_id'] + ": t_" + bus + "_" + child_dict['complete_id'].replace(".","_") + "_decoded;\n"
                  #else define another record
               snippet += "\tend record;\n\n"
               records_decoded += snippet
   records_decoded = re.sub(r"<<[0-9]*>>","",records_decoded)
   records_decoded = re.sub(r"\|","",records_decoded)
   records_decoded = re.sub(r"/","",records_decoded)
   ##
   ## REGISTER DESCRIPTOR RECORDS
   ##      
   descr_records = ""
   snippet = "\t" + "type t_" + bus + "_" + root.get('id') + "_descr is record\n"
   for node_id in get_object(["block","register_without_bitfield","bitfield"]):
      node_dict = global_dict[node_id]
      snippet += "\t\t" + node_dict['addressable_id'].replace(".","_") + ": t_reg_descr;\n"
   snippet += "\tend record;\n\n"
   descr_records += snippet
   descr_records = replace_const(descr_records)
   ##
   ## REGISTER DESCRIPTOR INIT
   ##      
   descr_records_init = ""
   snippet = "\t" + "constant " + bus + "_" + root.get('id') + "_descr: t_" + bus + "_" + root.get('id') + "_descr := (\n"
   for node_id in get_object(["block","register_without_bitfield","bitfield"]):
      node_dict = global_dict[node_id]
      addressable_id = node_dict['addressable_id'].replace(".","_")
      addressable_id = replace_const(addressable_id)
      snippet +=  "\t\t" + addressable_id + add_space(addressable_id,max_id_len) + " => ("
      if node_dict['addressable'] == None:
         snippet += "X\"00000000\","
      else:
         #print node_dict['addressable']
         snippet +=  "X\"" + hex_format(node_dict['addressable']) + "\","
      if node_dict['range'][0] >= 0:
         snippet += str_format(str(node_dict['range'][0]),2) + ","
      else:
         snippet += str_format(str(node_dict['range'][1]),2) + ","
      snippet += str_format(str(node_dict['range'][1]),2) + ","
      if node_dict['hw_rst'] == "no": 
         snippet += "X\"00000000\",   no_reset,"
      else:
         try:
            reset_val = hex_format(int(node_dict['hw_rst'],16))
         except:
            reset_val = "00000000"
         snippet += "X\"" + reset_val + "\",async_reset,"
      if node_dict['decoder_mask'] == None:
         snippet += "X\"" + hex_format(global_dict[node_dict['parent_key']]['decoder_mask']) + "\","
      else:
         snippet += "X\"" + hex_format(node_dict['decoder_mask']) + "\","
      snippet += node_dict['permission'] + "),\n" 
   snippet = re.sub(r",$","",snippet)
   snippet += "\t);\n\n"
   descr_records_init += snippet
   ##
   ## RESET ASSIGN
   ##      
   reset_assign = ""
   snippet = ""
   for node_id in get_object(["register_without_bitfield","bitfield"]):
      node_dict = global_dict[str(node_id)]
      snippet = node_dict['complete_id']
      
      snippet = replace_sig(snippet)

      if node_dict['hw_rst'] != "no":
         try:
            int(node_dict['hw_rst'],16)
            if node_dict['range'][0] == -1:
               snippet += " <= " + bus + "_" + root.get('id') + "_descr." + node_dict['addressable_id'].replace(".","_") + ".rst_val(0)" + ";\n"
            else:
               snippet += " <= " + bus + "_" + root.get('id') + "_descr." + node_dict['addressable_id'].replace(".","_") + ".rst_val(" + str(node_dict['range'][0]-node_dict['range'][1]) + " downto 0)" + ";\n"
         except:
            snippet += " <= " + node_dict['hw_rst'] + ";\n"

         snippet = replace_const(snippet)
      else:
         snippet = "--" + snippet + " is not reset!\n"

      reset_assign += snippet
   ##
   ## RESET GENERICS PROCEDURE
   ##
   ##
   ## RESET GENERICS DEFINITION
   ##
   reset_generics_definition = ""
   reset_generics_procedure = ""
   reset_generics_map = ""
   for key in sorted(reset_generics_dict.keys()):
      if reset_generics_dict[key] == "std_logic":
         reset_generics_definition += "\t" + key + ": " + reset_generics_dict[key] + " := '0';\n" 
         reset_generics_procedure  += ";\n" + indent(key + ": " + reset_generics_dict[key],8) 
      else:
         reset_generics_definition += "\t" + key + ": " + reset_generics_dict[key] + " := (others=>'0');\n" 
         reset_generics_procedure  += ";\n" + indent(key + ": " + reset_generics_dict[key],8) 
      reset_generics_map        += ",\n" + indent(key,8)
   if reset_generics_definition != "":
      reset_generics_definition = "generic(\n" + reset_generics_definition
      reset_generics_definition += ");\n"
      reset_generics_definition = reset_generics_definition.replace(";\n);","\n);")
   #print reset_generics_definition
   #print reset_generics_procedure
   #print reset_generics_map

   ##
   ## FULL DECODER ASSIGN
   ##         
   full_decoder_assign = ""
   snippet = ""
   for node_id in get_object(["block","register_without_bitfield","bitfield"]):
      node_dict = global_dict[str(node_id)]
      if_str = "if " + bus + "_<slave_name>_decoder(" + bus + "_<slave_name>_descr.<addressable_id>,addr) = true and en = '1' then\n"
      snippet = node_dict['complete_id'].replace(".","_decoded.",1) + " := '0';\n"
      snippet = replace_sig(snippet)
      
      snippet += if_str.replace('<slave_name>',global_dict['0']['this_id'])
      snippet = snippet.replace('<addressable_id>',node_dict['addressable_id'].replace(".","_"))
      snippet = replace_const(snippet)
      
      snippet += "\t" + node_dict['complete_id'].replace(".","_decoded.",1) + " := '1';\n"
      snippet += "end if;\n\n"

      snippet = replace_sig(snippet)
      
      full_decoder_assign += snippet 
   ##
   ## WRITE TO REGISTERS
   ##         
   write_reg = ""
   snippet = ""
   for node_id in get_object(["register_without_bitfield","bitfield"]):
      node_dict = global_dict[str(node_id)]
      if_str = "if <slave_name>_decoded.<addressable_id> = '1' then\n"
      if (node_dict['permission'] == "rw" or node_dict['permission'] == "w") and node_dict['size'] == "1":
         snippet = if_str.replace('<slave_name>',global_dict['0']['this_id'])
         snippet = snippet.replace('<addressable_id>',node_dict['addressable_id'])
               
         if node_dict['range'][0] == -1:
            snippet += "\t" + node_dict['complete_id'] + " <= data(" + str(node_dict['range'][1]) + ");\n"
         else:
            snippet += "\t" + node_dict['complete_id'] + " <= data(" + str(node_dict['range'][0]) + " downto " + str(node_dict['range'][1]) + ");\n"
         snippet += "end if;\n\n"
         
         snippet = replace_sig(snippet)

         write_reg += snippet
   ##
   ## READ FROM REGISTERS
   ##   
   read_reg = ""
   snippet = ""
   for node_id in get_object(["register_without_bitfield","bitfield"]):
      node_dict = global_dict[str(node_id)]
      if_str = "if <slave_name>_decoded.<addressable_id> = '1' then\n"
      if (node_dict['permission'] == "rw" or node_dict['permission'] == "r") and node_dict['size'] == "1":
         snippet = if_str.replace('<slave_name>',global_dict['0']['this_id'])
         snippet = snippet.replace('<addressable_id>',node_dict['addressable_id'])
               
         if node_dict['range'][0] == -1:
            snippet += "\tret(" + str(node_dict['range'][1]) + ") := " + node_dict['complete_id'] + ";\n"
         else:
            snippet += "\tret(" + str(node_dict['range'][0]) + " downto " + str(node_dict['range'][1]) + ") := " + node_dict['complete_id'] + ";\n"
         snippet += "end if;\n\n"
         
         snippet = replace_sig(snippet)
         
         read_reg += snippet
   ##
   ## FW WRITE TO REGISTERS
   ##       
   hw_write_reg_logic_prio = ""
   hw_write_reg_bus_prio = ""
   snippet = ""
   hw_doesnt_write = 1
   for node_id in get_object(["register_without_bitfield","bitfield"]):
      node_dict = global_dict[str(node_id)]
      if node_dict['hw_permission'] == "we" and node_dict['size'] == "1":
         hw_doesnt_write = 0
         id = bus + "_" + node_dict['complete_id']
         snippet = "if " + id.replace(".","_in_we.",1) + " = '1' then\n"
         snippet += "\t" + id.replace(".","_int.",1) + " <= " + id.replace(".","_in.",1) + ";\n"
         snippet += "end if;\n"
         
      if node_dict['hw_permission'] == "w" and node_dict['size'] == "1":
         hw_doesnt_write = 0
         id = bus + "_" + node_dict['complete_id']
         snippet = id.replace(".","_int.",1) + " <= " + id.replace(".","_in.",1) + ";\n"

      snippet = replace_sig(snippet)
      if node_dict['hw_prio'] == True: 
         hw_write_reg_logic_prio += snippet
      else:
         hw_write_reg_bus_prio += snippet 
      snippet = ""   
   ##
   ## MUX ASSIGN
   ##   
   mux_assign = ""
   snippet = ""
   memory_blocks = 0
   for node_id in get_object(["block"]):
      node_dict = global_dict[str(node_id)]
      if_str = "if " + bus + "_<slave_name>_decoder(" + bus + "_<slave_name>_descr.<addressable_id>,addr) = true then\n"
      snippet = if_str.replace('<slave_name>',global_dict['0']['this_id'])
      snippet = snippet.replace('<addressable_id>',node_dict['addressable_id'].replace(".","_"))
      
      snippet += "\tret(" + str(nof_registers_block+memory_blocks) + ") := '1';\n"
      snippet += "end if;\n\n"
         
      snippet = replace_sig(snippet)
      
      memory_blocks = memory_blocks + 1 
         
      mux_assign += snippet
      
   if nof_registers_block > 0 and nof_memory_block > 0:
      mux_assign += "if ret(ret'length-1 downto 1) = \"" + nof_memory_block*"0" + "\" then\n"
      mux_assign += "\tret(0) := '1';\n"
      mux_assign += "end if;\n\n"
      
   ipb_mapping_record = ""
   ipb_mapping_record_init = "" 
   memory_blocks_inst = ""
   memory_blocks_port = ""
   if nof_memory_block > 0:
      snippet = "type t_ipb_" + root.get('id') + "_mapping is record\n"
      for node_id in get_object(["block"]):
         node_dict = global_dict[str(node_id)]
         snippet += "\t" + node_dict['addressable_id'].replace(".","_") + ": integer;\n"
      snippet += "end record;\n"
      ipb_mapping_record = snippet

      snippet = "constant c_ipb_" + root.get('id') + "_mapping: t_ipb_" + root.get('id') + "_mapping := (\n"
      idx = 0
      for node_id in get_object(["block"]):
         node_dict = global_dict[str(node_id)]
         if idx > 0:
            snippet += ",\n"
         snippet += "\t" + node_dict['addressable_id'].replace(".","_") + "=> " + str(nof_registers_block+idx)
         idx += 1
      snippet += "\n);\n"
      ipb_mapping_record_init = snippet

      for node_id in get_object(["block"]):
         node_dict = global_dict[str(node_id)]
         if node_dict['permission'] == "r" or node_dict['permission'] == "rw":
            ipb_read = "true"
         else:
            ipb_read = "false"
         if node_dict['permission'] == "w" or node_dict['permission'] == "rw":
            ipb_write = "true"
         else:
            ipb_write = "false"
         if node_dict['hw_dp_ram'] == "yes":
            nof_hw_dp_ram += 1
            snippet = "ipb_<name>_dp_ram_inst: entity " + options.slave_library + ".ipb_" + root.get('id') + "_dp_ram\n"
            snippet += "generic map(\n"
            snippet += "\tram_add_width => <size>,\n"
            snippet += "\tram_dat_width => <dat_width>,\n"
            snippet += "\tipb_read => " + ipb_read + ",\n"
            snippet += "\tipb_write => " + ipb_write + ",\n"
            snippet += "\tipb_read_latency => <ipb_lat>,\n"
            snippet += "\tuser_read_latency => <user_lat>,\n"
            snippet += "\tinit_file => \"<init_file>\",\n"
            snippet += "\tinit_file_format => \"<init_file_format>\"\n"
            snippet += ")\n"
            snippet += "port map(\n"
            snippet += "\tipb_clk  => " + bus_clock + ",\n" 
            snippet += "\tipb_miso => ipb_miso_arr(c_ipb_" + root.get('id') + "_mapping.<name>),\n"
            snippet += "\tipb_mosi => ipb_mosi_arr(c_ipb_" + root.get('id') + "_mapping.<name>),\n"
            
            snippet += "\t" + "user_clk => "  + root.get('id') + "_<name>_clk,\n" 
            snippet += "\t" + "user_en => "   + root.get('id') + "_<name>_en,\n"
            snippet += "\t" + "user_we => "   + root.get('id') + "_<name>_we,\n"
            snippet += "\t" + "user_add => "  + root.get('id') + "_<name>_add,\n"
            snippet += "\t" + "user_wdat => " + root.get('id') + "_<name>_wdat,\n"
            snippet += "\t" + "user_rdat => " + root.get('id') + "_<name>_rdat\n"

            snippet += ");\n\n"  
            size = np.log2(int(node_dict['size'])/1)
            snippet = snippet.replace("<size>",str(int(math.ceil(size))))
            snippet = snippet.replace("<dat_width>",str(int(node_dict['hw_dp_ram_width'])))
            snippet = snippet.replace("<ipb_lat>",str(int(node_dict['hw_dp_ram_bus_lat'])))
            snippet = snippet.replace("<user_lat>",str(int(node_dict['hw_dp_ram_logic_lat'])))
            snippet = snippet.replace("<init_file>",str(node_dict['hw_dp_ram_init_file']))
            snippet = snippet.replace("<init_file_format>",str(node_dict['hw_dp_ram_init_file_format']))
            snippet = snippet.replace("<name>",node_dict['addressable_id'].replace(".","_"))

            memory_blocks_inst += snippet
            memory_blocks_inst = "--\n--\n--\n" + memory_blocks_inst
            
            snippet =  "\n" + root.get('id') + "_<name>_clk: in std_logic:='0';"
            snippet += "\n" + root.get('id') + "_<name>_en: in std_logic:='0';"
            snippet += "\n" + root.get('id') + "_<name>_we: in std_logic:='0';"
            snippet += "\n" + root.get('id') + "_<name>_add: in std_logic_vector(<size> downto 0):=(others=>'0');"
            snippet += "\n" + root.get('id') + "_<name>_wdat: in std_logic_vector(<dat_width> downto 0):=(others=>'0');"
            snippet += "\n" + root.get('id') + "_<name>_rdat: out std_logic_vector(<dat_width> downto 0);"
            snippet = snippet.replace("<size>",str(int(math.ceil(size))-1))
            snippet = snippet.replace("<dat_width>",str(int(node_dict['hw_dp_ram_width'])-1))
            snippet = snippet.replace("<ipb_lat>",str(int(node_dict['hw_dp_ram_bus_lat'])))
            snippet = snippet.replace("<user_lat>",str(int(node_dict['hw_dp_ram_logic_lat'])))
            snippet = snippet.replace("<name>",node_dict['addressable_id'].replace(".","_"))
            
            memory_blocks_port += snippet
         else:
            memory_blocks_port += "\n" + "ipb_" + root.get('id') + "_<name>_miso: in t_ipb_miso;"
            memory_blocks_port += "\n" + "ipb_" + root.get('id') + "_<name>_mosi: out t_ipb_mosi;"
            memory_blocks_port = memory_blocks_port.replace("<name>",node_dict['addressable_id'].replace(".","_"))
            snippet = "ipb_miso_arr(c_ipb_" + root.get('id') + "_mapping.<name>) <= ipb_" + root.get('id') + "_<name>_miso;\n"
            snippet += "ipb_" + root.get('id') + "_<name>_mosi <= ipb_mosi_arr(c_ipb_" + root.get('id') + "_mapping.<name>);\n"
            snippet = snippet.replace("<name>",node_dict['addressable_id'].replace(".","_"))
            memory_blocks_inst += snippet
            memory_blocks_inst = "--\n--\n--\n" + memory_blocks_inst
            
   #for k in range(len(global_dict)):
      #print k
      #print global_dict[str(k)]['this_id']
      #print global_dict[str(k)]['complete_id']
      #print global_dict[str(k)]['prev_id']
      ##print global_dict[str(k)]['this_node']
      ##print global_dict[str(k)]['parent_node']
      ##print global_dict[str(k)]['parent_key']
      ##print global_dict[str(k)]['brother_key']
      ##print global_dict[str(k)]['child_key']
      #print global_dict[str(k)]['absolute_offset']
      #print global_dict[str(k)]['decoder_mask']
      #print global_dict[str(k)]['rst']
      #print global_dict[str(k)]['permission']
      #print 
      
   #print "------RECORDS--------"
   #print records  
   #print "------DESCRIPTOR RECORDS--------"
   #print descr_records
   #print "------DESCRIPTOR RECORDS INIT--------"
   #print descr_records_init
   #print "------RESET ASSIGN--------"
   #print reset_assign
   #print "------WRITE REG--------"
   #print write_reg
   #print "------READ REG--------"
   #print read_reg

   #for n in get_object(["all"]):
   #   print global_dict[n]['complete_id']
   #   print global_dict[n]['addressable_id']
   #   print global_dict[n]['addressable']
   #   print global_dict[n]['absolute_offset']
   # ##
   # ## Replacing relevant fields in skeleton package file
   # ##
   vhdl_text = read_template_file("template/" + "xml2vhdl" + "_slave_pkg.template.vhd")   
   
   vhdl_text = vhdl_text.replace("<BUS>",bus)
   vhdl_text = vhdl_text.replace("<BUS_CLK>",bus_clock)
   vhdl_text = vhdl_text.replace("<BUS_RST>",bus_reset)
   vhdl_text = vhdl_text.replace("<BUS_RST_VAL>",bus_reset_val)
   vhdl_text = vhdl_text.replace("<BUS_LIBRARY>",options.bus_library)
   vhdl_text = vhdl_text.replace("<SLAVE_LIBRARY>",options.slave_library)
   vhdl_text = vhdl_text.replace("<SLAVE_NAME>",root.get('id'))
   vhdl_text = vhdl_text.replace("<RECORDS>\n",records)
   vhdl_text = vhdl_text.replace("<RECORDS_DECODED>\n",records_decoded)
   vhdl_text = vhdl_text.replace("<DESCRIPTOR_RECORDS>\n",descr_records)
   vhdl_text = vhdl_text.replace("<DESCRIPTOR_RECORDS_INIT>\n",descr_records_init)
   vhdl_text = vhdl_text.replace("<RESET_GENERICS_PROCEDURE>",indent(reset_generics_procedure,0))
   vhdl_text = vhdl_text.replace("<RESET_ASSIGN>\n",indent(reset_assign,2))
   vhdl_text = vhdl_text.replace("<FULL_DECODER_ASSIGN>\n",indent(full_decoder_assign,2))
   vhdl_text = vhdl_text.replace("<WRITE_ASSIGN>\n",indent(write_reg,2))
   vhdl_text = vhdl_text.replace("<READ_ASSIGN>\n",indent(read_reg,2))
   vhdl_text = vhdl_text.replace("<MUX_ASSIGN>\n",indent(mux_assign,3))
   vhdl_text = vhdl_text.replace("<NOF_REGISTER_BLOCKS>",str(nof_registers_block))
   vhdl_text = vhdl_text.replace("<NOF_MEMORY_BLOCKS>",str(nof_memory_block))
   vhdl_text = vhdl_text.replace("<IPB_MAPPING_RECORD>\n",indent(ipb_mapping_record,1))
   vhdl_text = vhdl_text.replace("<IPB_MAPPING_RECORD_INIT>\n",indent(ipb_mapping_record_init,1))
   if nof_registers_block == 0:
      vhdl_text = re.sub(r'<REMOVE_IF_BLOCK_ONLY_START>(.|\n)*?<REMOVE_IF_BLOCK_ONLY_END>\n',"",vhdl_text)
   else:
      vhdl_text = re.sub(r'<REMOVE_IF_BLOCK_ONLY_START>\n',"",vhdl_text)
      vhdl_text = re.sub(r'<REMOVE_IF_BLOCK_ONLY_END>\n',"",vhdl_text)      
   vhdl_text = vhdl_text.replace("\t","   ")
   
   write_vhdl_file(bus + "_" + root.get('id') + "_pkg.vhd",vhdl_output_folder,vhdl_text)
   # ##
   # ## Replacing relevant fields in template SLAVE file
   # ##
   vhdl_text = read_template_file("template/" + "xml2vhdl" + "_slave.template.vhd")   
   
   vhdl_text = vhdl_text.replace("<BUS>",bus)
   vhdl_text = vhdl_text.replace("<BUS_CLK>",bus_clock)
   vhdl_text = vhdl_text.replace("<BUS_RST>",bus_reset)
   vhdl_text = vhdl_text.replace("<BUS_RST_VAL>",bus_reset_val)
   vhdl_text = vhdl_text.replace("<BUS_LIBRARY>",options.bus_library)
   vhdl_text = vhdl_text.replace("<SLAVE_LIBRARY>",options.slave_library)
   vhdl_text = vhdl_text.replace("<SLAVE_NAME>",root.get('id'))
   vhdl_text = vhdl_text.replace("<RESET_GENERICS_DEFINITION>\n",indent(reset_generics_definition,1))
   vhdl_text = vhdl_text.replace("<RESET_GENERICS_MAP>",indent(reset_generics_map,0))
   vhdl_text = vhdl_text.replace("<MEMORY_BLOCKS_PORT>",indent(memory_blocks_port,2))
   vhdl_text = vhdl_text.replace("<MEMORY_BLOCKS_INST>",indent(memory_blocks_inst,1))
   vhdl_text = vhdl_text.replace("<HW_WRITE_REG_LOGIC_PRIO>",indent(hw_write_reg_logic_prio,3))
   vhdl_text = vhdl_text.replace("<HW_WRITE_REG_BUS_PRIO>",indent(hw_write_reg_bus_prio,3))
   if nof_registers_block == 0:
      vhdl_text = re.sub(r'<REMOVE_IF_BLOCK_ONLY_START>(.|\n)*?<REMOVE_IF_BLOCK_ONLY_END>\n',"",vhdl_text)
   else:
      vhdl_text = re.sub(r'<REMOVE_IF_BLOCK_ONLY_START>\n',"",vhdl_text)
      vhdl_text = re.sub(r'<REMOVE_IF_BLOCK_ONLY_END>\n',"",vhdl_text)
   if hw_doesnt_write == 1:
      vhdl_text = re.sub(r'<REMOVE_IF_NO_FW_WRITE_START>(.|\n)*?<REMOVE_IF_NO_FW_WRITE_END>\n',"",vhdl_text)
   else:
      vhdl_text = re.sub(r'<REMOVE_IF_NO_FW_WRITE_START>\n',"",vhdl_text)
      vhdl_text = re.sub(r'<REMOVE_IF_NO_FW_WRITE_END>\n',"",vhdl_text)
   vhdl_text = vhdl_text.replace(";\n);","\n\t);")
   vhdl_text = vhdl_text.replace("\t","   ")
   
   write_vhdl_file(bus + "_" + root.get('id') + ".vhd",vhdl_output_folder,vhdl_text)
   ##
   ## Replacing relevant fields in template MUXDEMUX file
   ##
   vhdl_text = read_template_file("template/" + "xml2vhdl" + "_slave_muxdemux.template.vhd")
   
   vhdl_text = vhdl_text.replace("<BUS>",bus)
   vhdl_text = vhdl_text.replace("<BUS_CLK>",bus_clock)
   vhdl_text = vhdl_text.replace("<BUS_RST>",bus_reset)
   vhdl_text = vhdl_text.replace("<BUS_RST_VAL>",bus_reset_val)
   vhdl_text = vhdl_text.replace("<SLAVE_NAME>",root.get('id'))
   vhdl_text = vhdl_text.replace("<BUS_LIBRARY>",options.bus_library)
   vhdl_text = vhdl_text.replace("<SLAVE_LIBRARY>",options.slave_library)
   vhdl_text = vhdl_text.replace("\t","   ")
   
   write_vhdl_file(bus + "_" + root.get('id') + "_muxdemux.vhd",vhdl_output_folder,vhdl_text)
   ##
   ## Replacing relevant fields in template SIM MASTER file
   ##
   if options.tb == True:
      vhdl_text = read_template_file("template/" + bus + "/" + "xml2vhdl" + "_sim_ms.template.vhd")
      
      tb_add = ""
      for node_id in get_object(["block","register_without_bitfield","bitfield"]):
         node_dict = global_dict[node_id]
         if node_dict['addressable'] != None:
            tb_add += "X\"" + hex_format(node_dict['addressable']) + "\""
            break
      
      vhdl_text = vhdl_text.replace("<BUS>",bus)
      vhdl_text = vhdl_text.replace("<BUS_CLK>",bus_clock)
      vhdl_text = vhdl_text.replace("<BUS_RST>",bus_reset)
      vhdl_text = vhdl_text.replace("<BUS_RST_VAL>",bus_reset_val)
      vhdl_text = vhdl_text.replace("<SLAVE_NAME>",root.get('id'))
      vhdl_text = vhdl_text.replace("<BUS_LIBRARY>",options.bus_library)
      vhdl_text = vhdl_text.replace("<SLAVE_LIBRARY>",options.slave_library)
      vhdl_text = vhdl_text.replace("<TB_ADD>",tb_add)
      vhdl_text = vhdl_text.replace("\t","   ")
      
      write_vhdl_file(bus + "_" + root.get('id') + "_sim_ms.vhd",vhdl_output_folder,vhdl_text)
      ##
      ## Replacing relevant fields in template TB file
      ##
      vhdl_text = read_template_file("template/" + "xml2vhdl" + "_tb.template.vhd")
      
      memory_blocks_signal = memory_blocks_port
      memory_blocks_signal = memory_blocks_signal.replace("\n","\nsignal ")
      memory_blocks_signal = memory_blocks_signal.replace(" in "," ")
      memory_blocks_signal = memory_blocks_signal.replace(" out "," ")
      
      memory_blocks_signal_list = memory_blocks_signal.split("\n")
      memory_blocks_portmap = ""
      for signal in memory_blocks_signal_list:
         signal = signal.replace("signal ","")
         x = signal.split(":")
         if x[0] != "":
            memory_blocks_portmap += "\n" + x[0] + " => " + x[0] + ","
   
      vhdl_text = vhdl_text.replace("<BUS>",bus)
      vhdl_text = vhdl_text.replace("<BUS_CLK>",bus_clock)
      vhdl_text = vhdl_text.replace("<BUS_RST>",bus_reset)
      vhdl_text = vhdl_text.replace("<BUS_RST_VAL>",bus_reset_val)
      vhdl_text = vhdl_text.replace("<SLAVE_NAME>",root.get('id'))
      vhdl_text = vhdl_text.replace("<BUS_LIBRARY>",options.bus_library)
      vhdl_text = vhdl_text.replace("<SLAVE_LIBRARY>",options.slave_library)
      vhdl_text = vhdl_text.replace("<MEMORY_BLOCKS_SIGNAL>",indent(memory_blocks_signal,1))
      vhdl_text = vhdl_text.replace("<MEMORY_BLOCKS_PORTMAP>",indent(memory_blocks_portmap,2))
      if nof_registers_block == 0:
         vhdl_text = re.sub(r'<REMOVE_IF_BLOCK_ONLY_START>(.|\n)*?<REMOVE_IF_BLOCK_ONLY_END>\n',"",vhdl_text)
      else:
         vhdl_text = re.sub(r'<REMOVE_IF_BLOCK_ONLY_START>\n',"",vhdl_text)
         vhdl_text = re.sub(r'<REMOVE_IF_BLOCK_ONLY_END>\n',"",vhdl_text)
      if hw_doesnt_write == 1:
         vhdl_text = re.sub(r'<REMOVE_IF_NO_FW_WRITE_START>(.|\n)*?<REMOVE_IF_NO_FW_WRITE_END>\n',"",vhdl_text)
      else:
         vhdl_text = re.sub(r'<REMOVE_IF_NO_FW_WRITE_START>\n',"",vhdl_text)
         vhdl_text = re.sub(r'<REMOVE_IF_NO_FW_WRITE_END>\n',"",vhdl_text)
      vhdl_text = vhdl_text.replace(";\n);","\n\t);")
      vhdl_text = vhdl_text.replace(",\n);","\n\t);")
      vhdl_text = vhdl_text.replace("\t","   ")
      
      write_vhdl_file(bus + "_" + root.get('id') + "_tb.vhd",vhdl_output_folder,vhdl_text)
   ##
   ## Replacing relevant fields in template IPB_RAM 
   ##
   if nof_hw_dp_ram > 0:
      vhdl_text = read_template_file("template/" + "xml2vhdl" + "_dp_ram.template.vhd")

      vhdl_text = vhdl_text.replace("<BUS>",bus)
      vhdl_text = vhdl_text.replace("<BUS_LIBRARY>",options.bus_library)
      vhdl_text = vhdl_text.replace("<SLAVE_NAME>",root.get('id'))

      write_vhdl_file("ipb" + "_" + root.get('id') + "_dp_ram.vhd",vhdl_output_folder,vhdl_text)
      
print "Done!"
print

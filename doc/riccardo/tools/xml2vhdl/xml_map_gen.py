import re
import os
import sys
import zlib
import copy
import math
import binascii
import textwrap
import numpy as np
import xml.dom.minidom
import lxml.etree as ET        #for getparent()
#import xml.etree.ElementTree as ET
from optparse import OptionParser

version = [ 
            1.5 , "bram init file containing zip compressed xml",
            1.4 , "converted sys.exit() to sys.exit(1)",
            1.3 , "merge attribute implementation",
            1.2 , "byte size correction",
            1.1 , "ic cascade support",
            1.0 , "first release"
           ]

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
   
#intent a block with tab_num tabs
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

def normalize_path(input):
   input = re.sub(r"\\","/",input)
   input = re.sub(r"/+","/",input)
   return input
   
def normalize_template(input):
   input = re.sub(r"\r\n","\n",input)
   return input
   
def normalize_output_folder(input):
   output_folder = input
   if output_folder != "":
      if not os.path.exists(output_folder):
         print "Folder \"" + output_folder + "\" doesn't exist! Press [Y | y] to create it, any other key to abort"
         key = _Getch()
         if key().lower() == "y":
            os.makedirs(output_folder)
         else:
            print "Exiting..."
            sys.exit(1)
      output_folder += "/"
   return output_folder

#specific function   
def ignore_check_offset(node_x,node_y):
   ret = False
   if is_leaf(node_x) == True and node_y == node_x.getparent():
      ret = True
   elif is_leaf(node_y) == True and node_x == node_y.getparent():
      ret = True
   elif is_leaf(node_x) == True and is_leaf(node_y) == True and node_x.getparent() == node_y.getparent(): 
      ret = True
   return ret

#different function   
def check_offset(root):
   #for node in root.findall('node'):
   for x in root.findall('node'):
      #print x.get('id')
      #print x.get('absolute_offset')
      x_address = int(x.get('absolute_offset'),16) 
      x_size = get_byte_size(x)#int(x.get('byte_size')) 
      for y in root.findall('node'):
         y_address = int(y.get('absolute_offset'),16) 
         y_size = get_byte_size(y)#int(y.get('byte_size')) 
         if x != y and ignore_check_offset(x,y) == False: 
            if x_address >= y_address and x_address < y_address + y_size:
               print "Error: conflicting addresses:"
               print get_absolute_id(x),hex(x_address)
               print get_absolute_id(x),hex(y_address)
               sys.exit(1)
            if x_address + x_size - 1 >= y_address and x_address  + x_size - 1  < y_address + y_size:
               print "Error: conflicting addresses:"
               print get_absolute_id(x),hex(x_address)
               print get_absolute_id(x),hex(y_address)
               sys.exit(1)
                  
#different function   
def check_offset_requirement(root):
   for x in root.findall('node'):
      if x.get('absolute_offset') != None:
         this_addr = int(x.get('absolute_offset'),16) 
         this_size = get_byte_size(x)
         #print x.get('id')
         #print this_addr
         #print this_size
         #print
         if this_addr & (this_size-1) != 0:
            print "Error! It should be (absolute_offset & (size-1)) = 0"
            print get_absolute_id(x) + " doesn't meet this requirement!"
            print get_absolute_id(x) + " absolute offset is " + hex(this_addr)
            print get_absolute_id(x) + " size is " + str(this_size) + " bytes"
            sys.exit(1)
         
#specific function                  
def get_xml_file(link,path_list):
   link = node.attrib['link']
   link_found = ""
   for path in path_list:
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
   return link_found

#specific function   
def get_absolute_offset(node):
   if node.get('address') != None:
      offset = int(node.get('address'),16)
   else:
      offset = 0
   current_node = node
   while(True):
      parent_node = current_node.getparent()
      if parent_node == None:
         break
      else:
         if parent_node.get('address') != None:
            offset += int(parent_node.get('address'),16)
      current_node = parent_node
   return hex_format(offset)
      
#specific function
def get_absolute_id(node):
   id = node.get('id')
   current_node = node
   while(True):
      parent_node = current_node.getparent()
      if parent_node == None:
         break
      else:
         if parent_node.get('id') != None:
            id = parent_node.get('id') + "." + id
      current_node = parent_node
   return id
   
#specific function   
def depth(node):
   d = 0
   while node is not None:
      d += 1
      node = node.getparent()
   return d
   
#specific function
def is_leaf(node):
   if node.findall("node") == []:
      ret = True
   else:
      ret = False
   return ret
      
def get_byte_size(node):
   x = node.get('byte_size')
   try:
      byte_size = int(x)
   except:
      try:
         byte_size = int(x,16)
      except:
         if node.get('byte_size') != None:
            print "Unsupported byte size attribute at node " + "\"" + node.get('id') + + "\""
            sys.exit(1)
         else:
            byte_size = None
   return byte_size
      
   
#return the node total size
def get_node_size(node):
   add_max = 0
   for x in node.findall('node'):
      add = int(x.get('address'),16)
      if get_byte_size(x) == None:
         return -1
      elif get_byte_size(x) > 1:
         add += get_byte_size(x)
      if abs(add) > abs(add_max):
         add_max = add
   n = 0;
   while(True):
      if abs(2**n) >= abs(add_max):
         break
      else:
         n += 1
   return 2**n 
#
#
# MAIN STARTS HERE
#
#
parser = OptionParser()
parser.add_option("-l", "--log", 
                  action="store_true",
                  dest="log", 
                  default = False,
                  help="Print version and history log.")
parser.add_option("-i", "--input_file", 
                  dest="input_file", 
                  default = "",
                  help="XML input file.")
parser.add_option("-v", "--vhdl_output", 
                  dest="vhdl_output", 
                  default = "",
                  help="Generated VHDL output folder.")
parser.add_option("-p", "--path", 
                  action="append",
                  dest="path", 
                  default = [],
                  help="Path to linked XML files.")
parser.add_option("-x", "--xml_output", 
                  dest="xml_output", 
                  default = "",
                  help="Generated XML output folder.")
parser.add_option("-t", "--top", 
                  dest="vhdl_top", 
                  default = "",
                  help="VHDL Top Level. If this option is not specified, no VHDL file is generated.")
parser.add_option("-r", "--vhdl_record_name", 
                  dest="vhdl_record_name", 
                  default = "t_axi4lite_mmap_slaves",
                  help="VHDL record name.")
parser.add_option("-b", "--bus_library", 
                  dest="bus_library", 
                  default = "work",
                  help="Generated code will reference the specified bus VHDL library. Default is \"work\".")
parser.add_option("-s", "--design_library", 
                  dest="design_library", 
                  default = "work",
                  help="Generated code will reference the specified design VHDL library. Default is \"work\".")
              
(options, args) = parser.parse_args()

print
print "xml_map_gen.py version " + str(version[0]) 

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
             
input_file_name = options.input_file  
vhdl_output_folder = normalize_output_folder(options.vhdl_output)
if options.xml_output == "":
   output_file_name = input_file_name
else:
   output_file_name = normalize_path(input_file_name).split("/")[-1]
xml_output_folder = normalize_output_folder(options.xml_output)

vhdl_package_name = bus + "_" + options.vhdl_top + "_mmap_pkg"

tree = ET.parse(input_file_name)
root = tree.getroot()

#resolve links
while(True):
   todo = 0
   for node in root.iter('node'):
      if 'link' in node.attrib.keys() and not ('link_done' in node.attrib.keys()):
         link = get_xml_file(node.attrib['link'],options.path)
         link_tree = ET.parse(link)
         link_root = link_tree.getroot()
         node.extend(link_root)
         if link_root.get('byte_size') != None:
            node.set('byte_size',link_root.get('byte_size'))
         node.set('link_done',node.attrib['link'])
         node.attrib.pop('link')
         todo = 1
   if todo == 0:
      break;
      
#write Address and absolute id and absolute offset
for node in root.iter('node'):
   if node != root:
      absolute_id = get_absolute_id(node)
      node.set('absolute_id',absolute_id)
      absolute_offset = get_absolute_offset(node)
      node.set('absolute_offset',absolute_offset)
   if node.get('address') != None:
      node.set('address',"0x" + hex_format(int(node.get('address'),16)))

#check byte size on first level child nodes
for node in root.findall("node"):
   if node != root:
      #print node.get('absolute_id')
      #print node.get('absolute_offset')
      if node.get('byte_size') == None and node.get('size') != None:
         node.set('byte_size',str(int(node.get('size'))*4))
      elif node.get('byte_size') == None:
         print "Error: Unknown byte size for node " + absolute_id
         sys.exit(1)  

check_offset(root)
check_offset_requirement(root)
         
root.set('byte_size',str(get_node_size(root)))

vhdl_start_node = None
if options.vhdl_top != "":
   print "Searching for VHDL top level " + options.vhdl_top
   for node in root.iter('node'):
      #print node.get('absolute_id')
      if node.get('absolute_id') == options.vhdl_top:
         vhdl_start_node = node
         print "VHDL top level found!"
         break
   if root.get('id') == options.vhdl_top:
      vhdl_start_node = root
      
   if vhdl_start_node == None:
      print "VHDL top level " + options.vhdl_top + " not found!"
      print "Exiting..."
      sys.exit(1)
   else:
      print "VHDL top level found!"
  
   vhdl_id = []
   vhdl_address = []  
   for node in vhdl_start_node.findall('node'):
      vhdl_id.append(node.get('id'))
      vhdl_address.append(int(node.get('address'),16))
   max_len = get_max_len(vhdl_id)
   snippet = "type " + options.vhdl_record_name + " is (\n" 
   for address in sorted(vhdl_address):
      id = vhdl_id[vhdl_address.index(address)]
      snippet += "\t" + "id_" + id + add_space(id,max_len) + ", ba0x" + hex_format(address) + ",\n"
   snippet = snippet[0:-2]
   snippet += "\n);\n"
   snippet = indent(snippet,1)
   snippet = re.sub(r"\t","   ",snippet)
   #
   # MMAP PACKAGE
   #
   skel_file = open("template/" + "xml2vhdl" + "_mmap.template.vhd", "rU")
   vhdl_template = skel_file.read()
   vhdl_template = normalize_template(vhdl_template)
   skel_file.close()
   
   vhdl_str = vhdl_template
   vhdl_str = vhdl_str.replace("<BUS>",bus)
   vhdl_str = vhdl_str.replace("<BUS_LIBRARY>",options.bus_library)
   vhdl_str = vhdl_str.replace("<TOP_LEVEL>",options.vhdl_top)
   vhdl_str = vhdl_str.replace("<VHDL_RECORD>",options.vhdl_record_name)
   vhdl_str = re.sub("<PKG_NAME>",vhdl_package_name,vhdl_str)
   vhdl_str = re.sub("<SLAVE_TYPE>",snippet,vhdl_str)

   vhdl_file_name = vhdl_package_name + ".vhd" 
   print "Writing VHDL output file: \"" + normalize_path(vhdl_output_folder + vhdl_file_name) + "\""
   vhdl_file = open(normalize_path(vhdl_output_folder + vhdl_file_name), "w")
   vhdl_file.write(vhdl_str)
   vhdl_file.close()
   #
   # IC PACKAGE 
   #
   skel_file = open("template/" + bus + "/xml2vhdl_ic_pkg.template.vhd", "rU")
   vhdl_template = skel_file.read()
   vhdl_template = normalize_template(vhdl_template)
   skel_file.close()
   
   vhdl_str = vhdl_template
   vhdl_str = vhdl_str.replace("<BUS>",bus)
   vhdl_str = vhdl_str.replace("<BUS_LIBRARY>",options.bus_library)
   vhdl_str = vhdl_str.replace("<TOP_LEVEL>",options.vhdl_top)

   vhdl_file_name = bus + "_" + options.vhdl_top + "_ic_pkg.vhd" 
   print "Writing VHDL output file: \"" + normalize_path(vhdl_output_folder + vhdl_file_name) + "\""
   vhdl_file = open(normalize_path(vhdl_output_folder + vhdl_file_name), "w")
   vhdl_file.write(vhdl_str)
   vhdl_file.close()
   #
   # IC 
   #
   skel_file = open("template/" + bus + "/xml2vhdl_ic.template.vhd", "rU")
   vhdl_template = skel_file.read()
   vhdl_template = normalize_template(vhdl_template)
   skel_file.close()
   
   vhdl_str = vhdl_template
   vhdl_str = vhdl_str.replace("<BUS>",bus)
   vhdl_str = vhdl_str.replace("<BUS_CLK>",bus_clock)
   vhdl_str = vhdl_str.replace("<BUS_RST>",bus_reset)
   vhdl_str = vhdl_str.replace("<BUS_RST_VAL>",bus_reset_val)
   vhdl_str = vhdl_str.replace("<BUS_LIBRARY>",options.bus_library)
   vhdl_str = vhdl_str.replace("<DSN_LIBRARY>",options.design_library)
   vhdl_str = vhdl_str.replace("<TOP_LEVEL>",options.vhdl_top)

   vhdl_file_name = bus + "_" + options.vhdl_top + "_ic.vhd" 
   print "Writing VHDL output file: \"" + normalize_path(vhdl_output_folder + vhdl_file_name) + "\""
   vhdl_file = open(normalize_path(vhdl_output_folder + vhdl_file_name), "w")
   vhdl_file.write(vhdl_str)
   vhdl_file.close()
   #
   # EXAMPLE
   #
   slave_inst = ""
   for id in vhdl_id:
      snippet = "\n" + bus + "_" + id + "_inst: entity work." + bus + "_" + id + "\n"
      snippet += "port map(\n"
      snippet += "\t" + "<BUS_CLK> => <BUS_CLK>,\n"
      snippet += "\t" + "<BUS_RST> => <BUS_RST>,\n"
      snippet += "\t" + "<BUS>_mosi => axi4lite_mosi_arr(axi4lite_mmap_get_id(id_" + id + ")),\n"
      snippet += "\t" + "<BUS>_miso => axi4lite_miso_arr(axi4lite_mmap_get_id(id_" + id + "))\n"#,\n"
      #snippet += "\t" + "<BUS>_" + id + "_out => <BUS>_" + id + "_out,\n"  
      #snippet += "\t" + "<BUS>_" + id + "_in_we => <BUS>_" + id + "_in_we,\n"
      #snippet += "\t<BUS>_" + id + "_in => <BUS>_" + id + "_in\n"
      snippet += ");\n"
      slave_inst += snippet
   
   slave_inst = indent(slave_inst,1)
   slave_inst = re.sub(r"\t","   ",slave_inst)

   skel_file = open("template/" + "xml2vhdl" + "_example.template.vhd", "rU")
   vhdl_template = skel_file.read()
   vhdl_template = normalize_template(vhdl_template)
   skel_file.close()
   
   vhdl_str = vhdl_template
   vhdl_str = re.sub("<SLAVE_INST>",slave_inst,vhdl_str)
   vhdl_str = vhdl_str.replace("<BUS>",bus)
   vhdl_str = vhdl_str.replace("<BUS_LIBRARY>",options.bus_library)
   vhdl_str = vhdl_str.replace("<DSN_LIBRARY>",options.design_library)
   vhdl_str = vhdl_str.replace("<BUS_CLK>",bus_clock)
   vhdl_str = vhdl_str.replace("<BUS_RST>",bus_reset)
   vhdl_str = vhdl_str.replace("<TOP_LEVEL>",options.vhdl_top)
   vhdl_str = re.sub("<PKG_NAME>",vhdl_package_name,vhdl_str)
   vhdl_str = re.sub("<SLAVE_TYPE>",snippet,vhdl_str)
   #print vhdl_str

   vhdl_file_name = bus + "_" + options.vhdl_top + "_example.vho"  
   print "Writing VHDL output file: \"" + normalize_path(vhdl_output_folder + vhdl_file_name) + "\""
   vhdl_file = open(normalize_path(vhdl_output_folder + vhdl_file_name), "w")
   vhdl_file.write(vhdl_str)
   vhdl_file.close()
   
#merge nodes
merge_list = []      
for node in root.iter('node'):
   if node.get('merge') == "yes":
      merge_list.append(node)
for node in merge_list:
   #print "node",node.get('id')
   #print "merge",node.get('merge')
   if node.get('merge') == "yes":
      id = node.get('id')
      add = int(node.get('address'),16)
      print "Merging node", id
      merge_root = copy.deepcopy(node)
      parent_node = node.getparent()
      root.remove(node)
      for child in merge_root.findall('node'):
         child.set('id',id + "_" + child.get('id'))
         child.set('address',"0x" + hex_format(int(child.get('address'),16) + add))
      root.extend(merge_root)   
         
myxml = xml.dom.minidom.parseString(ET.tostring(root)) #or xml.dom.minidom.parse('xmlfile.xml') 
myxml = myxml.toprettyxml()
myxml = re.sub(r"\t","   ",myxml)
myxml = re.sub(r"> *",">",myxml)
myxml = re.sub(r"\n\s*\n","\n\n",myxml)
myxml = re.sub("\n\n","\n",myxml)

xml_file_name = output_file_name
xml_file_name = re.sub(r".*?\.","",xml_file_name[::-1])[::-1] 
xml_file_name = xml_file_name + "_output.xml"   
print "Writing XML output file: \"" + normalize_path(xml_output_folder + xml_file_name) + "\""
xml_file = open(normalize_path(xml_output_folder + xml_file_name), "w")
xml_file.write(myxml)
xml_file.close()

xml_compressed = zlib.compress(myxml)
xml_compressed = binascii.hexlify(xml_compressed)
xml_compressed = hex_format(len(xml_compressed)/2) + xml_compressed
bram_init = ""
if len(xml_compressed) % 8 != 0:
   xml_compressed += "0"*(8-(len(xml_compressed) % 8))
for n in range(0,len(xml_compressed)/8):
   word = xml_compressed[8*n:8*n+8]
   bram_init += word + "\n"
bram_init_file_name = re.sub(r".*?\.","",xml_file_name[::-1])[::-1] 
bram_init_file_name = bram_init_file_name + ".hex"
bram_init_file = open(normalize_path(xml_output_folder + bram_init_file_name), "w")
bram_init_file.write(bram_init)
bram_init_file.close()

print "Done!"
print


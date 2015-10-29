import os
import re
import sys
sys.path.append("../")
from repo_utils.functions import *
import config.manager as config_man
import xml.etree.ElementTree as ET
      
REPO_ROOT   = config_man.get_repo_root()
XML_SRC_DIR = "/src/xml"
XML_OUT_DIR = "/src/xml2vhdl_generated"
      
def xml2vhdl_exec(xml_file_name,xml_path):
   THIS_SLAVE_FILE = xml_file_name.split("/")[-1]
   THIS_SLAVE_LOC  = re.sub(XML_SRC_DIR + "/" + THIS_SLAVE_FILE,"",xml_file_name)
   THIS_SLAVE_LIBRARY = THIS_SLAVE_LOC.split("/")[-1]
   str = "cd .. && cd xml2vhdl && " 
   str += "python xml2vhdl.py -i " + THIS_SLAVE_LOC + "/" + XML_SRC_DIR + "/" + THIS_SLAVE_FILE + \
                     " -v " + THIS_SLAVE_LOC + "/" + XML_OUT_DIR + \
                     " -x " + THIS_SLAVE_LOC + "/" + XML_OUT_DIR + \
                     " -b axi4lite -s " + THIS_SLAVE_LIBRARY + \
                     " -p " + THIS_SLAVE_LOC + XML_SRC_DIR 
   xml_path.append(THIS_SLAVE_LOC + "/" + XML_OUT_DIR)
   python_exec_cmd(str)
   return xml_path
   
def xml_map_gen(xml_file_name,xml_path):
   THIS_IC_FILE = xml_file_name.split("/")[-1]
   THIS_IC_NAME = THIS_IC_FILE.split(".")[0]
   THIS_IC_LOC  = re.sub(XML_SRC_DIR + "/" + THIS_IC_FILE,"",xml_file_name)
   THIS_IC_LIBRARY = THIS_IC_LOC.split("/")[-1]
   print "Generating IC for",THIS_IC_LIBRARY
   str = "cd .. && cd xml2vhdl && " 
   str += "python xml_map_gen.py" + \
          " -i " + THIS_IC_LOC + "/" + XML_SRC_DIR + "/" + THIS_IC_FILE + \
          " -v " + THIS_IC_LOC + "/" + XML_OUT_DIR + \
          " -x " + THIS_IC_LOC + "/" + XML_OUT_DIR + \
          " -t " + THIS_IC_NAME + \
          " -b axi4lite -s " + THIS_IC_LIBRARY 
   for path in xml_path:
      #print path
      str += " -p " + path
   python_exec_cmd(str)

##MAIN PROGRAM
if __name__ == "__main__":
   
   module_list = read_file("module_depend.txt").split("\n")
   path_list = []
   for module in module_list:
      path_list.append(get_module_folder(REPO_ROOT,module) + XML_SRC_DIR) 

   xml_list = list_generate(path_list,[r".*xml2vhdl_generated.*"],".xml")

   ic_list = []
   xml_path = []
   for xml in xml_list:
      print "Analysing",xml 
      tree = ET.parse(xml)
      root = tree.getroot() 
      if root.get('hw_type') == "ic":
         ic_list.append(xml)
         print xml
      else:
         xml_path = xml2vhdl_exec(xml,xml_path)

   for xml in ic_list:
      xml_map_gen(xml,xml_path)
  
##
## OLD STUFF 
##
# for n in range(len(SLAVE_TODO)):
   # xml_path = xml2vhdl_exec(SLAVE_TODO[n],SLAVE_LOC[n],xml_path)
      
# for n in range(len(IC_TODO)):
   # xml_map_gen(IC_TODO[n],IC_LOC[n],xml_path)
  
# def normalize(path):
    # return re.sub(r"\\", '/', path)

# def rename_xml(folder):   
   # result = [os.path.join(dp, f) for dp, dn, fn in os.walk(normalize(folder)) for f in fn if os.path.splitext(f)[1] == '.xml']  
   # print folder
   # for n in result:
      # if n.find("_output.xml") != -1:
         # os.rename(n,n.replace("_output.xml",".xml"))
         
# def delete_xml(folder):   
   # result = [os.path.join(dp, f) for dp, dn, fn in os.walk(normalize(folder)) for f in fn if os.path.splitext(f)[1] == '.xml']  
   # print folder
   # for n in result:
         # os.remove(n)
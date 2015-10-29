import sys
import os
import re
import ConfigParser
sys.path.append("../")
from repo_utils.functions import *

#run checks on configuration
def checks(config):
   not_good = 0
   if check_folder_exists(config['REPO_ROOT']) == False:
      not_good = 1
      print "Error: 'REPO_ROOT' in config.txt doesn't point to a valid folder!"
   if check_file_exists(config['VIVADO_EXE']) == False:
      not_good = 1
      print "Error: 'VIVADO_EXE' in config.txt doesn't point to a valid file!"
   if check_folder_exists(config['MSIM_LIB_PATH']) == False:
      not_good = 1
      print "Warning: 'MSIM_LIB_PATH' in config.txt doesn't point to a valid file!"
      print "This is not an error provided that the correct library mapping is present in your modelsim.ini"
   if config['FPGA_IP'] == "":
      not_good = 1
      print "Error: 'FPGA_IP' in config.txt is not specified!"
   if check_folder_exists(config['XML_FILE']) == False:
      not_good = 1
      print "Error: 'XML_FILE' in config.txt doesn't point to a valid folder!"
   if check_folder_exists(os.path.dirname(config['SWP_FILE'])) == False:
      not_good = 1
      print "Error: 'SWP_FILE' in config.txt doesn't point to a valid folder!"
   if check_folder_exists(os.path.dirname(config['STREAM_FILE'])) == False:
      not_good = 1
      print "Error: 'STREAM_FILE' in config.txt doesn't point to a valid folder!"
   if check_folder_exists(config['C2C_FOLDER']) == False:
      not_good = 1
      print "Error: 'C2C_FOLDER' in config.txt doesn't point to a valid folder!"
   
   if not_good != 0:
      sys.exit(1)
   return 

#set a property in a configuration file   
def set(config_file,section,field,value):
   parser = ConfigParser.ConfigParser()
   parser.optionxform = str
   parser.read(config_file)
   try:
      parser.add_section(section)
   except:
      pass
   parser.set(section,field,value)
   cfgfile = open(config_file,'w')
   parser.write(cfgfile)
   cfgfile.close()
   
# get configuration from file
def get_config_from_file(config_file="../config/config.txt",design="",display=False,check=False,sim=""):
   parser = ConfigParser.ConfigParser()
   parser.optionxform = str
   parser.read(config_file)
   design = string.upper(design)
   config = {}  
   try:
      config['VIVADO_EXE'] = normalize_path(parser.get("MAIN","VIVADO_EXE"))
   except:
      raise NameError("VIVADO_EXE option is not configured in " + config_file)
   try:
      config['MSIM_LIB_PATH'] = normalize_path(parser.get("MAIN","MSIM_LIB_PATH"))
   except:
      pass
   try:
      config['REPO_ROOT'] = normalize_path(parser.get("MAIN","REPO_ROOT"))
   except:
      raise NameError("REPO_ROOT option is not configured in " + config_file)
   if design == "":
      raise NameError("No design specified!")
   elif not design in parser.sections():
      raise NameError("Configuration section of design " + design + " not found!")
   else:
      try:
         config['FPGA_IP'] = parser.get(design,"FPGA_IP")
      except:
         raise NameError("FPGA_IP option is not configured in design '" + design + "' in " + config_file)
      try:
         config['UDP_PORT'] = int(parser.get(design,"UDP_PORT"))
      except:
         raise NameError("UDP_PORT option is not configured in design '" + design + "' in " + config_file)
      try:
         config['SIM_UDP_PORT'] = int(parser.get(design,"SIM_UDP_PORT"))
      except:
         raise NameError("SIM_UDP_PORT option is not configured in design '" + design + "' in " + config_file)
      try:
         config['UDP_TIMEOUT'] = int(parser.get(design,"UDP_TIMEOUT"))
      except:
         raise NameError("UDP_TIMEOUT option is not configured in design '" + design + "' in " + config_file)
      try:
         config['XML_FILE'] = normalize_path(parser.get(design,"XML_FILE"))
      except:
         raise NameError("XML_FILE option is not configured in design '" + design + "' in " + config_file)
      try:
         config['SWP_FILE'] = normalize_path(parser.get(design,"SWP_FILE"))
      except:
         raise NameError("SWP_FILE option is not configured in design '" + design + "' in " + config_file)
      try:
         config['STREAM_FILE'] = normalize_path(parser.get(design,"STREAM_FILE"))
      except:
         raise NameError("STREAM_FILE option is not configured in design '" + design + "' in " + config_file)
      try:
         config['C2C_FOLDER'] = normalize_path(parser.get(design,"C2C_FOLDER"))
      except:
         raise NameError("C2C_FOLDER option is not configured in '" + design + "' in " + config_file)
      try:
         config['SIM'] = parser.get(design,"SIM")
      except:
         raise NameError("SIM option is not configured in design '" + design + "' in " + config_file)
         
      if (config['SIM'] == "1" and sim != "0") or sim == "1":
         config['FPGA_IP'] = "127.0.0.1"
         config['UDP_PORT'] = config['SIM_UDP_PORT']
         config['UDP_TIMEOUT'] = 0
         
   if display == True:
      print
      print "Getting configuration from \"" + config_file + "\"" 
      for n in config.keys():
         print n + ": " + str(config[n])
      print
      
   if check == True:
      checks(config)
      
   return config
   
def get_repo_root():
   cwd = re.sub(r"\\", '/', os.getcwd())
   if cwd.split("/")[-2] != "tools" or (cwd.split("/")[-1] not in ["config","make"]):
     print cwd.split("/")[-2]
     print "Please run the script from its folder!"
     sys.exit(1)
   return "/".join(cwd.split("/")[0:-2])
   
def set_config_file_main(config_file):

   REPO_ROOT = get_repo_root()
   
   parser = ConfigParser.ConfigParser()
   parser.optionxform = str
   
   cfgfile = open(config_file,'w')

   parser.add_section('MAIN')
   parser.set('MAIN','REPO_ROOT',      REPO_ROOT)
   parser.set('MAIN','VIVADO_EXE',     "\"Path to Vivado Executable\"")
   parser.set('MAIN','MSIM_LIB_PATH',  "\"Path to compiled Vivado Library for ModelSim. Leave empty if managed in your modelsim.ini\"")
   
   parser.write(cfgfile)
   
   cfgfile.close()
   
def set_config_file_design(config_file,design):

   REPO_ROOT = get_repo_root()
   
   parser = ConfigParser.ConfigParser()
   parser.optionxform = str

   parser.read(config_file)
   
   parser.add_section(string.upper(design))
   
   parser.set(string.upper(design),'FPGA_IP',        "\"FPGA IP address\"")
   parser.set(string.upper(design),'UDP_PORT',       10000)
   parser.set(string.upper(design),'SIM_UDP_PORT',   10000)
   parser.set(string.upper(design),'UDP_TIMEOUT',    1)
   parser.set(string.upper(design),'XML_FILE',       REPO_ROOT + "/designs/" + design + "/src/xml2vhdl_generated/" + design + "_output.xml")
   parser.set(string.upper(design),'SWP_FILE',       REPO_ROOT + "/designs/" + design + "/src/vhdl/tb/c2c/c2c_swap.txt")
   parser.set(string.upper(design),'STREAM_FILE',    REPO_ROOT + "/designs/" + design + "/src/vhdl/tb/c2c/c2c_stream_log.txt")   
   parser.set(string.upper(design),'C2C_FOLDER',     REPO_ROOT + "/designs/" + design + "/src/vhdl/tb/c2c")  
   parser.set(string.upper(design),'SIM',            "0")   

   cfgfile = open(config_file,'w')
   parser.write(cfgfile)
   cfgfile.close()
   
def merge_config_files(merge_from,merge_to):
   parser_from = ConfigParser.ConfigParser()
   parser_from.optionxform = str
   parser_from.read(merge_from)
   
   parser_to = ConfigParser.ConfigParser()
   parser_to.optionxform = str
   parser_to.read(merge_to)

   for section_name in parser_from.sections():
      # print 'Section:', section_name
      # print '  Options:', parser_from.options(section_name)
      # for name, value in parser_from.items(section_name):
         # print '  %s = %s' % (name, value)
      # print
      for name, value in parser_from.items(section_name):
         if name in ['VIVADO_EXE','MSIM_LIB_PATH','SIM','FPGA_IP','UDP_PORT','SIM_UDP_PORT','UDP_TIMEOUT']:
            set(merge_to,section_name,name,value)
               


   

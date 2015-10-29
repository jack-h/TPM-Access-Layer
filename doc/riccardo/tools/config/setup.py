import re
import os
import sys
import manager
from optparse import OptionParser
sys.path.append("../")
from repo_utils.functions import *

# str1 =  """
# This script will generate a config.txt file containing the repository 
# configuration. If the scripts terminates with error it is necessary to 
# manually edit the generated configuration file. Note that the script 
# will overwrite the current config.txt. However the script looks for a 
# persistent configuration file named persistent_config.txt and will 
# merge this configuration into the current config.txt
      
# If this is the first execution of this script, the recommended procedure is:
   # * run this script
   # * rename the generated config.txt to persistent_config.txt
   # * fill the empty fields in persistent_config.txt
   # * re-run this scripts
# """

str2 = """
Warning! persistent_config.txt file not found. The persistent configuration 
         file will be generated, please fill all the relevant options 
         in the generated persistent_config.txt and re-run this script.
"""

str3 = """
Warning! persistent_config.txt file found. The contained configuration 
         will be merged into the generated config.txt file.
"""

if __name__ == "__main__":

   #getting options and args
   parser = OptionParser()
   (options, args) = parser.parse_args()
    
   if check_file_exists("persistent_config.txt") == False:
      print str2
   else: 
      print str3
      
   #writing provisional config.txt 
   manager.set_config_file_main("config.txt") 
   design_list = get_modules([manager.get_repo_root()+"/designs"],[]) 
   for dsn in design_list:
      manager.set_config_file_design("config.txt",get_module_name(dsn))
   
   if check_file_exists("persistent_config.txt") == False:
      manager.merge_config_files("config.txt","persistent_config.txt")
      sys.exit(1)
   
   
   #merging persistent configuration into current configuration
   manager.merge_config_files("persistent_config.txt","config.txt")
   
   #setting Environment Variable in VHDL package
   for dsn in design_list:
      dsn = get_module_name(dsn)
      config = manager.get_config_from_file("config.txt",design=dsn,display=False,check=False)
      vhdl_text = read_file("environment_config_pkg.vho")
      vhdl_text = re.sub("<g_c2c_folder>",config['C2C_FOLDER'],vhdl_text)
      vhdl_text = re.sub("<g_c2c_swp_file>",config['SWP_FILE'],vhdl_text)
      vhdl_text = re.sub("<g_c2c_stream_file>",config['STREAM_FILE'],vhdl_text)
      write_file_creating_folder(manager.get_repo_root() + "/designs/" + dsn + "/src/vhdl/environment_config/environment_config_pkg.vhd",vhdl_text)
      
   print "Success! Repository configured!"

import datetime
import getpass
import socket
import sys
sys.path.append("../")
from repo_utils.functions import *
import config.manager as config_man
import binascii
import platform
      
def get_field(field,text):
   my_regex = r"" + re.escape(field) + r"\s*(\w+)"
   m = re.search(my_regex,text)
   if m != None:
      return m.group(1)
   else:
      print field + " revision number not found in " + config['REPO_ROOT'] + "/designs/" + design + "/src/revision/revision.txt" 
      sys.exit(1)
      
def set_field(field,value,text):
   my_regex = r"" + re.escape(field) + r"\s*(\w+)"
   text = re.sub(my_regex,field + " " + str(value),text)
   return text
    
if len(sys.argv) != 2:
   print "Error! Design not specified!"
   sys.exit(1)
 
design = get_module_name(sys.argv[1])   
board  = get_module_name(sys.argv[1],2).split('_')[1]  
config = config_man.get_config_from_file("../config/config.txt",design,True)

compile_time = "UTC compile time: " + str(datetime.datetime.utcnow())
hostname = "Host: " + socket.gethostname()
username = "User: " + getpass.getuser()

cmd = config['VIVADO_EXE'] + " -version > " + config['REPO_ROOT'] + "/tools/make/vivado_version.txt" 
exec_cmd(cmd)

#cmd = "svn info " + config['REPO_ROOT'] + "/designs/" + design + "/src/revision/revision.txt > " + config['REPO_ROOT'] + "/tools/make/svn_info.txt" 
cmd = "svn info " + config['REPO_ROOT'] + " > " + config['REPO_ROOT'] + "/tools/make/svn_info.txt" 
exec_cmd(cmd)
   
revision = read_file(config['REPO_ROOT'] + "/designs/" + design + "/src/revision/revision.txt")
major = get_field("major",revision)
minor = get_field("minor",revision)
build = get_field("build",revision)
rev_reg = (int(major,16)&0xFF) << 24 | (int(minor,16)&0xFF) << 16 | (int(build,16)&0xFFFF) << 0

new_revision = set_field("build",str(int(build)+1),revision)
write_file(config['REPO_ROOT'] + "/designs/" + design + "/src/revision/revision.txt",new_revision)

extended_info =  "BOARD: " + board + "\n" 
extended_info += "MAJOR: " + major + "\n" 
extended_info += "MINOR: " + minor + "\n" 
extended_info += "BUILD: " + build + "\n" 
extended_info += compile_time + "\n"
extended_info += username + "\n" 
extended_info += hostname + " " + platform.platform() + "\n\n"
extended_info += read_file(config['REPO_ROOT'] + "/tools/make/vivado_version.txt" ) + "\n"
extended_info += read_file(config['REPO_ROOT'] + "/tools/make/svn_info.txt" )
print extended_info

write_file(config['REPO_ROOT'] + "/designs/" + design + "/src/xml2vhdl_generated/extended_info.txt",extended_info)
write_file(config['REPO_ROOT'] + "/designs/" + design + "/src/xml2vhdl_generated/rev_reg.txt",str(hex(rev_reg))[2:])

extended_info = binascii.hexlify(extended_info)
extended_info = format(len(extended_info)/2,'08x') + extended_info
bram_init = ""
if len(extended_info) % 8 != 0:
   extended_info += "0"*(8-(len(extended_info) % 8))
for n in range(0,len(extended_info)/8):
   word = extended_info[8*n:8*n+8]
   bram_init += word + "\n"
write_file(config['REPO_ROOT'] + "/designs/" + design + "/src/xml2vhdl_generated/extended_info.hex",bram_init)

sys.exit(0)





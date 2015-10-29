#CD C:\Project\TPM\vivado\board_kcu105\tpm_kcu105.sim\sim_1\behav
#vcom -work xil_defaultlib -2008 "$(FULL_CURRENT_PATH)"

import sys
import os

#msim_lib_dir = "C:\\Project\\SKA\\tpm\\design\\tpm_test\\vivado_kcu105\\tpm_test_kcu105.sim\\sim_1\\behav"
msim_lib_dir = 'C:\\Project\\SKA\\Channelizer\\trunk\\Firmware\\designs\\tpm_test\\build\\vivado_kcu105\\tpm_test_kcu105.sim\\sim_1\\behav'

complete_file_name = sys.argv[1]
complete_file_name = complete_file_name.replace("\\","/")

complete_file_name_split = complete_file_name.split(".")
extension = complete_file_name_split.pop()

complete_file_name_split = complete_file_name.split("/")
if "modules" in complete_file_name_split:
   library = complete_file_name_split[complete_file_name_split.index("modules")+1]
elif "designs" in complete_file_name_split:
   library = complete_file_name_split[complete_file_name_split.index("designs")+1]
elif "tb" in complete_file_name_split:
   library = "xil_defaultlib"
else:
   print "error: library not found"
   sys.exit()

if extension == "vhd":
   cmd = "vcom -work " + library + " " + complete_file_name
elif extension == "v" or extension == "sv":
   cmd = "vlog -work " + library + " " + complete_file_name
else:  
   print "--------------------> Nothing to compile! <--------------------"
   sys.exit()

os.system("cd " + msim_lib_dir + " && " + cmd)


# -*- coding: utf-8 -*-
"""
Created on Tue May 12 09:34:33 2015

@author: chiello
"""

import os
import re
import sys
import string
sys.path.append("../")
from repo_utils.functions import *
import config.manager as config_man
from optparse import OptionParser


parser = OptionParser()
parser.add_option("-d", "--design", 
                  dest="design", 
                  default = "tpm_test",
                  help="Design name")
parser.add_option("-b", "--board", 
                  dest="board", 
                  default = "kcu105",
                  help="Board name")
parser.add_option("-p", "--part", 
                  dest="part", 
                  default = "xcku040-ffva1156-2-e-es1",
                  help="FPGA Part number")
parser.add_option("-t", "--synth_top_level", 
                  dest="synth_top_level", 
                  default = "kcu105_tpm_top_wrap",
                  help="Synthesis top level")
parser.add_option("-s", "--sim_top_level", 
                  dest="sim_top_level", 
                  default = "tb_tpm_top",
                  help="Simulation top level")
parser.add_option("-o", "--output_folder", 
                  dest="output_folder", 
                  default = "vivado",
                  help="Output folder")
parser.add_option("-f", "--force", 
                  action="store_true",
                  dest="force", 
                  default = False,
                  help="Force Vivado project overwriting")
parser.add_option("-i", "--implement", 
                  action="store_true",
                  dest="implement", 
                  default = False,
                  help="Generate bitstream")
parser.add_option("--implement_only", 
                  action="store_true",
                  dest="implement_only", 
                  default = False,
                  help="Generate bitstream without generation Vivado project files")
parser.add_option("-m", "--modelsim", 
                  action="store_true",
                  dest="modelsim", 
                  default = False,
                  help="ModelSim compile")
parser.add_option("", "--module_depend", 
                  action="store_true",
                  dest="module_depend", 
                  default = False,
                  help="List module dependencies")

(options, args) = parser.parse_args()

config = config_man.get_config_from_file(config_file= "../config/config.txt",design=options.design,display=True)

#Repository ROOT
REPO_ROOT = config['REPO_ROOT']

#Path to Vivado Executable
VIVADO_EXE = config['VIVADO_EXE']

#Path to compiled ModelSim Library
MSIM_LIB_PATH = config['MSIM_LIB_PATH']

#Design
DESIGN = options.design

#board name
BOARD = options.board

#FPGA part number
PART = options.part     #"xcku040-ffva1156-2-e-es1"

#Implemented top level
DESIGN_TOP_LEVEL = options.synth_top_level

#Simulation top level
SIM_TOP_LEVEL = options.sim_top_level

#XPR output folder
XPR_FOLDER = options.output_folder

#Regular expressions for excluding HDL files from Vivado project          
HDL_EXCLUDE = [r".*old.*",
               r".*altera.*",]

#Path to TCLs to include
TCL_PATH = ["/tools/make/tcl/pre_synth.tcl"]
        
def sort_module(module_depend_dict,module_included):
   all_modules = module_included
   while(True):
      done = 0
      print all_modules
      for module in sorted(all_modules):
         for ref_module in module_depend_dict[module]:
            if ref_module not in all_modules and ref_module in module_depend_dict.keys():
               all_modules.append(ref_module)
               done = 1
      if done == 0:
         break
   return sorted(all_modules)
      
   # modules = []
   # while(True):
      # done = 0
      # for check_module in sorted(module_depend_dict.keys()):
         # if module_depend_dict[check_module] == []:
            # modules.append(check_module)
            # module_depend_dict.pop(check_module,None)
            # for module in module_depend_dict.keys():
               # if check_module in module_depend_dict[module]:
                  # module_depend_dict[module].remove(check_module)
                  # done = 1
      # if done == 0:

         # if module_depend_dict != {}:
            # print "Warning! sort_module found unresolved module dependencies."
            # for module in module_depend_dict:
               # print "module \"" + module + "\" depends on:"
               # print module_depend_dict[module]
               # modules.append(module)
            # print 
         # for module in modules:
            # if not module in module_included:
               # print "Skipped module: " + module
               # modules.remove(module);
         # if design_name in modules:
            # modules.remove(design_name);
            # modules = [design_name] + modules
         # # if "work" in modules:
            # # modules.remove("work");
            # # modules = ["work"] + modules
         # return modules

def skip_module(module_depend_dict,design_name):
   design_modules = module_depend_dict[design_name]
   todo_modules = [design_name]
   #print "SKIP MODULES-----------------------------------"
   #print design_name
   #print design_modules
   
   for module in design_modules:
      #print module
      #print dict[re.sub(r'(?i)_lib$',"",n)]
      module = re.sub(r'(?i)_lib$',"",module)
      if not module in todo_modules:
         todo_modules.append(module)
      for submodule in module_depend_dict[module]:
         submodule = re.sub(r'(?i)_lib$',"",submodule)
         if not submodule in todo_modules:
            todo_modules.append(re.sub(r'(?i)_lib$',"",submodule))
   #print todo_modules
   #sys.exit()
   return todo_modules
   
def rename_module(repo_list,found_list):
   print repo_list
   new_list = []
   found = 0
   for found_name in found_list:
      found = 0
      for repo_name in repo_list:
         if found_name.lower() == repo_name.lower():
            new_list.append(repo_name)
            found = 1
      if found == 0:
         print "Error: module " + found_name + " not found!"
         sys.exit(1)
   return new_list
    
if __name__ == "__main__":
   print
   print "REPO_ROOT: ",REPO_ROOT
   print

   CWD = re.sub(r"\\", '/', os.getcwd())
   XPR_FILE_NAME = normalize_path(REPO_ROOT + "/designs/" + DESIGN + "/build/" + XPR_FOLDER + "_" + BOARD + "/" + DESIGN + "_" + BOARD + ".xpr")
   #Generated TCL file name
   XTCL_FILE_NAME = normalize_path(REPO_ROOT + "/designs/" + DESIGN + "/build/" + XPR_FOLDER + "_" + BOARD + "/" + "xpr_" + BOARD + ".tcl")
   SIM_FOLDER = normalize_path(REPO_ROOT + "/designs/" + DESIGN + "/build/" + XPR_FOLDER + "_" + BOARD + "/" + DESIGN + "_" + BOARD + ".sim/sim_1/behav" )

   LIB_PATH = ["/modules"]
   LIB_EXCLUDE = []
   LIB_PATH = add_root(LIB_PATH,REPO_ROOT)
   LIB_PATH = get_modules(LIB_PATH,LIB_EXCLUDE)

   TCL_PATH = add_root(TCL_PATH,REPO_ROOT)

   DSN_PATH = ["/designs/" + DESIGN]
   DSN_PATH = add_root(DSN_PATH,REPO_ROOT)
   for dsn in DSN_PATH:
      if os.path.isdir(dsn) == False:
         print "Error! Design " + DESIGN + " not found!" 
         sys.exit(1)

   #Path to IPs
   IP_PATH = ["/ip/board_" + BOARD,
              "/designs/" + DESIGN + "/src/ip/board_" + BOARD]
   IP_EXCLUDE = []
   IP_PATH  = add_root(IP_PATH,REPO_ROOT)

   #Path to Block Diagrams
   BD_PATH = ["/bd/board_" + BOARD,
              "/designs/" + DESIGN + "/src/bd/board_" + BOARD]
   BD_EXCLUDE = []
   BD_PATH  = add_root(BD_PATH,REPO_ROOT)

   #Path to Netlists
   EDN_PATH = ["/netlist",
               "/designs/" + DESIGN + "/src/netlist"]
   EDN_EXCLUDE = []
   EDN_PATH = add_root(EDN_PATH,REPO_ROOT)

   #XDC files, no path because the order matters 
   XDC_FILES = [
                "/designs/" + DESIGN + "/src/constr/board_" + BOARD + "/timing_specific.xdc",
                "/designs/" + DESIGN + "/src/constr/common/timing.xdc",
                "/designs/" + DESIGN + "/src/constr/board_" + BOARD + "/placement.xdc",
                "/designs/" + DESIGN + "/src/constr/common/work.xdc",
               ]
   XDC_FILES = add_root(XDC_FILES,REPO_ROOT)

   DEFAULT_LIB = ["ieee","unisim","std"]
   
   REPO_MODULE_AND_DESIGN_LIST = get_module_list(REPO_ROOT) + get_design_list(REPO_ROOT)
   
   file_depend = {}
   file_du = {}
   module_depend = {}
   module_files = {}
   design_name = ""
   referenced_library_names = []
   referenced_designs = []

   path_list_per_modules = []
   work_path_list = []
   for path in LIB_PATH:
      path_list_per_modules.append([path + "/src/vhdl",path + "/src/xml2vhdl_generated"])
   for path in DSN_PATH:
      work_path_list.append(path + "/src/vhdl")
      work_path_list.append(path + "/src/xml2vhdl_generated")
      design_name = get_module_name(path)
   path_list_per_modules.append(work_path_list)


   for path_list in path_list_per_modules:

      this_module_path_list = path_list
      #print "this_module_path", this_module_path
      this_module = get_module_name(this_module_path_list[0]).lower()
      #print this_module
      this_vhdl_module_files = list_generate(this_module_path_list,HDL_EXCLUDE,'.vhd')
      this_verilog_module_files = list_generate(this_module_path_list,HDL_EXCLUDE,'.v')
      this_sv_module_files = list_generate(this_module_path_list,HDL_EXCLUDE,'.sv')
      this_module_file = this_vhdl_module_files + this_verilog_module_files + this_sv_module_files
      #print this_module_file
      module_files[this_module] = this_module_file
      
      for file_name in this_module_file:
         vhdl_file = open(file_name, "r")
         vhdl_text = vhdl_file.read()
         vhdl_file.close()

         vhdl_text = vhdl_text.lower()
         vhdl_text = re.sub("--.*\n","",vhdl_text)
         vhdl_text = "\n" + vhdl_text
         
         entities = []
         libraries = []
         components = []
         packages = []
         #
         # Searching for defined design units
         #
         # entity declaration
         while(True):
            m = re.search(r"\n(\s|\n)*entity(\s|\n)+(\w+)(\s|\n)+is",vhdl_text)
            if m != None:
               if not (this_module + "." + m.group(3)) in entities:
                  entities.append(this_module + "." + m.group(3))
               vhdl_text = vhdl_text[:m.start()] + vhdl_text[m.end():]
            else:
               break
         
         # component declaration      
         # while(True):
            # m = re.search(r"\n(\s|\n)*(\w+)(\s|\n)*:(\s|\n)*(\w+)(\s|\n)*(generic|port)",vhdl_text)
            # if m != None:
               # if not m.group(5) in components:
                  # components.append(m.group(5))
               # vhdl_text = vhdl_text[:m.start()] + vhdl_text[m.end():]
            # else:
               # break

         # package declaration
         while(True):
            m = re.search(r"\n(\s|\n)*package(\s|\n)+(\w+)(\s|\n)+is",vhdl_text)
            if m != None:
               if not (this_module + "." + m.group(3)) in packages:
                  packages.append(this_module + "." + m.group(3))
               vhdl_text = vhdl_text[:m.start()] + vhdl_text[m.end():]
            else:
               break   
          
         this_du = {}
         this_du['packages']   = packages
         this_du['entities']   = entities
         this_du['all']        = packages + entities
         
         file_du[file_name]    = this_du
         #print "file_du", file_du
         
         entities = []
         libraries = []
         components = []
         packages = []
         #
         # Searching for dependencies
         #
         # direct entity instantiation
         while(True):
            m = re.search(r"\n(\s|\n)*(\w+)(\s|\n)*:(\s|\n)*entity(\s|\n)+(\w+).(\w+)",vhdl_text)
            if m != None:
               if not (m.group(6) + "." + m.group(7)) in entities:
                  entities.append(m.group(6) + "." + m.group(7))
               vhdl_text = vhdl_text[:m.start()] + vhdl_text[m.end():]
            else:
               break
         
         # component instantiation      
         while(True):
            m = re.search(r"\n(\s|\n)*(\w+)(\s|\n)*:(\s|\n)*(\w+)(\s|\n)*(generic|port)",vhdl_text)
            if m != None:
               if not m.group(5) in components:
                  components.append(m.group(5))
               vhdl_text = vhdl_text[:m.start()] + vhdl_text[m.end():]
            else:
               break
            
         # library reference
         while(True):
            m = re.search(r"\n(\s|\n)*library(\s|\n)+(\w+)",vhdl_text)
            if m != None:
               if not m.group(3) in libraries and not m.group(3).lower() in DEFAULT_LIB:
                  libraries.append(m.group(3))
               vhdl_text = vhdl_text[:m.start()] + vhdl_text[m.end():]
            else:
               break
          
         # package reference
         while(True):
            m = re.search(r"\n(\s|\n)*use(\s|\n)+(\w+).(\w+)",vhdl_text)
            if m != None:
               if not (m.group(3) + "." + m.group(4)) in packages and not m.group(3).lower() in DEFAULT_LIB:
                  packages.append(m.group(3) + "." + m.group(4))
               vhdl_text = vhdl_text[:m.start()] + vhdl_text[m.end():]
            else:
               break
       
         this_depend = {}
         this_depend['module']     = this_module
         this_depend['libraries']  = libraries
         this_depend['packages']   = packages
         this_depend['entities']   = entities
         this_depend['components'] = components
         this_depend['all'] = packages + entities   
         
         for lib in libraries:
            if not lib in referenced_library_names:
               referenced_library_names.append(lib)
               
         for lib in libraries:
            if get_module_type(REPO_ROOT,lib) == "designs" and not lib in referenced_designs:  
               referenced_designs.append(lib)
               path = REPO_ROOT + "/designs/" + lib
               work_path_list = []
               work_path_list.append(path + "/src/vhdl")
               work_path_list.append(path + "/src/xml2vhdl_generated")
               path_list_per_modules.append(work_path_list)
         
         for name_list in this_depend.keys():
            if name_list != 'module':
               old_list = this_depend[name_list]
               new_list = []
               for name in old_list:
                  name = re.sub(r'(?i)_lib$',"",name)
                  name = re.sub(r'(?i)_lib\.',".",name)
                  new_list.append(name)  ##Here strip out "_lib"
               this_depend[name_list] = new_list
         
         file_depend[file_name] = this_depend
      
         if this_module not in module_depend.keys():
            module_depend[this_module] = []
         for lib in libraries:
            if lib not in module_depend[this_module] and lib != this_module:
               module_depend[this_module].append(lib)

   #verify if a library is referenced with its name and its name + _lib suffix
   for lib in referenced_library_names:
      if lib + "_lib" in referenced_library_names:
         print "WARNING! The code references module " + lib + " as " + lib + " and " + lib + "_lib"
         print "Assuming " + lib + "_lib as correct reference!"
         referenced_library_names.remove(lib)
     
   # substitute "work" with actual library name
   for file in file_depend.keys():
      new_list = []
      for inst in file_depend[file]['all']:
         inst = re.sub("work.",file_depend[file]['module']+".",inst)
         new_list.append(inst)
      file_depend[file]['all'] = new_list;
            
   print "module_depend:"
   for n in module_depend.keys():
      print n, module_depend[n]
   print

   #print "file_depend:"
   #for keys in sorted(file_depend.keys()):
   #   print keys
   #   print file_depend[keys]
   #   print
   #print module_files
      
   compile_order = []
   module_included = skip_module(module_depend,design_name)
   #print module_included
   #sys.exit(1)
   module_order = sort_module(module_depend,module_included)
   #print module_order
   #sys.exit(1)
   module_order = rename_module(REPO_MODULE_AND_DESIGN_LIST,module_order)
   print
   print "module_order: " 
   for n in module_order:
      print n
   print

   if options.module_depend == True:
      write_file("module_depend.txt","\n".join(module_order))
      sys.exit(0)

   while(True):
      module_found = 0
      for module in module_order:
         #getting files
         print "Analysing module ", module
         files_todo = module_files[module.lower()]
         
         while(True):
            found = 0
            for x in sorted(files_todo):
               #print
               #print "/////////////////////////////////////", x
               #print file_depend[x]
               if file_depend[x]['all'] == []:
                  compile_order.append([x,get_module_name(x)])
                  files_todo.remove(x)
                  found = 1
                  module_found = 1
                  for du in file_du[x]['all']: 
                     for file in file_depend.keys():  #all files!
                        if du in file_depend[file]['all']:
                           #print "removed!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
                           #print du
                           #print file
                           #print
                           file_depend[file]['all'].remove(du)
            if found == 0:
               module_files[module] = files_todo
               break
      if module_found == 0:
         break
      
   print "Compile order:"   
   for n in compile_order:             
      print n[0], "library: " + n[1]
   for module in module_order:
      if module_files[module] != []:
         print
         print "Unresolved dependency: "
         for n in module_files[module]:
            #compile_order.append([n,get_module_name(n)])
            print n + " depends on: "
            print file_depend[n]['all']
            print
            
   ip_files = list_generate(IP_PATH,IP_EXCLUDE,'.xci')
   bd_files = list_generate(BD_PATH,BD_EXCLUDE,'.bd')
   edn_files = list_generate(EDN_PATH,EDN_EXCLUDE,'.edn')
   edn_constraints = list_generate(EDN_PATH,EDN_EXCLUDE,'.xdc')

   if options.force == True:
      force = " -force"
   else:
      force = ""

   xtcl = "create_project " + XPR_FILE_NAME + force + " -part " + PART + "\n"
   xtcl += "set_property part " + PART + " [current_project]\n"
   xtcl += "set_property target_language VHDL [current_project]\n"

   xtcl += "#add hdl source files\n"
   for f in compile_order:
       xtcl += "add_files -norecurse \"" + f[0] + "\"\n"
       if f[1] != "work":
         if f[1] in referenced_library_names:
            lib_name = f[1]
         else:
            lib_name = f[1] + "_lib"
         xtcl += "set_property library " + lib_name + " [get_files  " + f[0] + "]\n"
       
   xtcl += "#add IPs\n"
   for f in ip_files:
       xtcl += "add_files -norecurse \"" + f + "\"\n" 

   xtcl += "#add Block Diagram\n"
   for f in bd_files:
       xtcl += "add_files -norecurse \"" + f + "\"\n"
       
   xtcl += "#add netlist\n"
   for f in edn_files:
       xtcl += "add_files -norecurse \"" + f + "\"\n"
       
   xtcl += "#add constraint files\n"
   for f in XDC_FILES:
       xtcl += "add_files -fileset constrs_1 -norecurse \"" + f + "\"\n"
   if len(XDC_FILES) > 0:
       xtcl += "set_property target_constrs_file \"" + XDC_FILES[len(XDC_FILES)-1] + "\" [current_fileset -constrset]\n"
   xtcl += "#add netlist constraint files\n"
   for f in edn_constraints:
       xtcl += "add_files -fileset constrs_1 -norecurse \"" + f + "\"\n"
     
   #xtcl += "#disable not needed source files\n"  
   #for n in EXCLUDED_FILES:
   #    xtcl += "set_property is_enabled false [get_files \"" + n + "\"]\n"
       
   xtcl += "#set top level\n"
   if DESIGN_TOP_LEVEL != "":
       xtcl += "set_property top " + DESIGN_TOP_LEVEL + " [current_fileset]\n"
       xtcl += "update_compile_order -fileset sources_1\n"
   if SIM_TOP_LEVEL != "":
       xtcl += "set_property top " + SIM_TOP_LEVEL + " [current_fileset -simset]\n"
       xtcl += "set_property top_lib xil_defaultlib [get_filesets sim_1]\n"

   for tcl in TCL_PATH:
      xtcl += "set_property STEPS.SYNTH_DESIGN.TCL.PRE {" + tcl + "} [get_runs synth_1]\n"
   xtcl += "set_property target_simulator ModelSim [current_project]\n"
   if MSIM_LIB_PATH != "":
      xtcl += "set_property compxlib.compiled_library_dir " + MSIM_LIB_PATH + " [current_project]\n"
   xtcl += "set_property -name runtime -value {1000ns} -objects [get_filesets sim_1]\n"
   xtcl += "set_property used_in_synthesis false [get_files -filter {NAME =~ */tb/*}]"

   if not os.path.exists(os.path.dirname(XTCL_FILE_NAME)):
      print "Folder \"" + os.path.dirname(XTCL_FILE_NAME) + "\" doesn't exist! Press [Y | y] to create it, any other key to abort"
      key = get_char()
      if key.lower() == "y":
         os.makedirs(os.path.dirname(XTCL_FILE_NAME))
      else:
         print "Exiting..."
         sys.exit(1)
   xtcl_file = open(XTCL_FILE_NAME, "wb")  
   xtcl_file.write(xtcl)
   xtcl_file.close()  

   print "TCL files generated!"

   if options.implement_only == False:
      os_cmd = "cd " + "/".join(XPR_FILE_NAME.split("/")[:-1]) + " && "
      os_cmd += VIVADO_EXE + " -mode batch -source " + XTCL_FILE_NAME
      print os_cmd
      exec_cmd(os_cmd)

      if SIM_TOP_LEVEL != "":
         os_cmd = "cd " + "/".join(XPR_FILE_NAME.split("/")[:-1]) + " && "
         os_cmd += VIVADO_EXE + " -mode tcl -source " + CWD + "/tcl/" + "sim_build.tcl" + " " + XPR_FILE_NAME
         print os_cmd
         exec_cmd(os_cmd)
         
         text = "cd " + DESIGN + "_" + BOARD + ".sim/sim_1/behav && start /B modelsim"
         write_file("/".join(XPR_FILE_NAME.split("/")[:-1]) + "/" + "start_msim.bat",text)
         
         text = read_file("sim.do")
         write_file(SIM_FOLDER + "/" + "sim.do",text)
         
         text = re.sub(r"\$1",DESIGN + "." + SIM_TOP_LEVEL,text)
         text += "\n" + "run -all" 
         write_file(SIM_FOLDER + "/" + "sim_top.do",text)
         
         text = read_file(SIM_FOLDER + "/" + SIM_TOP_LEVEL + ".do")
         text = re.sub(r"vsim(.|\s)*","",text)
         write_file(SIM_FOLDER + "/" + SIM_TOP_LEVEL + "_compile_all.do",text)  
         if options.modelsim == True:
            for line in text.split("\n"):
               if line.split(" ")[0] in ["vmap","vlib","vcom","vlog"]:
                  os_cmd = "cd " + "/".join(XPR_FILE_NAME.split("/")[:-1]) + "/" + DESIGN + "_" + BOARD + ".sim/sim_1/behav" + " && "  
                  os_cmd += line
                  exec_cmd(os_cmd)
               
   if options.implement == True or options.implement_only == True:
      os_cmd = "cd " + "/".join(XPR_FILE_NAME.split("/")[:-1]) + " && " 
      os_cmd += VIVADO_EXE + " -mode batch -notrace -source " + CWD + "/tcl/" + "fw_build.tcl" + " " + XPR_FILE_NAME
      print os_cmd
      exec_cmd(os_cmd)
      
   print "Done!"
   #foo = raw_input()
   
   
   
#   
# OLD STUFF
#   
# def exec_cmd(cmd):
   # ret = os.system(cmd)
   # if ret != 0:
      # sys.exit(1)
     
# def normalize_path(path):
    # return re.sub(r"\\", '/', path)
    
# def read_file(file_name):
   # file = open(file_name, "rU")
   # text = file.read()
   # text = normalize_eol(text)
   # file.close()
   # return text

#write output file
# def write_file(file_name,text):
   # file = open(file_name, "w")
   # file.write(text)
   # file.close()
   
# def normalize_eol(input):
   # input = re.sub(r"\r\n","\n",input)
   # return input
    
# def add_root(path_list,root):
   # ret_list = []
   # for path in path_list:
      # ret_list.append(normalize_path(root+normalize_path(path)))
   # return ret_list

# def exclude(file_list,exclude_list):
   # filter_list = []
   # for f in file_list: 
      # matched = []
      # f = normalize_path(f)
      # for e in exclude_list: 
         # e = normalize_path(e)
         # matchObj = re.match( e, f, re.I)
         # if matchObj:
            # matched.append("1")
      # if len(matched) == 0:
         # filter_list.append(f)
        # #if len(matched) != 0:
        # #    print f
        # #else:
        # #    filter_list.append(f)
   # return filter_list
    
# def get_modules(path_list,exclude_list):
   # ret_list = []
   # for path in path_list:
      # for x in next(os.walk(path))[1]:
         # ret_list.append(normalize_path(path+ "/" + x))
   # ret_list = exclude(ret_list,exclude_list)
   # return ret_list
       
# def list_generate(path_list,exclude_list,ext):
    # ret = []    
    # for p in path_list:
        # result = [os.path.join(dp, f) for dp, dn, fn in os.walk(normalize_path(p)) for f in fn if os.path.splitext(f)[1] == ext]  
        # result_filter = exclude(result,exclude_list)
        # for n in result_filter:
            # ret.append(n)
    # return ret
    
# def get_module_name(file_name):
   # #print file_name
   # split = normalize_path(file_name).split("/")
   # if "modules" in split:
      # ret = split[split.index("modules")+1]   
   # elif "designs" in split:
      # ret = split[split.index("designs")+1]
   # return ret
   
# def get_module_type(module):
   # if os.path.exists(REPO_ROOT + "/" + "designs" + "/" + module):
      # return "designs"
   # elif os.path.exists(REPO_ROOT + "/" + "modules" + "/" + module):
      # return "modules"
   # else:
      # return "unknown"

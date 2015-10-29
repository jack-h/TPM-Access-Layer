import os
import re
import sys
import string

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
        
def get_char():
   key = _Getch()
   return key()

def exec_cmd(cmd):
   ret = os.system(cmd)
   if ret != 0:
      print "Command " + cmd
      print "returned error code " + str(ret)
      raise NameError("exec_cmd_fail")
      
def python_exec_cmd(cmd):
   ret = os.system(cmd)
   if ret != 0:
      print "Command \"" + cmd + "\""
      print "returned error code " + str(ret)
      sys.exit(1)
      
def normalize_eol(input):
   input = re.sub(r"\r\n","\n",input)
   return input
   
def normalize_path(path):
    return re.sub(r"\\", '/', path)
    
def check_folder_exists(folder):
   if os.path.exists(folder):
      return True
   else:
      return False
      
def check_file_exists(file):
   if os.path.isfile(file):
      return True
   else:
      return False

def read_file(file_name):
   file = open(file_name, "rU")
   text = file.read()
   text = normalize_eol(text)
   file.close()
   return text
   
def write_file(file_name,text):
   file = open(file_name, "w")
   file.write(text)
   file.close()
   
def write_file_creating_folder(file_name,text):
   output_folder = normalize_path(os.path.dirname(os.path.abspath(file_name)))
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
      write_file(file_name,text)
   else:
      "Output folder creation error!"
      sys.exit(1)
      
def list_generate(path_list,exclude_list,ext):
   ret = []    
   for p in path_list:
      result = [os.path.join(dp, f) for dp, dn, fn in os.walk(normalize_path(p)) for f in fn if os.path.splitext(f)[1] == ext]  
      result_filter = exclude(result,exclude_list)
      for n in result_filter:
         ret.append(n)
   return ret
    
def exclude(file_list,exclude_list):
   filter_list = []
   for f in file_list: 
      matched = []
      f = normalize_path(f)
      for e in exclude_list: 
         e = normalize_path(e)
         matchObj = re.match( e, f, re.I)
         if matchObj:
            matched.append("1")
      if len(matched) == 0:
         filter_list.append(f)
   return filter_list
   
def add_root(path_list,root):
   ret_list = []
   for path in path_list:
      ret_list.append(normalize_path(root+normalize_path(path)))
   return ret_list
   
def get_modules(path_list,exclude_list):
   ret_list = []
   for path in path_list:
      for x in next(os.walk(path))[1]:
         ret_list.append(normalize_path(path+ "/" + x))
   ret_list = exclude(ret_list,exclude_list)
   return ret_list
   
def get_module_folder(repo_root,module):
   if os.path.exists(repo_root + "/" + "designs" + "/" + module):
      return repo_root + "/" + "designs" + "/" + module
   elif os.path.exists(repo_root + "/" + "modules" + "/" + module):
      return repo_root + "/" + "modules" + "/" + module
   else:
      print "Unknown module", module
      sys.exit(1)
      
def get_module_name(file_name,offset=0):
   #print file_name
   split = normalize_path(file_name).split("/")
   if "modules" in split:
      return split[split.index("modules")+1+offset]   
   elif "designs" in split:
      return split[split.index("designs")+1+offset]
   else:
      print "Unknown module in file", file_name
      sys.exit(1)
         
def get_module_type(repo_root,module):
   if os.path.exists(repo_root + "/" + "designs" + "/" + module):
      return "designs"
   elif os.path.exists(repo_root + "/" + "modules" + "/" + module):
      return "modules"
   else:
      return "unknown"
     
def get_module_list(repo_root):
   return os.listdir(repo_root + "/modules")
    
def get_design_list(repo_root):
   return os.listdir(repo_root + "/designs")


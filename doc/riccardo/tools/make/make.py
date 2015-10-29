import os
import sys
sys.path.append("../")
from repo_utils.functions import *


if __name__ == "__main__":
   if "-h" in sys.argv:
      str = "python make_xpr.py -h"
      ret = python_exec_cmd(str)
      sys.exit(0)

   str = "python make_xpr.py " + " ".join(sys.argv[1:]) + " --module_depend" 
   print str   
   python_exec_cmd(str)

   str = "python make_xml.py"
   print(str)
   ret = python_exec_cmd(str)
      
   str = "python make_xpr.py " + " ".join(sys.argv[1:])   
   print(str)
   python_exec_cmd(str)



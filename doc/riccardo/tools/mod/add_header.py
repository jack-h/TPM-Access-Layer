# -*- coding: utf-8 -*-
"""
Created on Tue May 12 09:34:33 2015

@author: chiello
"""

import os
import re
import sys
import string
from optparse import OptionParser

parser = OptionParser()

# parser.add_option("-o", "--output_folder", 
                  # dest="output_folder", 
                  # default = "vivado",
                  # help="Output folder")
# parser.add_option("-f", "--force", 
                  # action="store_true",
                  # dest="force", 
                  # default = False,
                  # help="Force Vivado project overwriting.")

(options, args) = parser.parse_args()

SRC_INCLUDE  = ["axi4s","c2c","common_mem","common_ox","f2f","jesd204_if","jesd_buffer","tpm_test"]
FILE_EXCLUDE = []
#Regular expressions for excluding HDL files from Vivado project          
HDL_EXCLUDE = [r".*old.*",]
            
def normalize(path):
    return re.sub(r"\\", '/', path)
    
def add_root(path_list,root):
   ret_list = []
   for path in path_list:
      ret_list.append(normalize(root+normalize(path)))
   return ret_list

def exclude(file_list,exclude_list):
   filter_list = []
   for f in file_list: 
      matched = []
      f = normalize(f)
      for e in exclude_list: 
         e = normalize(e)
         matchObj = re.match( e, f, re.I)
         if matchObj:
            matched.append("1")
      if len(matched) == 0:
         filter_list.append(f)
        #if len(matched) != 0:
        #    print f
        #else:
        #    filter_list.append(f)
   return filter_list
   
def get_modules(path_list,exclude_list):
   ret_list = []
   for path in path_list:
      for x in next(os.walk(path))[1]:
         ret_list.append(normalize(path+ "/" + x))
   ret_list = exclude(ret_list,exclude_list)
   return ret_list
    
def list_generate(path_list,exclude_list,ext):
    ret = []    
    for p in path_list:
        result = [os.path.join(dp, f) for dp, dn, fn in os.walk(normalize(p)) for f in fn if os.path.splitext(f)[1] == ext]  
        result_filter = exclude(result,exclude_list)
        for n in result_filter:
            ret.append(n)
    return ret
    
#read VHDL file
def read_vhdl_file(file_name):
   vhdl_file = open(file_name, "rU")
   text = vhdl_file.read()
   vhdl_file.close()
   return text

#write VHDL file
def write_vhdl_file(file_name,text):
   vhdl_file = open(file_name, "w")
   vhdl_file.write(text)
   vhdl_file.close()

#Repository root
cwd = re.sub(r"\\", '/', os.getcwd())
if cwd.split("/")[-2] != "tools" or cwd.split("/")[-1] != "mod" :
   print cwd.split("/")[-2]
   print "Please run make_xpr.py from its folder!"
   sys.exit()

REPO_ROOT = "/"
REPO_ROOT = REPO_ROOT.join(cwd.split("/")[0:-2])      #"C:/Project/SKA/tpm"

print
print "REPO_ROOT: ",REPO_ROOT
print

SRC_PATH = ["/modules","/designs"]
SRC_PATH = add_root(SRC_PATH,REPO_ROOT)
SRC_PATH = get_modules(SRC_PATH,[])
SRC_PATH_INCLUDED = []
for n in SRC_PATH:
   if (n.split("/")[-1] in SRC_INCLUDE):
      SRC_PATH_INCLUDED.append(n)
print "Included Folder:"
for n in SRC_PATH_INCLUDED:
   print n
print

files_filtered = []
for path in SRC_PATH_INCLUDED:
   path = path + "/src/vhdl"
   files = list_generate([path],HDL_EXCLUDE,'.vhd')
   files_included = []
   for n in files:
      text = read_vhdl_file(n)
      m = re.search(r'--<h(.|\s)*?h>',text)
      if not (n in FILE_EXCLUDE) and m == None:
         files_included.append(n)
      else:
         print "Excluding file ", n
   files_filtered += files_included

print "Adding header to following files:"
for n in files_filtered:
   print n

print "Press [Y | y] to continue, any other key to abort"
key = sys.stdin.read(1)
sys.stdin.flush()
if string.lower(key) != "y":
   print "Exiting..."
   sys.exit()
 
header = read_vhdl_file("header.txt")
for n in files_filtered:
   text = read_vhdl_file(n)
   #text = re.sub(r'--<h(.|\s)*?h>',"",text)
   text = header + text
   write_vhdl_file(n,text)
   
print "Done!"  
sys.exit()


foo = raw_input()

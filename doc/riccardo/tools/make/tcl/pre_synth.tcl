set curr_dir [pwd]
cd "../../../../../../"
cd "tools/make"

#executing extended_info.py script
if { [catch {exec python extended_info.py $curr_dir} input] } {
   return -code error $input
} 

#reading rev_reg.txt file
cd $curr_dir
cd "../../../../src/xml2vhdl_generated"
# Slurp up the data file
set fp [open "rev_reg.txt" r]
set rev_reg [read $fp]
close $fp

#exec python make_xml.py
cd $curr_dir

set_property generic "g_rev=32'h$rev_reg" [current_fileset]

return 0




















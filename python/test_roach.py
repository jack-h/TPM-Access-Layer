__author__ = 'lessju'

from pyfabil import Roach

# Connect and initliase
roach = Roach(ip = "10.42.0.22", port = 7147)
print "Connected to roach"

for register in roach.get_register_list().iterkeys():
    print register + ':\t\t' + hex(roach[register])


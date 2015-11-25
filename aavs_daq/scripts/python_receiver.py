# X10G Development code
# UDP Receive
# Halsall 14-08-2014

import sys, socket

#from msvcrt import *

if len(sys.argv) == 3:
	ip   = sys.argv[1]
	port = int(sys.argv[2])
else:
	print "use: python udp_rx.py 192.168.9.2 61650"
	exit(0)
 
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF, 200000000)

print "Receiving on ",ip,":",port

sock.bind((ip, port))

print"Entering packet receive loop - press 's' to exit....\n"

pkt_num = 0

headings = "%9s %8s %8s %8s %8s %8s %8s %8s %8s %8s" % ('Packet No' ,'Length','DATA0','DATA1', 'DATA2', 'DATA3', 'DATA4','DATA5', 'DATA6', 'DATA7')
print headings

chr =""

data0 = 0
data1 = 0
data2 = 0
data3 = 0

try:
        while True:
 		#receive packet up to 8K Bytes
 		pkt = sock.recv(9000)
 		pkt_len = len(pkt)
 		pkt_top = 0
		data0 = (ord(pkt[pkt_top+3]) << 24) + (ord(pkt[pkt_top+2]) << 16) + (ord(pkt[pkt_top+1]) << 8) + ord(pkt[pkt_top+0])
		data1 = (ord(pkt[pkt_top+7]) << 24) + (ord(pkt[pkt_top+6]) << 16) + (ord(pkt[pkt_top+5]) << 8) + ord(pkt[pkt_top+4])
		pkt_top = 8
		data2 = (ord(pkt[pkt_top+3]) << 24) + (ord(pkt[pkt_top+2]) << 16) + (ord(pkt[pkt_top+1]) << 8) + ord(pkt[pkt_top+0])
		data3 = (ord(pkt[pkt_top+7]) << 24) + (ord(pkt[pkt_top+6]) << 16) + (ord(pkt[pkt_top+5]) << 8) + ord(pkt[pkt_top+4])
 		pkt_top = 16
		data4 = (ord(pkt[pkt_top+3]) << 24) + (ord(pkt[pkt_top+2]) << 16) + (ord(pkt[pkt_top+1]) << 8) + ord(pkt[pkt_top+0])
		data5 = (ord(pkt[pkt_top+7]) << 24) + (ord(pkt[pkt_top+6]) << 16) + (ord(pkt[pkt_top+5]) << 8) + ord(pkt[pkt_top+4])
		pkt_top = 24
		data6 = (ord(pkt[pkt_top+3]) << 24) + (ord(pkt[pkt_top+2]) << 16) + (ord(pkt[pkt_top+1]) << 8) + ord(pkt[pkt_top+0])
		data7 = (ord(pkt[pkt_top+7]) << 24) + (ord(pkt[pkt_top+6]) << 16) + (ord(pkt[pkt_top+5]) << 8) + ord(pkt[pkt_top+4])
 		pkt_str = "%08X %08X %08X %08X %08X %08X %08X %08X %08X %08X" % (pkt_num, pkt_len, data0, data1, data2, data3, data4, data5, data6, data7)
		print pkt_str
		pkt_num = pkt_num + 1
except:
    print "closing socket after exception"
    sock.close()
#finally:
    
print "closing socket at end"
sock.close()

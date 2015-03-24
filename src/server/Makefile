main:
    # Note that this links to a specific version of protobuf (2.6.1) to avoid version conflicts
	g++ -o server main.cpp utils.cpp message.pb.cc -Wall -std=c++11 -lzmq -I. -l:libprotobuf.so.9 -I/home/lessju/Code/TPM-Access-Layer/src/library -L/home/lessju/Code/TPM-Access-Layer/src/library -lboard

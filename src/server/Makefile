LIBRARY_DIR := ../library
GCC         := g++

main:
    # Note that this links to a specific version of protobuf (2.6.1) to avoid version conflicts
#    g++ -c -g `pkg-config --cflags QtCore` -MMD -MP -MF "build/AAVSFile.o.d" -o build/AAVSFile.o AAVSFile.cpp
#    g++ -c -g `pkg-config --cflags QtCore` -MMD -MP -MF "build/ChannelFormatFileManager.o.d" -o build/ChannelFormatFileManager.o ChannelFormatFileManager.cpp
#    g++ -c -g `pkg-config --cflags QtCore` -MMD -MP -MF "build/RawFormatFileManager.o.d" -o build/RawFormatFileManager.o RawFormatFileManager.cpp
	${GCC} -o server main.cpp utils.cpp message.pb.cc hdf5/ChannelFormatFileManager.cpp hdf5/RawFormatFileManager.cpp hdf5/AAVSFile.cpp -Wall -std=c++11 -D_REENTRANT -lzmq -I. -l:libprotobuf.so.9 -I$(LIBRARY_DIR) -L$(LIBRARY_DIR)/build -laccesslayer -lhdf5_cpp -lhdf5 `pkg-config --cflags QtCore --libs QtCore`

cmake_minimum_required(VERSION 2.8)

project(server)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -std=c++11 -D_REENTRANT -lzmq -I. -l:libprotobuf.so.9 -I$../library -laccesslayer")

set(SOURCE_FILES
        message.pb.cc
        message.pb.h
        utils.cpp
        utils.hpp
        zmq.hpp
        hdf5/AAVSFile.h
        hdf5/AAVSFile.cpp
        hdf5/RawFormatFileManager.cpp
        hdf5/RawFormatFileManager.h
        hdf5/FileModes.h
        hdf5/FileTypes.h
        hdf5/ChannelFormatFileManager.cpp
        hdf5/ChannelFormatFileManager.h
        )

add_executable(server main)
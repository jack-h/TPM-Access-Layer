cmake_minimum_required(VERSION 2.8)

project(server)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -std=c++11 -D_REENTRANT -lzmq -I. -l:libprotobuf.so.9 -I$../library -laccesslayer")

set(SOURCE_FILES
        message.pb.cc
        message.pb.h
        utils.cpp
        utils.hpp
        zmq.hpp
        ChannelisedDataReader.h)

add_executable(server main.cpp ChannelisedDataReader.cpp ChannelisedDataReader.h)
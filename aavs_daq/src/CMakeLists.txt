cmake_minimum_required(VERSION 2.8)

project(NetworkReceiver C CXX)

find_package(Threads REQUIRED )

# CMAKE compilation flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11 -D_REENTRANT -fPIC -g")

# Source files
set(SOURCE_FILES
        NetworkReceiver.cpp
        RingBuffer.cpp
        RealTimeThread.h
        Utils.h
        ChannelisedData.cpp
        DoubleBuffer.cpp
        AntennaData.cpp
        AntennaData.h
        BeamformedData.cpp
        BeamformedData.h
        DataConsumer.h
        Daq.h
        Daq.cpp)

# Create shared library
add_library(aavsdaq SHARED ${SOURCE_FILES} )

# Create executable
add_executable(network_receiver main.cpp)
target_link_libraries(network_receiver aavsdaq ${CMAKE_THREAD_LIBS_INIT})

# Install library
install(TARGETS "aavsdaq" DESTINATION /usr/local/lib)

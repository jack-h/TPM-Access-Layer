cmake_minimum_required(VERSION 2.8)
project(library)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++0x -D_REENTRANT -fPIC")

set(SOURCE_FILES
    AccessLayer.cpp
    AccessLayer.hpp
    Board.cpp
    Board.hpp
    Definitions.hpp
    KATCP.cpp
    KATCP.hpp
    MemoryMap.cpp
    MemoryMap.hpp
    Protocol.hpp
    RapidXML.hpp
    ROACH.cpp
    ROACH.hpp
    SPI.cpp
    SPI.hpp
    TPM.cpp
    TPM.hpp
    UCP.cpp
    UCP.hpp
    UniBoard.cpp
    UniBoard.hpp
    Utils.cpp
    Utils.hpp)

add_library(accesslayer SHARED ${SOURCE_FILES})

install(TARGETS "accesslayer" DESTINATION /usr/local/lib)

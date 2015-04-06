INSTALL_DIR  := /usr/local/lib
LIBRARY_NAME := libboard.so

layer:
	g++ -shared -fPIC -Wall -std=c++11 -o $(LIBRARY_NAME) AccessLayer.cpp Board.cpp Protocol.cpp MemoryMap.cpp Utils.cpp

install: layer
	install -D $(LIBRARY_NAME) $(INSTALL_DIR)/$(LIBRARY_NAME)  

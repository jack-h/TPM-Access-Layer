INSTALL_DIR  := /usr/local/lib
LIBRARY_NAME := libboard.so
GCC          := g++

layer:
	$(GCC) -shared -fPIC -Wall -std=c++0x -g -o $(LIBRARY_NAME) AccessLayer.cpp Board.cpp MemoryMap.cpp Utils.cpp SPI.cpp TPM.cpp UCP.cpp KATCP.cpp ROACH.cpp

install: layer
	install -D $(LIBRARY_NAME) $(INSTALL_DIR)/$(LIBRARY_NAME)

layer:
	g++ -shared -fPIC -Wall -std=c++11 -o libboard.so AccessLayer.cpp Board.cpp Protocol.cpp MemoryMap.cpp Utils.cpp

windows:
	x86_64-w64-mingw32-gcc -shared -Wall -std=c++11 -o libboard_windows.so AccessLayer.cpp Board.cpp Protocol.cpp MemoryMap.cpp Utils.cpp


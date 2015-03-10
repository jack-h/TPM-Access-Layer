layer:
	g++ -shared -fPIC -Wall -std=c++11 -o libboard.so AccessLayer.cpp Board.cpp Protocol.cpp MemoryMap.cpp Utils.cpp

main:
	g++ -o main main.cpp -lboard -L.

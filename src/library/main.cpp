//
// Created by lessju on 15/06/2015.
//

#include <iostream>
#include "AccessLayer.hpp"

using namespace std;

int main()
{
    ID id = connectBoard(TPM_BOARD, "10.0.10.2", 10000);
    RETURN err = loadFirmware(id, BOARD, "/tmp/xml_file.xml");
    std::cout << id << ", " << err << std::endl;
    err = loadSPIDevices(id, BOARD, "/tmp/spi.xml");
    std::cout << id << ", " << err << std::endl;
}


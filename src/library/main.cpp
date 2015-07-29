//
// Created by lessju on 15/06/2015.
//

#include <stdio.h>
#include "AccessLayer.hpp"
#include "Definitions.hpp"

int main()
{
    ID id = connectBoard(TPM_BOARD, "127.0.0.1", 10000);
    loadSPIDevices(id, BOARD, "/home/lessju/xilinx_map.xml");
}


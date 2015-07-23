//
// Created by lessju on 15/06/2015.
//

#include <stdio.h>
#include "AccessLayer.hpp"
#include "Definitions.hpp"

int main()
{
    ID id = connectBoard(TPM_BOARD, "10.0.10.2", 10000);

    loadFirmware(id, FPGA_1, "/home/lessju/map.xml");
    VALUES val = readDevice(id, "pll", 0x3);
    printf("%d %d\n", val.error,  val.values[0]);
}


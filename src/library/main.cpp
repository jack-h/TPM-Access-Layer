//
// Created by lessju on 15/06/2015.
//

#include "AccessLayer.hpp"
#include "Definitions.hpp"

int main()
{
    ID id = connectBoard(UNIBOARD_BOARD, "127.0.0.1", 50000);
    loadFirmwareBlocking(id, FPGA_1, "/home/lessju/Code/TPM-Access-Layer/doc/XML/uniboard_map.xml");
    loadFirmwareBlocking(id, FPGA_2, "/home/lessju/Code/TPM-Access-Layer/doc/XML/uniboard_map.xml");
    loadFirmwareBlocking(id, FPGA_3, "/home/lessju/Code/TPM-Access-Layer/doc/XML/uniboard_map.xml");
    loadFirmwareBlocking(id, FPGA_4, "/home/lessju/Code/TPM-Access-Layer/doc/XML/uniboard_map.xml");
    loadFirmwareBlocking(id, FPGA_5, "/home/lessju/Code/TPM-Access-Layer/doc/XML/uniboard_map.xml");
    loadFirmwareBlocking(id, FPGA_6, "/home/lessju/Code/TPM-Access-Layer/doc/XML/uniboard_map.xml");
    loadFirmwareBlocking(id, FPGA_7, "/home/lessju/Code/TPM-Access-Layer/doc/XML/uniboard_map.xml");
    loadFirmwareBlocking(id, FPGA_8, "/home/lessju/Code/TPM-Access-Layer/doc/XML/uniboard_map.xml");
    UINT num_registers;
    REGISTER_INFO *info = getRegisterList(id, &num_registers);
}


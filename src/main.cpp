#include "AccessLayer.hpp"

int main()
{
    // Connect to board
    ID id = connect("192.168.127.38", 10000);

    // Program board
    loadFirmwareBlocking(id, FPGA_1, "/home/lessju/Code/TPM-Access-Layer/doc/Memory Map XML Example.xml");
    ERROR loadFirmwareBlocking(ID id, FPGA fpga, char* bitstream);

    disconnect(id);

}

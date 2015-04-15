#include "AccessLayer.hpp"

#include <sys/time.h>
#include <stdio.h>

int main(void)
{
    // Connect to board
    ID id = connectBoard(ROACH_BOARD, "192.168.100.2", 7147);

    // Get list of firmware
    UINT num_firmware;
    FIRMWARE firmware = getFirmware(id, FPGA_1, &num_firmware);

    printf("Number of firmware: %d\n", num_firmware);

    // Program the board
    printf("%d\n", loadFirmwareBlocking(id, FPGA_1, "fenggbe.bof"));

    // Get list of registers
    UINT num_registers;
    REGISTER_INFO *registers = getRegisterList(id, &num_registers);

    printf("Number of registers: %d\n", num_registers);
    for(unsigned i = 0; i < num_registers; i++)
        printf("%s\n", registers[i].name);

    // Write a register value
    UINT value = 25;
    if (writeRegister(id, FPGA_1, "gbe_dest_port", &value) != SUCCESS)
        printf("Write failed!\n");
}

#include "AccessLayer.hpp"
#include <stdio.h>

int main(void)
{
    // Connect to board
    ID id = connect("10.62.14.234", 15000);

    // Program board
    loadFirmwareBlocking(id, FPGA_1, "/home/lessju/Memory Map XML Example.xml");

    // Get register list
    unsigned int num_registers;
    REGISTER_INFO *list = getRegisterList(id, &num_registers);
    
    // Read a register value
    VALUE val = getRegisterValue(id, list[10].device, list[10].name);
    if (val.error == FAILURE)
        printf("Main. Unable to get register value\n");  
    else
        printf("Main. Register value is %d\n", val.value);  

    // Write a regster value
    if (setRegisterValue(id, list[7].device, list[7].name, 69) == FAILURE)
        printf("Main. Unable to set register value\n");

    disconnect(id);

}

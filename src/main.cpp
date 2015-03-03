#include "AccessLayer.hpp"

#include <sys/time.h>
#include <stdio.h>

// Test performance
void testPerformance(ID id, REGISTER_INFO *registers)
{
    // Start timing
    struct timeval start, end;
    long seconds, useconds;    
    gettimeofday(&start, NULL);

    int times = 1000;

    // Repeatedly read from register
    for(unsigned i = 0; i < times; i++)
    {  
        readRegister(id, registers[0].device, registers[0].name, 32);
    }

    gettimeofday(&end, NULL);
    seconds  = end.tv_sec  - start.tv_sec;
    useconds = end.tv_usec - start.tv_usec;

    float mtime = ((end.tv_sec - start.tv_sec) * 1e6 + (end.tv_usec - start.tv_usec)) / 1000.0;
    printf("Time: %.2lf ms, Reads per second: %f\n", mtime, 1.0 / (mtime / ((float) times * 1000.0)));
}

int main(void)
{
    // Connect to board
    ID id = connectBoard("10.62.14.249", 10000);

    // Program board
    loadFirmwareBlocking(id, FPGA_1, "/home/lessju/XilinxBoardMap.xml");

    // Get register list
    unsigned int num_registers;
    REGISTER_INFO *list = getRegisterList(id, &num_registers);
    
    // Read a register value
//    VALUES val = readRegister(id, list[0].device, list[0].name, 1);
//    if (val.error == FAILURE)
//        printf("Main. Unable to get register value\n");  
//    else
//        printf("Main. Register value is %d\n", val.values[0]);  

//    // Write a regster value
//    uint32_t value = 69;
//    if (writeRegister(id, list[7].device, list[7].name, 1, &value) == FAILURE)
//        printf("Main. Unable to set register value\n");

    testPerformance(id, list);

    disconnectBoard(id);

}

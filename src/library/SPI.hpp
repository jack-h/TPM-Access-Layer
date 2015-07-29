#ifndef SPI_DEVICES
#define SPI_DEVICES

#include "Definitions.hpp"
#include <utility>
#include <string>
#include <map>

class SPI
{
    public:
        // SPI constructor accepting filepath
        SPI(const char *filepath);

        // Get SPI device list
        SPI_DEVICE_INFO* getSPIList(UINT *num_devices);
    
        // Get device information
        std::pair<int, int> getSPIInfo(REGISTER device);

    public:
        UINT spi_address;
        UINT spi_address_mask;
        UINT write_data;
        UINT write_data_mask;
        UINT read_data;
        UINT read_data_mask;    
        UINT chip_select;
        UINT chip_select_mask;
        UINT sclk;
        UINT sclk_mask;
        UINT cmd_address;
        UINT cmd_start_mask;
        UINT cmd_rnw_mask;

    private:
        char                                           *filepath;  // Store filepath to SPI Devices XML file
        std::map<std::string, std::pair<int, int> >  spi_map;    // SPI device map (spi_en, spi_sclk)
};

#endif // SPI_DEVICES

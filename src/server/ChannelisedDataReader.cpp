/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

/*
 * File:   ChannelisedDataReader.cpp
 * Author: andrea
 *
 * Created on November 20, 2015, 10:51 AM
 */

#include "ChannelisedDataReader.h"

ChannelisedDataReader::ChannelisedDataReader(string filename) {
    this -> filename = filename;
}

int ChannelisedDataReader::getData(complex_t *buffer, uint16_t antenna, uint16_t polarization, uint32_t nof_samples, uint32_t nof_channels)
{
    try{
        // Create output buffer
        complex_t *internal_buffer;
        internal_buffer = new complex_t[nof_samples];

        // File string name
        H5std_string FILE_NAME(this->filename);
        // Dataset name
        H5std_string DATASET_NAME("data");

        // Open the specified file and the specified dataset in the file.
        H5File file(FILE_NAME, H5F_ACC_RDONLY);

        //Group channel_group, antenna_group;
        for(unsigned channel = 0; channel < nof_channels; channel++)
        {
            cout << "CHANNEL: [" << channel << "]" << endl;

            H5std_string CHN_GROUP_NAME("channel_"+NumberToString(channel));
            H5std_string ANT_GROUP_NAME("antenna_"+NumberToString(antenna));
            H5std_string POL_GROUP_NAME("polarity_"+NumberToString(polarization));


            Group channel_group = Group(file.openGroup(CHN_GROUP_NAME));
            Group antenna_group = channel_group.openGroup(ANT_GROUP_NAME);
            Group pol_group = antenna_group.openGroup(POL_GROUP_NAME);
            DataSet dataset = pol_group.openDataSet(DATASET_NAME);

            DataSpace dataspace = dataset.getSpace();
            dataspace.selectAll();

            hsize_t dimsm[1];              /* memory space dimensions */
            dimsm[0] = nof_samples;
            DataSpace memspace(1, dimsm);
            memspace.selectAll();

            DataType datatype = dataset.getDataType();

            //dataset.read(internal_buffer, datatype, memspace, dataspace);
            memcpy(buffer+(channel * nof_samples), internal_buffer, nof_samples * sizeof(complex_t));
        }
        return 0;
    }
    catch(...){
        printf("Error.\n");
        return -1;
    }
}

ChannelisedDataReader::ChannelisedDataReader(const ChannelisedDataReader& orig) {
}

ChannelisedDataReader::~ChannelisedDataReader() {
}

string ChannelisedDataReader::NumberToString(int number){
    stringstream ss;
    ss << number;
    return ss.str();
}
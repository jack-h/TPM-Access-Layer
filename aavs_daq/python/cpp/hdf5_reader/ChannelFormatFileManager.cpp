/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

/* 
 * File:   ChannelFormatFileManager.cpp
 * Author: andrea
 * 
 * Created on November 30, 2015, 10:28 AM
 */

#include "ChannelFormatFileManager.h"

ChannelFormatFileManager::ChannelFormatFileManager(string root_path, int mode) : AAVSFile(root_path, mode) {
    this->type = FileTypes::CHANNEL;
}

ChannelFormatFileManager::ChannelFormatFileManager(const ChannelFormatFileManager& orig) {
}

ChannelFormatFileManager::~ChannelFormatFileManager() {
}

complex16_t* ChannelFormatFileManager::read_data(string timestamp, vector<int> channels, vector<int> antennas, vector<int> polarizations, int n_samples, int sample_offset) {

    // Create output buffer
    int num_channels = channels.size();
    int num_antennas = antennas.size();
    int num_polarizations = polarizations.size();
    complex16_t *output_buffer = new complex16_t[num_channels * num_antennas * num_polarizations * n_samples];

    H5File file;
    try {
        file = this->loadFile(timestamp);
        H5std_string DATASET_NAME("root");
        DataSet root_dataset = file.openDataSet(DATASET_NAME);
    } catch (Exception e) {
        cout << "Can't load file: " << e.getDetailMsg() << endl;
        delete[] output_buffer;
        return NULL;
    }

    try {
        // Dataset name
        H5std_string DATASET_NAME("data");

        //Group channel_group, antenna_group;
        for (unsigned channel_idx = 0; channel_idx < num_channels; channel_idx++) {
            H5std_string CHN_GROUP_NAME("channel_" + NumberToString(channels[channel_idx]));
            Group channel_group = Group(file.openGroup(CHN_GROUP_NAME));
            DataSet dataset = channel_group.openDataSet(DATASET_NAME);

            int total_items = this->n_samples;
            int gather_samples = 0;
            if (sample_offset + n_samples > total_items) {
                gather_samples = total_items;
            } else {
                gather_samples = n_samples;
            }

            // Create internal buffer
            complex16_t internal_buffer[gather_samples];
            for (unsigned i = 0; i < gather_samples; i++) {
                internal_buffer[i].real = 0;
                internal_buffer[i].imag = 0;
            }

            for (unsigned antenna_idx = 0; antenna_idx < num_antennas; antenna_idx++) {
                int current_antenna = antennas[antenna_idx];
                for (unsigned polarization_idx = 0; polarization_idx < num_polarizations; polarization_idx++) {
                    int current_polarization = polarizations[polarization_idx];

                    hsize_t offset[2], count[2];
                    hsize_t offset_out[1], count_out[1];
                    hsize_t dimsm[1];

                    // Specify size and shape of subset to read. 
                    offset[0] = (current_antenna * this->n_pols) + current_polarization;
                    offset[1] = sample_offset;

                    count[0] = 1;
                    count[1] = gather_samples;

                    // Specify size and shape of subset to write. 
                    offset_out[0] = 0;
                    count_out[0] = gather_samples;

                    //Define memory space
                    dimsm[0] = gather_samples;
                    int RANK = 1;
                    DataSpace memspace(RANK, dimsm, NULL);
                    //Define hyperslab in the memory space.
                    memspace.selectHyperslab(H5S_SELECT_SET, count_out, offset_out);

                    //Define hyperslab in the dataset. 
                    DataSpace dataspace = dataset.getSpace();
                    dataspace.selectHyperslab(H5S_SELECT_SET, count, offset);
                    hssize_t n_points = dataspace.getSelectNpoints();

                    DataType datatype = dataset.getDataType();
                    dataset.read(internal_buffer, datatype, memspace, dataspace);
                    cout << "Antenna: " << current_antenna << " Polarization: " << current_polarization << " Offset: " << (current_antenna * this->n_pols) + current_polarization << endl;

                    int channel_skip = (channel_idx * num_antennas * num_polarizations * n_samples);
                    int antenna_skip = (antenna_idx * num_polarizations * n_samples);
                    int pol_skip = (polarization_idx * n_samples);

                    //                int channel_skip = (channel_idx * this->n_antennas * this->n_pols * this->n_samples);
                    //                int antenna_skip = (antenna_idx * this->n_pols * this->n_samples);
                    //                int pol_skip = (polarization_idx * this->n_samples);

                    int output_offset = channel_skip + antenna_skip + pol_skip;
                    //cout << output_offset << endl;
                    memcpy(output_buffer + output_offset, internal_buffer, gather_samples * sizeof (complex16_t));
                }
            }
        }
        return output_buffer;
    } catch (Exception e) {
        cout << "Error during read(): " << e.getDetailMsg() << endl;
        delete[] output_buffer;
        return NULL;
    }
}
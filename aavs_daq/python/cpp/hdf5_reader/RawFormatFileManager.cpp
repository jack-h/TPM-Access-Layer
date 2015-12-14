/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

/* 
 * File:   RawFormatFileManager.cpp
 * Author: andrea
 * 
 * Created on December 14, 2015, 11:28 AM
 */

#include "RawFormatFileManager.h"

RawFormatFileManager::RawFormatFileManager(string root_path, int mode): AAVSFile(root_path, mode) {
    this->type = FileTypes::RAW;
}

RawFormatFileManager::RawFormatFileManager(const RawFormatFileManager& orig) {
}

RawFormatFileManager::~RawFormatFileManager() {
}

int8_t* RawFormatFileManager::read_data(string timestamp, int antennas[], int polarizations[], int n_samples, int sample_offset){
 
    // Create output buffer
    int num_antennas = sizeof(antennas)/sizeof(antennas[0]);
    int num_polarizations = sizeof(polarizations)/sizeof(polarizations[0]);  
    int8_t *output_buffer = new int8_t[num_antennas*num_polarizations*n_samples];    

    H5File file;
    try
    {
        file = this->loadFile(timestamp);
        H5std_string DATASET_NAME("root");   
        DataSet root_dataset = file.openDataSet(DATASET_NAME);    
    }
    catch (Exception e)
    {
        cout << "Can't load file: " << e.getDetailMsg() << endl;
        return output_buffer;
    }

    // Group name
    H5std_string RAW_GROUP_NAME("raw_");

    // Dataset name
    H5std_string DATASET_NAME("data");

    Group raw_group = Group(file.openGroup(RAW_GROUP_NAME));
    DataSet dataset = raw_group.openDataSet(DATASET_NAME);

    int total_items = this->n_samples;
    int gather_samples = 0;
    if (sample_offset + n_samples > total_items){
        gather_samples = total_items;
    }else{
        gather_samples = n_samples;
    }
  
    // Create internal buffer
    int8_t internal_buffer[gather_samples];
    for (unsigned i = 0; i < gather_samples; i++){
        internal_buffer[i] = 0;
    }  
          
    for(unsigned antenna_idx = 0; antenna_idx < num_antennas; antenna_idx++){
        int current_antenna = antennas[antenna_idx];            
        for(unsigned polarization_idx = 0; polarization_idx < num_polarizations; polarization_idx++){
            int current_polarization = polarizations[polarization_idx];                

            hsize_t offset[2], count[2];
            hsize_t offset_out[1], count_out[1];
            hsize_t dimsm[1];

            // Specify size and shape of subset to read. 
            offset[0] = (current_antenna * this->n_pols)+current_polarization;
            offset[1] = sample_offset;

            count[0]  = 1;
            count[1]  = gather_samples;

            // Specify size and shape of subset to write. 
            offset_out[0] = 0;
            count_out[0]  = gather_samples;

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
            cout << "Antenna: " << current_antenna << " Polarization: " << current_polarization << " Offset: " <<  (current_antenna * this->n_pols)+current_polarization << endl;

            int antenna_skip = (antenna_idx * num_polarizations * n_samples);
            int pol_skip = (polarization_idx * n_samples);


            int output_offset = antenna_skip + pol_skip;
            //cout << output_offset << endl;
            memcpy(output_buffer+output_offset, internal_buffer, gather_samples * sizeof (int8_t));               
        }       
    }
  return output_buffer;
}

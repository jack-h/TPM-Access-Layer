/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

/* 
 * File:   main.cpp
 * Author: andrea
 *
 * Created on November 20, 2015, 10:38 AM
 */

#include <cstdlib>
#include "ChannelFormatFileManager.h"
#include "RawFormatFileManager.h"
#include "AAVSFile.h"
using namespace std;

/*
 * 
 */
int main(int argc, char** argv) {   
    int antennas[2] = {0,1};
    int polarizations[2] = {0,1};
    int channels[2] = {0,1};
    int sample_offset = 0;
    int n_samples = 128;
    
    int num_channels = sizeof(channels)/sizeof(channels[0]);
    int num_antennas = sizeof(antennas)/sizeof(antennas[0]);
    int num_polarizations = sizeof(polarizations)/sizeof(polarizations[0]);     
    
    ChannelFormatFileManager ch_fmgr = ChannelFormatFileManager("/media/andrea/hdf5", FileModes::READ);
    complex16_t *output_channel = ch_fmgr.read_data("0",channels,antennas,polarizations,n_samples,sample_offset);  
    for(unsigned i = 0; i < num_channels*num_antennas*num_polarizations*n_samples; i++){
        cout << "[" << i << "] " << static_cast<int>(output_channel[i].real) << ", " << static_cast<int>(output_channel[i].imag) << endl;
    }
    
    RawFormatFileManager rw_fmgr = RawFormatFileManager("/media/andrea/hdf5", FileModes::READ);
    int8_t *output_raw = rw_fmgr.read_data("0",antennas,polarizations,n_samples,sample_offset);  
    for(unsigned i = 0; i < num_antennas*num_polarizations*n_samples; i++){
        cout << "[" << i << "] " << static_cast<int>(output_raw[i]) << endl;
    }
}


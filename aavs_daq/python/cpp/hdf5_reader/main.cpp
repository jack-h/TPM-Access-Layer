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
    vector<int> antennas(2); antennas[0]=1; antennas[1]=1;
    vector<int> polarizations(2); polarizations[0]=0; polarizations[1]=1;
    vector<int> channels(2); channels[0]=0; channels[1]=1;
    
    //int antennas[2] = {0,1};
    //int polarizations[2] = {0,1};
    //int channels[2] = {0,1};
    int sample_offset = 0;
    int n_samples = 1024;
    
    int num_channels = channels.size();
    int num_antennas = antennas.size();
    int num_polarizations = polarizations.size();     
    
    ChannelFormatFileManager ch_fmgr = ChannelFormatFileManager("/media/andrea/hdf5", FileModes::READ);
    complex16_t *output_channel = ch_fmgr.read_data("378.0",channels,antennas,polarizations,n_samples,sample_offset);  
    for(unsigned i = 0; i < num_channels*num_antennas*num_polarizations*n_samples; i++){
        cout << "[" << i << "] " << static_cast<int>(output_channel[i].real) << ", " << static_cast<int>(output_channel[i].imag) << endl;
    }
    
//    RawFormatFileManager rw_fmgr = RawFormatFileManager("/media/andrea/hdf5", FileModes::READ);
//    int8_t *output_raw = rw_fmgr.read_data("0",antennas,polarizations,n_samples,sample_offset);  
//    for(unsigned i = 0; i < num_antennas*num_polarizations*n_samples; i++){
//        cout << "[" << i << "] " << static_cast<int>(output_raw[i]) << endl;
//    }    
//        
//    // passing an empty timestamp
//    RawFormatFileManager rw_fmgr2 = RawFormatFileManager("/media/andrea/hdf5", FileModes::READ);
//    int8_t *output_raw2 = rw_fmgr2.read_data("",antennas,polarizations,n_samples,sample_offset);  
//    for(unsigned i = 0; i < num_antennas*num_polarizations*n_samples; i++){
//        cout << "[" << i << "] " << static_cast<int>(output_raw2[i]) << endl;
//    }
}


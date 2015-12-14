/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

/* 
 * File:   AAVSFile.cpp
 * Author: andrea
 * 
 * Created on December 14, 2015, 1:16 PM
 */

#include "AAVSFile.h"

AAVSFile::AAVSFile(string root_path, int mode) {
    this->root_path = root_path;
    this->mode = mode;
}

AAVSFile::AAVSFile(const AAVSFile& orig) {
}

AAVSFile::~AAVSFile() {
}

void AAVSFile::closeFile(H5File file){
    file.close();
}

H5File AAVSFile::loadFile(string timestamp){
    QString filename_prefix;
    QString full_filename;
    QString qstr_timestamp = QString::fromStdString(timestamp);
    
    if (this->type == FileTypes::RAW) {
        filename_prefix = "raw_";
    }
    else if (this->type == FileTypes::CHANNEL){
        filename_prefix = "channel_";
    }
    else if (this->type == FileTypes::BEAM){
        filename_prefix = "beamformed_";
    }
    
    if(timestamp.empty()){
        QStringList nameFilter("*.hdf5");      
        QDir directory(QString::fromStdString(this->root_path));
        QStringList hdf5list = directory.entryList(nameFilter);
        for(unsigned file_idx = 0; file_idx < hdf5list.length(); file_idx++){
            QString filename = hdf5list.at(file_idx);
            if (filename.startsWith(filename_prefix)){
                full_filename = directory.absoluteFilePath(filename);
                break;
            }
        }        
    }else{
        full_filename = QDir(QString::fromStdString(this->root_path)).filePath(filename_prefix + qstr_timestamp + ".hdf5");        
    }
       
    bool file_read = false;
    uint slept_time = 0;
    if(!full_filename.isEmpty()){
        try{
            // File string name
            H5std_string FILE_NAME(full_filename.toStdString());
            // Open the specified file and the specified dataset in the file.
            H5File file(FILE_NAME, H5F_ACC_RDWR);
            // Dataset name
            H5std_string DATASET_NAME("root");            
            while ((file_read==false) && (slept_time < 5)){
                if (this->checkRootIntegrity(file)){
                    DataSet root_dataset = file.openDataSet(DATASET_NAME);

                    Attribute n_antennas_attr = root_dataset.openAttribute("n_antennas");
                    Attribute n_pols_attr = root_dataset.openAttribute("n_pols");
                    Attribute n_stations_attr = root_dataset.openAttribute("n_stations");
                    Attribute n_beams_attr = root_dataset.openAttribute("n_beams");
                    Attribute n_tiles_attr = root_dataset.openAttribute("n_tiles");
                    Attribute n_chans_attr = root_dataset.openAttribute("n_chans");
                    Attribute n_samples_attr = root_dataset.openAttribute("n_samples");
                    DataType type = n_antennas_attr.getDataType();

                    n_antennas_attr.read(type,&this->n_antennas);
                    n_pols_attr.read(type,&this->n_pols);
                    n_stations_attr.read(type,&this->n_stations);
                    n_beams_attr.read(type,&this->n_beams);
                    n_tiles_attr.read(type,&this->n_tiles);
                    n_chans_attr.read(type,&this->n_chans);
                    n_samples_attr.read(type,&this->n_samples);

                    file_read = true;                 
                }else{
                    cout << slept_time << " - Waiting for file integrity checks in " + full_filename.toStdString();
                    this->sleepcp(1000);
                    slept_time++;            
                }            
            }
            if (file_read == false){
                throw "Requested file is either corrupt, or perpetually unavailable for further processing.";
            }else{
                return file;
            }
        }catch (Exception e){
        }
    }
}

void AAVSFile::sleepcp(int milliseconds){ // cross-platform sleep function
    #ifdef WIN32
    Sleep(milliseconds);
    #else
    usleep(milliseconds * 1000);
    #endif // win32
}

bool AAVSFile::checkRootIntegrity(H5File file){
    bool integrity = true;
    try{
        DataSet root_dataset;
        // check for root dataset in file
        try {  // to determine if the dataset exists in the group
            root_dataset = DataSet(file.openDataSet("root"));
            uint n_attrs = root_dataset.getNumAttrs();
            if (n_attrs >= 9){ // if this test passes, then all attributes should be there, but checks will start
                try{
                    Attribute n_antennas_attr = root_dataset.openAttribute("n_antennas");
                    Attribute n_pols_attr = root_dataset.openAttribute("n_pols");
                    Attribute n_stations_attr = root_dataset.openAttribute("n_stations");
                    Attribute n_beams_attr = root_dataset.openAttribute("n_beams");
                    Attribute n_tiles_attr = root_dataset.openAttribute("n_tiles");
                    Attribute n_chans_attr = root_dataset.openAttribute("n_chans");
                    Attribute n_samples_attr = root_dataset.openAttribute("n_samples");
                    
                    return integrity;
                }catch (AttributeIException not_found_error){
                    integrity = false; 
                    return integrity;                    
                }
            }
            else{
                integrity = false;
                return integrity;
            }
        }catch( GroupIException not_found_error ) {
            integrity = false;
        }
    }catch (Exception e){
        integrity = false;
        return integrity;
    }
    return integrity;
}

string AAVSFile::NumberToString(int number){
    stringstream ss;
    ss << number;
    return ss.str();
}


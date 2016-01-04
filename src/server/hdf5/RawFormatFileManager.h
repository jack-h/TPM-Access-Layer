/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

/* 
 * File:   RawFormatFileManager.h
 * Author: andrea
 *
 * Created on December 14, 2015, 11:28 AM
 */

#ifndef RAWFORMATFILEMANAGER_H
#define RAWFORMATFILEMANAGER_H

#include "AAVSFile.h"
class RawFormatFileManager: public AAVSFile {
public:   
    RawFormatFileManager(string root_path=".", int mode = FileModes::READ);
    RawFormatFileManager(const RawFormatFileManager& orig);
    virtual ~RawFormatFileManager();
    int8_t* read_data(string timestamp, int antennas[], int polarizations[], int n_samples, int sample_offset = 0);

private:    
};

#endif /* RAWFORMATFILEMANAGER_H */


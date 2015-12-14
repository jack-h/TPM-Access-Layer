/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

/* 
 * File:   ChannelFormatFileManager.h
 * Author: andrea
 *
 * Created on November 30, 2015, 10:28 AM
 */

#ifndef CHANNELFORMATFILEMANAGER_H
#define CHANNELFORMATFILEMANAGER_H

#include "AAVSFile.h"

typedef struct {
    int8_t   real;
    int8_t   imag;
} complex16_t;


class ChannelFormatFileManager: public AAVSFile{
public:
    ChannelFormatFileManager(string root_path=".", int mode = FileModes::READ);
    ChannelFormatFileManager(const ChannelFormatFileManager& orig);
    virtual ~ChannelFormatFileManager();    
    complex16_t* read_data(string timestamp, int channels[], int antennas[], int polarizations[], int n_samples=0, int sample_offset=0);
private:
};

#endif /* CHANNELFORMATFILEMANAGER_H */


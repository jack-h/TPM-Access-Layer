/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

/*
 * File:   ChannelisedDataReader.h
 * Author: andrea
 *
 * Created on November 20, 2015, 10:51 AM
 */

#ifndef CHANNELISEDDATAREADER_H
#define CHANNELISEDDATAREADER_H

#ifdef OLD_HEADER_FILENAME
#include <iostream.h>
#else
#include <iostream>
#endif

#ifndef H5_NO_NAMESPACE
#ifndef H5_NO_STD
using std::cout;
using std::endl;
#endif  // H5_NO_STD
#endif

#include "H5Cpp.h"

#ifndef H5_NO_NAMESPACE
using namespace H5;
#endif

#include <string>
#include <iostream>     // std::cout
#include <sstream>      // std::stringstream, std::stringbuf
#include <cstdlib>
#include <complex>
#include <cstring>
using namespace std;

typedef struct {
    float   real;
    float   imag;
} complex_t;

class ChannelisedDataReader {
public:
    ChannelisedDataReader(string filename);
    ChannelisedDataReader(const ChannelisedDataReader& orig);
    virtual ~ChannelisedDataReader();
    int getData(complex_t *buffer, uint16_t antenna, uint16_t polarization, uint32_t nof_samples, uint32_t nof_channels);
private:
    string filename;
    string NumberToString(int number);
};

#endif /* CHANNELISEDDATAREADER_H */

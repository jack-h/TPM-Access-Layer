/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

/* 
 * File:   AAVSFile.h
 * Author: andrea
 *
 * Created on December 14, 2015, 1:16 PM
 */

#ifndef AAVSFILE_H
#define AAVSFILE_H

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
#include <QDir>
#include <QStringList>
#include <QString>
#include <iostream>
#include <stdint.h>
#include <vector>

#ifdef WIN32
#include <windows.h>
#else
#include <unistd.h>
#endif // win32
    
#include <time.h>   
using namespace std; 

#include "FileTypes.h"
#include "FileModes.h"

//enum FileTypes{RAW, CHANNEL, BEAM};
//enum FileModes{READ, WRITE};

class AAVSFile {
public:
    AAVSFile(string root_path=".", int mode = FileModes::READ);
    AAVSFile(const AAVSFile& orig);
    virtual ~AAVSFile();
    void closeFile(H5File file);
    H5File loadFile(string timestamp=NULL);     

protected:
    bool checkRootIntegrity(H5File file);
    string NumberToString(int number);
    void sleepcp(int milliseconds);// cross-platform sleep function
   
    string root_path;
    int type;
    int mode;
    
    int n_antennas;
    int n_pols;
    int n_stations;
    int n_beams;
    int n_tiles;
    int n_chans;
    int n_samples;     
};

#endif /* AAVSFILE_H */


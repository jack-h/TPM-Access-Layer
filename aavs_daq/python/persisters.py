__author__ = 'Alessio Magro'

from matplotlib import pyplot as plt
from abc import abstractmethod
from enum import Enum
import numpy
import h5py
import math

class FileTypes(Enum):
    Raw = 1
    Channel = 2
    Beamformed = 3


class FileModes(Enum):
    Read = 1
    Write = 2

# --------------------------------------------------------- AAVS FILE --------------------------------------------------
class AAVSFileManager(object):
    # Class constructor

    def __init__(self, root_path = '', type = None, mode = FileModes.Read):
        self.type = type
        self.root_path = root_path
        self.mode = mode

        # if mode == FileModes.Read:
        #     self.file = h5py.File(path, 'r')
        # elif mode == FileModes.Write:
        #     self.file = h5py.File(path, 'w')
        # self.main_dset = self.file.create_dataset("root", (1,), chunks=True,  dtype='float16')

    @abstractmethod
    def configure(self, file):
        pass

    def set_metadata(self, n_antennas = 16, n_pols = 2, n_stations = 1, n_beams = 1, n_tiles = 1, n_chans = 512, n_samples = 0):
        self.n_antennas = n_antennas
        self.n_pols = n_pols
        self.n_stations = n_stations
        self.n_beams = n_beams
        self.n_tiles = n_tiles
        self.n_chans = n_chans
        self.n_samples = n_samples

    @abstractmethod
    def ingest_data(self, data_ptr = None, timestamp = 0, append=False):
        """Method documentation"""
        pass


    def load_file(self, timestamp = 0):
        if self.type == FileTypes.Raw:
            filename_suffix = "_raw.hdf5"
        elif self.type == FileTypes.Channel:
            filename_suffix = "_channel.hdf5"
        elif self.type == FileTypes.Beamformed:
            filename_suffix = "_beamformed.hdf5"

        full_filename = self.root_path + "/" + str(timestamp) + filename_suffix

        file = h5py.File(full_filename, 'r+')

        self.main_dset = file["root"]

        self.n_antennas = self.main_dset.attrs['n_antennas']
        self.n_pols = self.main_dset.attrs['n_pols']
        self.n_stations = self.main_dset.attrs['n_stations']
        self.n_beams = self.main_dset.attrs['n_beams']
        self.n_tiles = self.main_dset.attrs['n_tiles']
        self.n_chans = self.main_dset.attrs['n_chans']
        self.n_samples = self.main_dset.attrs['n_samples']

        return file

    def create_file(self, timestamp = 0):
        if self.type == FileTypes.Raw:
            filename_suffix = "_raw.hdf5"
        elif self.type == FileTypes.Channel:
            filename_suffix = "_channel.hdf5"
        elif self.type == FileTypes.Beamformed:
            filename_suffix = "_beamformed.hdf5"

        full_filename = self.root_path + "/" + str(timestamp) + filename_suffix

        if self.mode == FileModes.Read:
            file = h5py.File(full_filename, 'r')
        elif self.mode == FileModes.Write:
            file = h5py.File(full_filename, 'w')

        self.main_dset = file.create_dataset("root", (1,), chunks=True,  dtype='float16')

        self.main_dset.attrs['n_antennas'] = self.n_antennas
        self.main_dset.attrs['n_pols'] = self.n_pols
        self.main_dset.attrs['n_stations'] = self.n_stations
        self.main_dset.attrs['n_beams'] = self.n_beams
        self.main_dset.attrs['n_tiles'] = self.n_tiles
        self.main_dset.attrs['n_chans'] = self.n_chans
        self.main_dset.attrs['n_samples'] = self.n_samples
        self.main_dset.attrs['type'] = self.type.value

        self.configure(file)
        return file

    def close_file(self, file):
        file.close()

# --------------------------------------------------------- BEAM FILE --------------------------------------------------
class BeamFormatFileManager(AAVSFileManager):

    # Class constructor
    def __init__(self, root_path = '', mode = FileModes.Read):
        super(BeamFormatFileManager, self).__init__(root_path=root_path, type=FileTypes.Beamformed, mode=mode)
        self.ctype = numpy.dtype([('real', numpy.int8), ('imag', numpy.int8)])

    def configure(self, file):
        n_pols = self.main_dset.attrs['n_pols']
        n_samp = self.main_dset.attrs['n_samples']
        n_chans = self.main_dset.attrs['n_chans']
        for polarity in xrange(0, n_pols):
            polarity_grp = file.create_group("polarity_"+str(polarity))
            polarity_grp.create_dataset("data", (n_chans,0), chunks=(n_chans,n_samp), dtype=self.ctype, maxshape=(n_chans,None))

    def read_data(self, timestamp=0, channels=[], polarizations=[], n_samples=0):
        try:
            file = self.load_file(timestamp)
        except:
            print "Can't load file"

        output_buffer = numpy.zeros([len(polarizations),len(channels), n_samples],dtype=self.ctype)

        for polarization_idx in xrange(0, len(polarizations)):
            current_polarization = polarizations[polarization_idx]
            polarization_grp = file["polarity_" + str(current_polarization)]
            dset = polarization_grp["data"]
            nof_items = dset[0].size
            for channel_idx in xrange(0, len(channels)):
                current_channel = channels[channel_idx]
                if n_samples > nof_items:
                    output_buffer[polarization_idx,channel_idx,:] = dset[current_channel,0:nof_items]
                else:
                    output_buffer[polarization_idx,channel_idx,:] = dset[current_channel,0:n_samples]
        return output_buffer

    def ingest_data(self, data_ptr=None, timestamp=0, append=False):
        if append:
            try:
                file = self.load_file(timestamp)
            except:
                file = self.create_file(timestamp)
        else:
            file = self.create_file(timestamp)

        n_pols = self.main_dset.attrs['n_pols']
        n_samp = self.main_dset.attrs['n_samples']
        n_chans = self.main_dset.attrs['n_chans']
        self.main_dset.attrs['timestamp'] = timestamp
        for polarization in xrange(0, n_pols):
            polarization_grp = file["polarity_"+str(polarization)]
            dset = polarization_grp["data"]
            ds_last_size = dset[0].size
            if append:
                dset.resize(ds_last_size+n_samp, axis=1) #resize to fit new data
            else:
                dset.resize(n_samp, axis=1) #resize for only one fit

            for channel in xrange(0, n_chans):
                start_idx = (polarization * n_chans * n_samp) + channel
                end_idx = (polarization + 1) * n_chans * n_samp

                if append:
                    dset[channel, ds_last_size:ds_last_size+n_samp] = data_ptr[start_idx : end_idx : n_chans]
                else:
                    dset[channel,:] = data_ptr[start_idx : end_idx : n_chans]
        file.flush()
        self.close_file(file)

# ------------------------------------------------------- CHANNEL FILE -------------------------------------------------
class ChannelFormatFileManager(AAVSFileManager):

    # Class constructor
    def __init__(self, root_path = '', mode = FileModes.Read):
        super(ChannelFormatFileManager, self).__init__(root_path=root_path, type=FileTypes.Channel, mode=mode)
        self.ctype = numpy.dtype([('real', numpy.int8), ('imag', numpy.int8)])

    def complex_abs(self, value):
        return math.sqrt(value[0] ** 2) + (value[1] ** 2)

    def configure(self, file):
        n_pols = self.main_dset.attrs['n_pols']
        n_antennas = self.main_dset.attrs['n_antennas']
        n_samp = self.main_dset.attrs['n_samples']
        n_chans = self.main_dset.attrs['n_chans']
        for channel in xrange(0, n_chans):
            channel_grp = file.create_group("channel_"+str(channel))
            for antenna in xrange(0, n_antennas):
                antenna_subgrp = channel_grp.create_group("antenna_"+str(antenna))
                antenna_subgrp.create_dataset("data", (n_pols,0), chunks=(n_pols,n_samp), dtype=self.ctype, maxshape=(n_pols,None))
        file.flush()

    def plot(self, data_in=None, timestamp=0, channels=[], antennas=[], polarizations=[], n_samples=0):
        complex_func = numpy.vectorize(self.complex_abs)
        # output_buffer[channel_idx,antenna_idx,polarization_idx,:] = dset[0:n_samples]
        if data_in is None:
            data = self.read_data(timestamp=timestamp, channels=channels, antennas=antennas, polarizations=polarizations, n_samples=n_samples)
        else:
            data = data_in

        total_plots = len(antennas) * len(polarizations)
        plot_cnt = 1
        for antenna_idx in xrange(0, len(antennas)):
            current_antenna = antennas[antenna_idx]
            for polarization_idx in xrange(0, len(polarizations)):
                current_polarization = polarizations[polarization_idx]
                subplot = plt.subplot(total_plots/2, 2, plot_cnt)
                subplot.set_title("Antenna: " + str(current_antenna) + " - Polarization: " + str(current_polarization), fontsize=9)
                plt.xlabel('Time (sample)')
                plt.ylabel('Channel')

                sub_data = complex_func(data[:,antenna_idx,polarization_idx,:])
                plt.imshow(sub_data, aspect='auto',  origin='lower')
                #plt.yticks(channels)
                plot_cnt += 1
        plt.show()

    def read_data(self, timestamp=0, channels=[], antennas=[], polarizations=[], n_samples=0):
        try:
            file = self.load_file(timestamp)
        except:
            print "Can't load file"

        output_buffer = numpy.zeros([len(channels),len(antennas),len(polarizations), n_samples],dtype=self.ctype)

        for channel_idx in xrange(0, len(channels)):
            current_channel = channels[channel_idx]
            channel_grp = file["channel_" + str(current_channel)]
            for antenna_idx in xrange(0, len(antennas)):
                current_antenna = antennas[antenna_idx]
                antenna_subgrp = channel_grp["antenna_" + str(current_antenna)]
                dset = antenna_subgrp["data"]
                nof_items = dset[0].size
                for polarization_idx in xrange(0, len(polarizations)):
                    current_polarization = polarizations[polarization_idx]
                    if n_samples > nof_items:
                        output_buffer[channel_idx,antenna_idx,polarization_idx,:] = dset[current_polarization,0:nof_items]
                    else:
                        output_buffer[channel_idx,antenna_idx,polarization_idx,:] = dset[current_polarization,0:n_samples]
        return output_buffer

    def ingest_data(self, data_ptr=None, timestamp=0, append=False):
        if append:
            try:
                file = self.load_file(timestamp)
            except:
                file = self.create_file(timestamp)
        else:
            file = self.create_file(timestamp)

        n_pols = self.main_dset.attrs['n_pols']
        n_antennas = self.main_dset.attrs['n_antennas']
        n_samp = self.main_dset.attrs['n_samples']
        n_chans = self.main_dset.attrs['n_chans']
        self.main_dset.attrs['timestamp'] = timestamp
        for channel in xrange(0, n_chans):
            channel_grp = file["channel_" + str(channel)]
            for antenna in xrange(0, n_antennas):
                antenna_subgrp = channel_grp["antenna_" + str(antenna)]
                dset = antenna_subgrp["data"]
                ds_last_size = dset[0].size
                if append:
                    dset.resize(ds_last_size+n_samp, axis=1) #resize to fit new data
                else:
                    dset.resize(n_samp, axis=1) #resize for only one fit

                for polarization in xrange(0, n_pols):
                    start_idx = (channel * n_samp * n_pols * n_antennas) + (n_pols * antenna) + polarization
                    end_idx = ((channel + 1) * n_samp * n_pols * n_antennas)

                    if append:
                        dset[polarization,ds_last_size:ds_last_size+n_samp] = data_ptr[start_idx : end_idx : n_antennas * n_pols]
                    else:
                        dset[polarization,:] = data_ptr[start_idx : end_idx : n_antennas * n_pols]
        file.flush()
        self.close_file(file)


# --------------------------------------------------------- BEAM FILE --------------------------------------------------
class RawFormatFileManager(AAVSFileManager):

    # Class constructor
    def __init__(self, root_path = '', mode = FileModes.Read):
        super(RawFormatFileManager, self).__init__(root_path=root_path, type=FileTypes.Raw, mode=mode)

    def configure(self, file):
        n_pols = self.main_dset.attrs['n_pols']
        n_antennas = self.main_dset.attrs['n_antennas']
        n_samp = self.main_dset.attrs['n_samples']
        for antenna in xrange(0, n_antennas):
            antenna_grp = file.create_group("antenna_"+str(antenna))
            antenna_grp.create_dataset("data", (n_pols,0), chunks=(n_pols,n_samp/32), dtype='int8', maxshape=(n_pols,None))

    def read_data(self, timestamp=0, antennas=[], polarizations=[], n_samples=0):
        try:
            file = self.load_file(timestamp)
        except:
            print "Can't load file"

        output_buffer = numpy.zeros([len(antennas),len(polarizations), n_samples],dtype='int8')

        for antenna_idx in xrange(0, len(antennas)):
            current_antenna = antennas[antenna_idx]
            antenna_grp = file["antenna_" + str(current_antenna)]
            dset = antenna_grp["data"]
            nof_items = dset[0].size
            for polarization_idx in xrange(0, len(polarizations)):
                current_polarization = polarizations[polarization_idx]
                if n_samples > nof_items:
                    output_buffer[antenna_idx,polarization_idx,:] = dset[current_polarization,0:nof_items]
                else:
                    output_buffer[antenna_idx,polarization_idx,:] = dset[current_polarization,0:n_samples]
        return output_buffer

    def plot(self, data_in=None, timestamp=0, antennas=[], polarizations=[], n_samples=0):
        # output_buffer[antenna_idx,polarization_idx,:] = dset[0:n_samples]
        if data_in is None:
            data = self.read_data(timestamp=timestamp, antennas=antennas, polarizations=polarizations, n_samples=n_samples)
        else:
            data = data_in

        total_plots = len(antennas) * len(polarizations)
        plot_cnt = 1
        for antenna_idx in xrange(0, len(antennas)):
            current_antenna = antennas[antenna_idx]
            for polarization_idx in xrange(0, len(polarizations)):
                current_polarization = polarizations[polarization_idx]
                subplot = plt.subplot(total_plots/2, 2, plot_cnt)
                subplot.set_title("Antenna: " + str(current_antenna) + " - Polarization: " + str(current_polarization), fontsize=9)
                plt.xlabel('Time (sample)')
                plt.ylabel('Amplitude')
                sub_data = data[antenna_idx,polarization_idx,:]
                plt.plot(range(0, n_samples),sub_data)

                # recompute the ax.dataLim
                subplot.relim()
                # update subplot.viewLim using the new dataLim
                subplot.autoscale_view()
                plt.draw()
                plot_cnt += 1
                #plt.imshow(data[antenna_idx,polarization_idx,:], aspect='auto')
        plt.show()

    def ingest_data(self, data_ptr=None, timestamp=0, append=False):
        if append:
            try:
                file = self.load_file(timestamp)
            except:
                file = self.create_file(timestamp)
        else:
            file = self.create_file(timestamp)

        n_pols = self.main_dset.attrs['n_pols']
        n_antennas = self.main_dset.attrs['n_antennas']
        n_samp = self.main_dset.attrs['n_samples']
        self.main_dset.attrs['timestamp'] = timestamp

        for antenna in xrange(0, n_antennas):
            antenna_grp = file["antenna_" + str(antenna)]
            dset = antenna_grp["data"]
            ds_last_size = dset[0].size
            if append:
                dset.resize(ds_last_size+n_samp, axis=1) #resize to fit new data
            else:
                dset.resize(n_samp, axis=1) #resize for only one fit

            for polarization in xrange(0, n_pols):
                start_idx = antenna * n_samp * n_pols + polarization
                end_idx = (antenna+1) * n_samp * n_pols
                if append:
                    dset[polarization,ds_last_size:ds_last_size+n_samp] = data_ptr[start_idx : end_idx : n_pols]
                else:
                    dset[polarization,:] = data_ptr[start_idx : end_idx : n_pols]
        file.flush()
        self.close_file(file)
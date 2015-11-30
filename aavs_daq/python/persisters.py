import os

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
        self.ctype = numpy.dtype([('real', numpy.int8), ('imag', numpy.int8)])

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

    def complex_abs(self, value):
        return math.sqrt((value[0]**2) + (value[1]**2))

    def ingest_data(self, data_ptr=None, timestamp=None, append=False):
        if append:
            self.append_data(data_ptr=data_ptr, timestamp=timestamp)
        else:
            self.write_data(data_ptr=data_ptr, timestamp=timestamp)

    def load_file(self, timestamp = None):
        if self.type == FileTypes.Raw:
            filename_prefix = "raw_"
        elif self.type == FileTypes.Channel:
            filename_prefix = "channel_"
        elif self.type == FileTypes.Beamformed:
            filename_prefix = "beamformed_"

        full_filename = None
        if timestamp==None:
            files = next(os.walk(self.root_path))[2]
            for file in files:
                if file.startswith(filename_prefix) and file.endswith(".hdf5"):
                    full_filename = os.path.join(self.root_path, file)
        else:
            full_filename = os.path.join(self.root_path, filename_prefix + str(timestamp) + ".hdf5")

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

    def create_file(self, timestamp = None):
        if self.type == FileTypes.Raw:
            filename_prefix = "raw_"
        elif self.type == FileTypes.Channel:
            filename_prefix = "channel_"
        elif self.type == FileTypes.Beamformed:
            filename_prefix = "beamformed_"

        full_filename = os.path.join(self.root_path, filename_prefix + str(timestamp) + ".hdf5")

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

    def configure(self, file):
        n_pols = self.main_dset.attrs['n_pols']
        n_samp = self.main_dset.attrs['n_samples']
        n_chans = self.main_dset.attrs['n_chans']
        for polarization in xrange(0, n_pols):
            polarization_grp = file.create_group("polarization_"+str(polarization))
            polarization_grp.create_dataset("data", (n_chans,0), chunks=(n_chans,n_samp), dtype=self.ctype, maxshape=(n_chans,None))
        file.flush()

    def plot(self, data_in=None, timestamp=None, channels=[], polarizations=[], sample_offset=0, n_samples=0):
        complex_func = numpy.vectorize(self.complex_abs)
        # output_buffer[channel_idx,antenna_idx,polarization_idx,:] = dset[0:n_samples]
        if data_in is None:
            data = self.read_data(timestamp=timestamp, channels=channels, polarizations=polarizations, n_samples=n_samples, sample_offset=sample_offset)
        else:
            data = data_in

        total_plots = len(polarizations)
        plot_cnt = 1
        for polarization_idx in xrange(0, len(polarizations)):
            current_polarization = polarizations[polarization_idx]
            subplot = plt.subplot(total_plots/2, 2, plot_cnt)
            subplot.set_title("Polarization: " + str(current_polarization), fontsize=9)
            plt.xlabel('Time (sample)')
            plt.ylabel('Channel')

            sub_data = complex_func(data[polarization_idx,:,:])
            plt.imshow(sub_data, aspect='auto', interpolation='none')
            plot_cnt += 1
        plt.show()

    def progressive_plot(self, timestamp=None, channels=[], polarizations=[], sample_start=0, sample_end=0, n_samples_view=0):
        plt.ion()
        complex_func = numpy.vectorize(self.complex_abs)
        try:
            file = self.load_file(timestamp)
        except Exception as e:
            print "Can't load file: ", e.message
            raise

        fig = plt.figure()
        dummy_data = numpy.zeros((self.n_chans,n_samples_view))

        #set up image area
        total_plots = len(polarizations)
        images = []
        plot_cnt = 1
        for polarization_idx in xrange(0, len(polarizations)):
            current_polarization = polarizations[polarization_idx]
            subplot = fig.add_subplot(total_plots/2, 2, plot_cnt)
            subplot.set_title("Polarization: " + str(current_polarization), fontsize=9)
            images.append(plt.imshow(dummy_data, aspect='auto', interpolation='none'))
            plt.xlabel('Time (sample)')
            plt.ylabel('Channel')
            plot_cnt += 1
        plt.show(block=False)

        #now start real plotting
        current_sample_start = sample_start
        while (current_sample_start+n_samples_view) < sample_end:
            #print current_sample_start
            plot_cnt = 1
            data = self.read_data(timestamp=timestamp, channels=channels, polarizations=polarizations, n_samples=n_samples_view, sample_offset=current_sample_start)
            sub_data = complex_func(data[:,:,:])
            plt.waitforbuttonpress()
            for polarization_idx in xrange(0, len(polarizations)):
                images[plot_cnt-1].set_data(sub_data[polarization_idx,:,:])
                images[plot_cnt-1].autoscale()
                plot_cnt += 1
            current_sample_start += n_samples_view
            fig.canvas.draw()
            plt.show(block=False)
            print "Drawn!"
        plt.show()

    def read_data(self, timestamp=None, channels=[], polarizations=[], n_samples=0, sample_offset=0):
        try:
            file = self.load_file(timestamp)
        except Exception as e:
            print "Can't load file: ", e.message
            raise

        output_buffer = numpy.zeros([len(polarizations),len(channels), n_samples],dtype=self.ctype)

        for polarization_idx in xrange(0, len(polarizations)):
            current_polarization = polarizations[polarization_idx]
            polarization_grp = file["polarization_" + str(current_polarization)]
            dset = polarization_grp["data"]
            nof_items = dset[0].size
            for channel_idx in xrange(0, len(channels)):
                current_channel = channels[channel_idx]
                if sample_offset+n_samples > nof_items:
                    output_buffer[polarization_idx,channel_idx,:] = dset[current_channel,0:nof_items]
                else:
                    output_buffer[polarization_idx,channel_idx,:] = dset[current_channel,sample_offset:sample_offset+n_samples]
        return output_buffer

    def write_data(self, timestamp=None, data_ptr=None):
        file = self.create_file(timestamp)

        n_pols = self.main_dset.attrs['n_pols']
        n_samp = self.main_dset.attrs['n_samples']
        n_chans = self.main_dset.attrs['n_chans']
        self.main_dset.attrs['timestamp'] = timestamp
        for polarization in xrange(0, n_pols):
            polarization_grp = file["polarization_"+str(polarization)]
            dset = polarization_grp["data"]
            dset.resize(n_samp, axis=1) #resize for only one fit
            for channel in xrange(0, n_chans):
                start_idx = (polarization * n_chans * n_samp) + channel
                end_idx = (polarization + 1) * n_chans * n_samp
                dset[channel,:] = data_ptr[start_idx : end_idx : n_chans]
        file.flush()
        self.close_file(file)

    def append_data(self, timestamp = 0, data_ptr=None):
        try:
            file = self.load_file(timestamp)
        except:
            file = self.create_file(timestamp)

        n_pols = self.main_dset.attrs['n_pols']
        n_samp = self.main_dset.attrs['n_samples']
        n_chans = self.main_dset.attrs['n_chans']
        self.main_dset.attrs['timestamp'] = timestamp
        for polarization in xrange(0, n_pols):
            polarization_grp = file["polarization_"+str(polarization)]
            dset = polarization_grp["data"]
            ds_last_size = dset[0].size
            dset.resize(ds_last_size+n_samp, axis=1) #resize to fit new data
            for channel in xrange(0, n_chans):
                start_idx = (polarization * n_chans * n_samp) + channel
                end_idx = (polarization + 1) * n_chans * n_samp
                dset[channel, ds_last_size:ds_last_size+n_samp] = data_ptr[start_idx : end_idx : n_chans]
        file.flush()
        self.close_file(file)

# ------------------------------------------------------- CHANNEL FILE -------------------------------------------------
class ChannelFormatFileManager(AAVSFileManager):

    # Class constructor
    def __init__(self, root_path = '', mode = FileModes.Read):
        super(ChannelFormatFileManager, self).__init__(root_path=root_path, type=FileTypes.Channel, mode=mode)

    def configure(self, file):
        n_pols = self.main_dset.attrs['n_pols']
        n_antennas = self.main_dset.attrs['n_antennas']
        n_samp = self.main_dset.attrs['n_samples']
        n_chans = self.main_dset.attrs['n_chans']
        for channel in xrange(0, n_chans):
            channel_grp = file.create_group("channel_"+str(channel))
            channel_grp.create_dataset("data", (n_pols*n_antennas,0), chunks=(n_pols*n_antennas,n_samp), dtype=self.ctype, maxshape=(n_pols*n_antennas,None))
        file.flush()

    def plot(self, data_in=None, timestamp=None, channels=[], antennas=[], polarizations=[], sample_offset=0, n_samples=0):
        complex_func = numpy.vectorize(self.complex_abs)
        # output_buffer[channel_idx,antenna_idx,polarization_idx,:] = dset[0:n_samples]
        if data_in is None:
            data = self.read_data(timestamp=timestamp, channels=channels, antennas=antennas, polarizations=polarizations, n_samples=n_samples, sample_offset=sample_offset)
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
                plt.xlabel('Time (sample)',fontsize=9)
                plt.ylabel('Channel',fontsize=9)

                sub_data = complex_func(data[:,antenna_idx,polarization_idx,:])
                #selected_data = data[:,antenna_idx,polarization_idx,:]
                #sub_data = complex_func(selected_data)
                plt.imshow(sub_data, aspect='auto', interpolation='none')
                #plt.yticks(channels)
                plot_cnt += 1

        mng = plt.get_current_fig_manager()
        mng.resize(*mng.window.maxsize())
        plt.tight_layout()
        plt.subplots_adjust(left=0.04, bottom=0.05, right=0.99, top=0.95, wspace=0.1, hspace=0.2)
        plt.show()

    def progressive_plot(self, timestamp=None, channels=[], antennas=[], polarizations=[], sample_start=0, sample_end=0, n_samples_view=0):
        plt.ion()
        complex_func = numpy.vectorize(self.complex_abs)
        try:
            file = self.load_file(timestamp)
        except Exception as e:
            print "Can't load file: ", e.message
            raise

        #total_views = (int) (sample_end-sample_start) / n_samples_view
        fig = plt.figure()
        dummy_data = numpy.zeros((self.n_chans,n_samples_view))

        #set up image area
        total_plots = len(antennas) * len(polarizations)
        images = []
        plot_cnt = 1
        for antenna_idx in xrange(0, len(antennas)):
            current_antenna = antennas[antenna_idx]
            for polarization_idx in xrange(0, len(polarizations)):
                current_polarization = polarizations[polarization_idx]
                subplot = fig.add_subplot(total_plots/2, 2, plot_cnt)
                subplot.set_title("Antenna: " + str(current_antenna) + " - Polarization: " + str(current_polarization), fontsize=9)
                images.append(plt.imshow(dummy_data, aspect='auto', interpolation='none'))
                plt.xlabel('Time (sample)', fontsize=9)
                plt.ylabel('Channel', fontsize=9)
                plot_cnt += 1

        mng = plt.get_current_fig_manager()
        mng.resize(*mng.window.maxsize())
        plt.tight_layout()
        plt.subplots_adjust(left=0.04, bottom=0.05, right=0.99, top=0.95, wspace=0.1, hspace=0.2)
        plt.show(block=False)

        #now start real plotting
        current_sample_start = sample_start
        while (current_sample_start+n_samples_view) < sample_end:
            #print current_sample_start
            plot_cnt = 1
            data = self.read_data(timestamp=timestamp, channels=channels, antennas=antennas, polarizations=polarizations, n_samples=n_samples_view, sample_offset=current_sample_start)
            sub_data = complex_func(data[:,:,:,:])
            plt.waitforbuttonpress()
            for antenna_idx in xrange(0, len(antennas)):
                for polarization_idx in xrange(0, len(polarizations)):
                    #data = self.read_data(timestamp=timestamp, channels=channels, antennas=antennas, polarizations=polarizations, n_samples=n_samples_view, sample_offset=current_sample_start)
                    #sub_data = complex_func(data[:,antenna_idx,polarization_idx,:])
                    images[plot_cnt-1].set_data(sub_data[:,antenna_idx,polarization_idx,:])
                    images[plot_cnt-1].autoscale()
                    plot_cnt += 1
            current_sample_start += n_samples_view
            fig.canvas.draw()
            plt.show(block=False)
            print "Drawn!"
        plt.show()

    def read_data(self, timestamp=None, channels=[], antennas=[], polarizations=[], n_samples=0, sample_offset=0):
        try:
            file = self.load_file(timestamp)
        except Exception as e:
            print "Can't load file: ", e.message
            raise

        output_buffer = numpy.zeros([len(channels),len(antennas),len(polarizations), n_samples],dtype=self.ctype)

        for channel_idx in xrange(0, len(channels)):
            current_channel = channels[channel_idx]
            channel_grp = file["channel_" + str(current_channel)]
            dset = channel_grp["data"]
            nof_items = dset[0].size
            for antenna_idx in xrange(0, len(antennas)):
                current_antenna = antennas[antenna_idx]
                for polarization_idx in xrange(0, len(polarizations)):
                    current_polarization = polarizations[polarization_idx]
                    if sample_offset+n_samples > nof_items:
                        output_buffer[channel_idx,antenna_idx,polarization_idx,:] = dset[(current_antenna*self.n_pols)+current_polarization, 0:nof_items]
                    else:
                        output_buffer[channel_idx,antenna_idx,polarization_idx,:] = dset[(current_antenna*self.n_pols)+current_polarization, sample_offset:sample_offset+n_samples]
        return output_buffer

    def write_data(self, data_ptr=None, timestamp=None):
        file = self.create_file(timestamp)

        n_pols = self.main_dset.attrs['n_pols']
        n_antennas = self.main_dset.attrs['n_antennas']
        n_samp = self.main_dset.attrs['n_samples']
        n_chans = self.main_dset.attrs['n_chans']
        collected_data = numpy.empty((n_pols*n_antennas,n_samp),dtype=self.ctype)
        self.main_dset.attrs['timestamp'] = timestamp
        for channel in xrange(0, n_chans):
            channel_grp = file["channel_" + str(channel)]
            dset = channel_grp["data"]
            dset.resize(n_samp, axis=1) #resize for only one fit
            for antenna in xrange(0, n_antennas):
                for polarization in xrange(0, n_pols):
                    start_idx = (channel * n_samp * n_pols * n_antennas) + (n_pols * antenna) + polarization
                    end_idx = ((channel + 1) * n_samp * n_pols * n_antennas)
                    collected_data[(antenna*n_pols)+polarization,:] = data_ptr[start_idx : end_idx : n_antennas * n_pols]
            dset[:,:] = collected_data
        file.flush()
        self.close_file(file)

    def append_data(self, data_ptr=None, timestamp=None):
        try:
            file = self.load_file(timestamp)
        except:
            file = self.create_file(timestamp)

        n_pols = self.main_dset.attrs['n_pols']
        n_antennas = self.main_dset.attrs['n_antennas']
        n_samp = self.main_dset.attrs['n_samples']
        n_chans = self.main_dset.attrs['n_chans']
        collected_data = numpy.empty((n_pols*n_antennas,n_samp),dtype=self.ctype)
        self.main_dset.attrs['timestamp'] = timestamp
        for channel in xrange(0, n_chans):
            channel_grp = file["channel_" + str(channel)]
            dset = channel_grp["data"]
            ds_last_size = dset[0].size
            dset.resize(ds_last_size+n_samp, axis=1) #resize to fit new data
            for antenna in xrange(0, n_antennas):
                for polarization in xrange(0, n_pols):
                    start_idx = (channel * n_samp * n_pols * n_antennas) + (n_pols * antenna) + polarization
                    end_idx = ((channel + 1) * n_samp * n_pols * n_antennas)
                    collected_data[(antenna*n_pols)+polarization,:] = data_ptr[start_idx : end_idx : n_antennas * n_pols]
            dset[:,ds_last_size:ds_last_size+n_samp] = collected_data
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
        raw_group = file.create_group("raw_")
        raw_group.create_dataset("data", (n_antennas*n_pols,0), chunks=(n_antennas*n_pols,n_samp), dtype='int8', maxshape=(n_antennas*n_pols,None))
        file.flush()

    def read_data(self, timestamp=None, antennas=[], polarizations=[], n_samples=0, sample_offset=0):
        try:
            file = self.load_file(timestamp)
        except Exception as e:
            print "Can't load file: ", e.message
            raise

        output_buffer = numpy.zeros([len(antennas),len(polarizations), n_samples],dtype='int8')
        raw_grp = file["raw_"]
        dset = raw_grp["data"]
        nof_items = dset[0].size

        for antenna_idx in xrange(0, len(antennas)):
            current_antenna = antennas[antenna_idx]
            for polarization_idx in xrange(0, len(polarizations)):
                current_polarization = polarizations[polarization_idx]
                if sample_offset+n_samples > nof_items:
                    output_buffer[antenna_idx,polarization_idx,:] = dset[(current_antenna*self.n_pols)+current_polarization, 0:nof_items]
                else:
                    output_buffer[antenna_idx,polarization_idx,:] = dset[(current_antenna*self.n_pols)+current_polarization, sample_offset:sample_offset+n_samples]
        return output_buffer

    def plot(self, data_in=None, timestamp=None, antennas=[], polarizations=[], n_samples=0, sample_offset=0):
        # output_buffer[antenna_idx,polarization_idx,:] = dset[0:n_samples]
        if data_in is None:
            data = self.read_data(timestamp=timestamp, antennas=antennas, polarizations=polarizations, n_samples=n_samples, sample_offset=sample_offset)
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
                plt.xlabel('Time (sample)', fontsize=9)
                plt.ylabel('Amplitude', fontsize=9)
                sub_data = data[antenna_idx,polarization_idx,:]
                plt.plot(range(0, n_samples),sub_data)

                # recompute the ax.dataLim
                subplot.relim()
                subplot.autoscale_view()
                plt.draw()
                plot_cnt += 1
        mng = plt.get_current_fig_manager()
        mng.resize(*mng.window.maxsize())
        plt.tight_layout()
        plt.subplots_adjust(left=0.04, bottom=0.05, right=0.99, top=0.95, wspace=0.1, hspace=0.2)
        plt.show()

    def progressive_plot(self, timestamp=None, antennas=[], polarizations=[], sample_start=0, sample_end=0, n_samples_view=0):
        plt.ion()
        try:
            file = self.load_file(timestamp)
        except Exception as e:
            print "Can't load file: ", e.message
            raise

        #total_views = (int) (sample_end-sample_start) / n_samples_view
        fig = plt.figure()
        dummy_data = numpy.zeros(n_samples_view)

        #set up image area
        total_plots = len(antennas) * len(polarizations)
        plots = []
        subplots = []
        plot_cnt = 1
        for antenna_idx in xrange(0, len(antennas)):
            current_antenna = antennas[antenna_idx]
            for polarization_idx in xrange(0, len(polarizations)):
                current_polarization = polarizations[polarization_idx]
                subplot = fig.add_subplot(total_plots/2, 2, plot_cnt)
                subplot.set_autoscale_on(True)
                subplot.autoscale_view(True,True,True)
                line, = subplot.plot(range(0, n_samples_view),dummy_data)
                subplot.set_title("Antenna: " + str(current_antenna) + " - Polarization: " + str(current_polarization), fontsize=9)
                plots.append(line)
                subplots.append(subplot)
                plt.xlabel('Time (sample)', fontsize=9)
                plt.ylabel('Amplitude', fontsize=9)
                plot_cnt += 1
        mng = plt.get_current_fig_manager()
        mng.resize(*mng.window.maxsize())
        plt.tight_layout()
        plt.subplots_adjust(left=0.04, bottom=0.05, right=0.99, top=0.95, wspace=0.1, hspace=0.2)
        plt.show(block=False)

        #now start real plotting
        current_sample_start = sample_start
        while (current_sample_start+n_samples_view) <= sample_end:
            #print current_sample_start
            plot_cnt = 1
            data = self.read_data(timestamp=timestamp, antennas=antennas, polarizations=polarizations, n_samples=n_samples_view, sample_offset=current_sample_start)
            for antenna_idx in xrange(0, len(antennas)):
                for polarization_idx in xrange(0, len(polarizations)):
                    plots[plot_cnt-1].set_ydata(data[antenna_idx,polarization_idx,:])
                    subplots[plot_cnt-1].relim()
                    subplots[plot_cnt-1].autoscale_view()
                    plot_cnt += 1
            current_sample_start += n_samples_view
            fig.canvas.draw()
            plt.show(block=False)
            plt.waitforbuttonpress()
            print "Drawn!"
        plt.show()

    def write_data(self, data_ptr=None, timestamp=None):
        file = self.create_file(timestamp)

        n_pols = self.main_dset.attrs['n_pols']
        n_antennas = self.main_dset.attrs['n_antennas']
        n_samp = self.main_dset.attrs['n_samples']
        self.main_dset.attrs['timestamp'] = timestamp

        raw_grp = file["raw_"]
        dset = raw_grp["dmaata"]
        ds_last_size = dset[0].size
        dset.resize(n_samp, axis=1) #resize for only one fit

        for antenna in xrange(0, n_antennas):
            for polarization in xrange(0, n_pols):
                start_idx = antenna * n_samp * n_pols + polarization
                end_idx = (antenna+1) * n_samp * n_pols
                dset[(antenna*n_pols)+polarization,:] = data_ptr[start_idx : end_idx : n_pols]
        file.flush()
        self.close_file(file)

    def append_data(self, data_ptr=None, timestamp=None):
        try:
            file = self.load_file(timestamp)
        except:
            file = self.create_file(timestamp)

        n_pols = self.main_dset.attrs['n_pols']
        n_antennas = self.main_dset.attrs['n_antennas']
        n_samp = self.main_dset.attrs['n_samples']
        self.main_dset.attrs['timestamp'] = timestamp

        raw_grp = file["raw_"]
        dset = raw_grp["data"]
        ds_last_size = dset[0].size
        dset.resize(ds_last_size+n_samp, axis=1) #resize to fit new data

        for antenna in xrange(0, n_antennas):
            for polarization in xrange(0, n_pols):
                start_idx = antenna * n_samp * n_pols + polarization
                end_idx = (antenna+1) * n_samp * n_pols
                dset[(antenna*n_pols)+polarization,ds_last_size:ds_last_size+n_samp] = data_ptr[start_idx : end_idx : n_pols]
        file.flush()
        self.close_file(file)

if __name__ == "__main__":

   channel_file = ChannelFormatFileManager(root_path="/home/lessju/Code/TPM-Access-Layer/aavs_daq/python", mode=FileModes.Read)
   channel_file.plot(channels=range(0, 512), antennas=range(0, 2), polarizations=range(0, 1), n_samples=1024)

    # beam_file = BeamFormatFileManager(root_path="/home/lessju/Code/TPM-Access-Layer/aavs_daq/python", mode=FileModes.Read)
    # beam_file.plot(channels=range(0,512), polarizations=[0,1], n_samples=64)

    # raw_file = RawFormatFileManager(root_path="/home/lessju/Code/TPM-Access-Layer/aavs_daq/python", mode=FileModes.Read)
    # raw_file.plot(antennas=range(8), polarizations=[0,1], n_samples=1024)
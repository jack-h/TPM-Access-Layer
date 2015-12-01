from aavs_file import *
from matplotlib import pyplot as plt
import time
import numpy
import ctypes

class ChannelFormatFileManager(AAVSFileManager):

    # Class constructor
    def __init__(self, root_path = '.', mode = FileModes.Read):
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

    def plot(self, timestamp=None):
        plt.close("all")
        antennas = self.plot_antennas
        channels = self.plot_channels
        polarizations = self.plot_polarizations
        n_samples = self.plot_n_samples
        sample_offset = self.plot_sample_offset

        data = self.read_data(timestamp=timestamp, channels=channels, antennas=antennas, polarizations=polarizations, n_samples=n_samples, sample_offset=sample_offset)

        complex_func = numpy.vectorize(self.complex_abs)

        total_plots = len(antennas) * len(polarizations)
        plot_div_value = total_plots / 2.0
        plot_cnt = 1
        for antenna_idx in xrange(0, len(antennas)):
            current_antenna = antennas[antenna_idx]
            for polarization_idx in xrange(0, len(polarizations)):
                current_polarization = polarizations[polarization_idx]
                if(plot_div_value < 1):
                    subplot = plt.subplot(1, 1, plot_cnt)
                elif(plot_div_value >= 1):
                    subplot = plt.subplot(math.ceil(total_plots / 2.0), 2, plot_cnt)
                subplot.set_title("Antenna: " + str(current_antenna) + " - Polarization: " + str(current_polarization), fontsize=9)
                plt.xlabel('Time (sample)',fontsize=9)
                plt.ylabel('Channel',fontsize=9)

                sub_data = complex_func(data[:,antenna_idx,polarization_idx,:])
                plt.imshow(sub_data, aspect='auto', interpolation='none')
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
        plot_div_value = total_plots / 2.0

        images = []
        plot_cnt = 1
        for antenna_idx in xrange(0, len(antennas)):
            current_antenna = antennas[antenna_idx]
            for polarization_idx in xrange(0, len(polarizations)):
                current_polarization = polarizations[polarization_idx]
                if(plot_div_value < 1):
                    subplot = fig.add_subplot(1, 1, plot_cnt)
                elif(plot_div_value >= 1):
                    subplot = fig.add_subplot(math.ceil(total_plots / 2.0), 2, plot_cnt)
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

if __name__ == '__main__':
    channels = 512
    antennas = 16
    pols = 2
    #samples = 131072
    samples = 100
    runs = 1

    ctype = numpy.dtype([('real', numpy.int8), ('imag', numpy.int8)])

    print "ingesting..."
    channel_file = ChannelFormatFileManager(root_path="/media/andrea/hdf5", mode=FileModes.Write)
    channel_file.set_metadata(n_chans=channels, n_antennas=antennas, n_pols=pols, n_samples=samples)
    #data = numpy.zeros(channels * samples * antennas * pols, dtype=ctype)

    a = numpy.arange(0,channels * samples * antennas * pols, dtype=numpy.int8)
    for channel_value in xrange(0,channels):
        a[channel_value*(samples*antennas*pols):((channel_value+1)*(samples*antennas*pols))] = channel_value
    b = numpy.zeros(channels * samples * antennas * pols, dtype=numpy.int8)
    data = numpy.array([(a[i],b[i]) for i in range(0,len(a))],dtype=ctype)
    a=[]
    b=[]
    # numpy.set_printoptions(threshold='nan')
    # print data
    start = time.time()
    for i in xrange(0, 1):
        for run in xrange(0, runs):
            channel_file.write_data(data_ptr=data, timestamp=run)
            #channel_file.append_data(data_ptr=data, timestamp=0)
    end = time.time()
    bits = (channels * antennas * pols * samples * runs * 16)
    mbs = bits * 1.25e-7
    print "Write speed: " + str(mbs/(end - start)) + " Mb/s"

    # print "reading back out"
    # channel_file = ChannelFormatFileManager(root_path="/media/andrea/hdf5", mode=FileModes.Read)
    # start = time.time()
    # buffer = channel_file.read_data(timestamp=0, channels=range(0, channels), antennas=range(0, antennas), polarizations=range(0, pols), n_samples=samples)
    # print buffer.size
    # end = time.time()
    # print end - start

    channel_file = ChannelFormatFileManager(root_path="/media/andrea/hdf5", mode=FileModes.Read)
    channel_file.set_plot_defaults(channels=range(0, channels), antennas=range(0, antennas), polarizations=range(0, pols), n_samples=samples, sample_offset=0)
    print "Plotting"
    start = time.time()
    channel_file.plot(timestamp=0)
    #channel_file.progressive_plot(timestamp=0, channels=range(0, channels), antennas=range(0, 2), polarizations=range(0, pols), sample_start=0, sample_end=samples, n_samples_view=256)
    end = time.time()
    print end - start
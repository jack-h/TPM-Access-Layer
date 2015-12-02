from aavs_file import *
from matplotlib import pyplot as plt
import time
import numpy

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

    def do_plotting(self):
        timestamp = self.plot_timestamp
        channels = self.plot_channels
        antennas = self.plot_antennas
        polarizations = self.plot_polarizations
        n_samples = self.plot_n_samples
        sample_offset = self.plot_sample_offset
        data = self.read_data(timestamp=timestamp, channels=channels, polarizations=polarizations, n_samples=n_samples, sample_offset=sample_offset)
        complex_func = numpy.vectorize(self.complex_abs)
        sub_data = complex_func(data[:,:,:])

        plot_cnt = 1
        for polarization_idx in xrange(0, len(polarizations)):
            self.images[plot_cnt-1].set_data(sub_data[polarization_idx,:,:])
            self.images[plot_cnt-1].autoscale()
            plot_cnt += 1
        print "Drawn!"
        self.update_canvas = True

    def plot(self, real_time = False, timestamp=None, channels=[], antennas = [], polarizations = [], n_samples = 0, sample_offset=0):
        plt.close()
        self.plot_channels = channels
        self.plot_antennas = antennas
        self.plot_polarizations = polarizations
        self.plot_n_samples = n_samples
        self.plot_sample_offset = sample_offset
        self.plots = []
        self.subplots = []
        self.images=[]

        if real_time:
            self.file_monitor.start_file_monitor()
            self.plot_timestamp = self.real_time_timestamp
        else:
            self.plot_timestamp = timestamp
            self.file_monitor.stop_file_monitor()
            self.update_canvas = True

        #set up image area
        self.fig = plt.figure()
        dummy_data = numpy.zeros((len(channels),n_samples))
        total_plots = len(polarizations)
        plot_div_value = total_plots / 2.0;

        images = []
        plot_cnt = 1
        for polarization_idx in xrange(0, len(polarizations)):
            current_polarization = polarizations[polarization_idx]
            if(plot_div_value < 1):
                subplot = self.fig.add_subplot(1, 1, plot_cnt)
            elif(plot_div_value >= 1):
                subplot = self.fig.add_subplot(math.ceil(total_plots / 2.0), 2, plot_cnt)
            subplot.set_title("Polarization: " + str(current_polarization), fontsize=9)
            self.images.append(plt.imshow(dummy_data, aspect='auto', interpolation='none'))
            plt.xlabel('Time (sample)', fontsize=9)
            plt.ylabel('Channel', fontsize=9)
            plot_cnt += 1
        plt.tight_layout()
        plt.subplots_adjust(left=0.04, bottom=0.05, right=0.99, top=0.95, wspace=0.1, hspace=0.2)
        plt.show(block=False)
        dummy_data=[]

        if(real_time):
            while True:
                time.sleep(1)
                while(self.update_canvas == False):
                    self.fig.canvas.flush_events()
                else:
                    self.fig.canvas.draw()
                    self.fig.canvas.flush_events()
                    self.update_canvas = False
        else:
            self.do_plotting()
            self.fig.canvas.draw()
            plt.show()

    def progressive_plot(self, timestamp=None, channels=[], polarizations=[], sample_start=0, sample_end=0, n_samples_view=0):
        plt.ion()
        try:
            file = self.load_file(timestamp)
        except Exception as e:
            print "Can't load file: ", e.message
            raise
        complex_func = numpy.vectorize(self.complex_abs)
        self.plot(real_time=False, timestamp=timestamp,channels=channels, polarizations=polarizations, n_samples=n_samples_view)

        #now start real plotting
        current_sample_start = sample_start
        while (current_sample_start+n_samples_view) < sample_end:
            #print current_sample_start
            plot_cnt = 1
            data = self.read_data(timestamp=timestamp, channels=channels, polarizations=polarizations, n_samples=n_samples_view, sample_offset=current_sample_start)
            sub_data = complex_func(data[:,:,:])
            plt.waitforbuttonpress()
            for polarization_idx in xrange(0, len(polarizations)):
                self.images[plot_cnt-1].set_data(sub_data[polarization_idx,:,:])
                self.images[plot_cnt-1].autoscale()
                plot_cnt += 1
            current_sample_start += n_samples_view
            self.fig.canvas.draw()
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
        data_flushed = False
        while not data_flushed:
            try:
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
                data_flushed = True
            except Exception as e:
                print "File appears to be in construction, re-trying."
                self.close_file(file)
                file = self.load_file(timestamp)
        return output_buffer

    def write_data(self, timestamp=None, data_ptr=None):
        file = self.create_file(timestamp)
        self.close_file(file)
        file = self.load_file(timestamp)

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

    def append_data(self, timestamp = None, data_ptr=None):
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

if __name__ == '__main__':
    channels = 32
    pols = 2
    samples = 1024
    #samples = 500000 * 8
    runs = 2


    # print "ingesting..."
    # ctype = numpy.dtype([('real', numpy.int8), ('imag', numpy.int8)])
    #
    # beam_file_mgr = BeamFormatFileManager(root_path="/media/andrea/hdf5", mode=FileModes.Write)
    # beam_file_mgr.set_metadata(n_chans=channels, n_pols=pols, n_samples=samples)
    # #data = numpy.zeros(channels * samples * pols, dtype=ctype)
    #
    # a = numpy.arange(0,channels * samples * pols, dtype=numpy.int8)
    # b = numpy.zeros(channels * samples * pols, dtype=numpy.int8)
    # data = numpy.array([(a[i],b[i]) for i in range(0,len(a))],dtype=ctype)
    #
    # start = time.time()
    # for run in xrange(0, runs):
    #     beam_file_mgr.write_data(timestamp=5, data_ptr=data)
    #     #beam_file_mgr.append_data(timestamp=run, data_ptr=data)
    # end = time.time()
    # bits = (channels * pols * samples * runs * 16)
    # mbs = bits * 1.25e-7
    # print "Write speed: " + str(mbs/(end - start)) + " Mb/s"

    # beam_file_mgr = BeamFormatFileManager(root_path="/media/andrea/hdf5", mode=FileModes.Read)
    # print "reading back out"
    # start = time.time()
    # buffer = beam_file_mgr.read_data(timestamp=0, channels=range(0, channels), polarizations=range(0, pols), n_samples=samples)
    # print buffer.size
    # end = time.time()
    # print end - start
    #
    # print "Plotting"
    # beam_file_mgr = BeamFormatFileManager(root_path="/media/andrea/hdf5", mode=FileModes.Read)
    # start = time.time()
    # #beam_file_mgr.plot(timestamp=0, channels=range(0, channels), polarizations=range(0, pols), n_samples=samples, sample_offset=0)
    # beam_file_mgr.progressive_plot(timestamp=0, channels=range(0, channels), polarizations=range(0, pols), sample_start=0, sample_end=samples, n_samples_view=256)
    # end = time.time()
    # print end - start

    beam_file_mgr = BeamFormatFileManager(root_path="/media/andrea/hdf5", mode=FileModes.Read)
    beam_file_mgr.plot(real_time=True, channels=range(0,4), polarizations=range(0, 2), n_samples=samples, sample_offset=0)

from aavs_file import *
from matplotlib import pyplot as plt
from matplotlib import cm
import time
import numpy

class ChannelFormatFileManager(AAVSFileManager):

    # Class constructor
    def __init__(self, root_path = '.', mode = FileModes.Write):
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

    def do_plotting(self):
        timestamp = self.plot_timestamp
        channels = self.plot_channels
        antennas = self.plot_antennas
        polarizations = self.plot_polarizations
        n_samples = self.plot_n_samples
        sample_offset = self.plot_sample_offset
        data = self.read_data(timestamp=timestamp, channels=channels, antennas=antennas, polarizations=polarizations, n_samples=n_samples, sample_offset=sample_offset)

        complex_func = numpy.vectorize(self.complex_abs)
        sub_data = complex_func(data[:,:,:,:])

        if self.plot_normalize:
            max_data = numpy.amax(sub_data)
            if(max_data>0):
                sub_data = sub_data/max_data

        if self.plot_log:
            sub_data = 10 * math.log10(sub_data)

        if self.plot_powerspectrum:
            sub_data = numpy.mean(sub_data, 3)

        #now start real plotting
        if not self.plot_powerspectrum:
            plot_cnt = 1
            for antenna_idx in xrange(0, len(antennas)):
                for polarization_idx in xrange(0, len(polarizations)):
                    self.images[plot_cnt-1].set_data(sub_data[:,antenna_idx,polarization_idx,:])
                    self.images[plot_cnt-1].autoscale()
                    #self.images[plot_cnt-1].set_clim(vmin=0, vmax=1)
                    plot_cnt += 1
            print "Drawn!"
            self.update_canvas = True
        else:
            plot_cnt = 1
            for antenna_idx in xrange(0, len(antennas)):
                for polarization_idx in xrange(0, len(polarizations)):
                    self.images[plot_cnt-1].set_ydata(sub_data[:,antenna_idx,polarization_idx])
                    self.subplots[plot_cnt-1].relim()
                    self.subplots[plot_cnt-1].autoscale_view()
                    plot_cnt += 1
            print "Drawn!"
            self.update_canvas = True

    def plot(self, power_spectrum = False, normalize = False, log_plot = False, real_time = False, timestamp=None, channels=[], antennas = [], polarizations = [], n_samples = 0, sample_offset=0):
        plt.close()
        self.plot_powerspectrum = power_spectrum
        self.plot_normalize = normalize
        self.plot_log = log_plot
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
        dummy_data = numpy.ones((len(channels),n_samples))
        dummy_data[0] = 0
        total_plots = len(antennas) * len(polarizations)
        plot_div_value = total_plots / 2.0

        plot_cnt = 1
        for antenna_idx in xrange(0, len(antennas)):
            current_antenna = antennas[antenna_idx]
            for polarization_idx in xrange(0, len(polarizations)):
                current_polarization = polarizations[polarization_idx]
                if(plot_div_value < 1):
                    subplot = self.fig.add_subplot(1, 1, plot_cnt)
                elif(plot_div_value >= 1):
                    subplot = self.fig.add_subplot(math.ceil(total_plots / 2.0), 2, plot_cnt)
                subplot.set_autoscale_on(True)
                subplot.autoscale_view(True,True,True)
                subplot.set_title("Antenna: " + str(current_antenna) + " - Polarization: " + str(current_polarization), fontsize=9)
                if not self.plot_powerspectrum:
                    self.images.append(plt.imshow(dummy_data, aspect='auto', interpolation='none', vmin=0.0, vmax=1.0))
                    plt.xlabel('Time (sample)', fontsize=9)
                    plt.ylabel('Channel', fontsize=9)
                else:
                    line, = subplot.plot(range(0, len(channels)),dummy_data[:,0])
                    self.images.append(line)
                    self.subplots.append(subplot)
                    plt.xlabel('Channel', fontsize=9)
                    plt.ylabel('Power', fontsize=9)
                plot_cnt += 1

        #plt.tight_layout()
        plt.subplots_adjust(left=0.04, bottom=0.05, right=0.99, top=0.95, wspace=0.1, hspace=0.2)

        if not self.plot_powerspectrum:
            im = self.images[0]
            self.fig.subplots_adjust(right=0.9)
            cax = self.fig.add_axes([0.95, 0.1, 0.01, 0.8])
            self.fig.colorbar(im, cax=cax)

        plt.show(block=False)
        dummy_data=[]

        if(real_time):
            while True:
                try:
                    time.sleep(1)
                    while(self.update_canvas == False):
                        self.fig.canvas.flush_events()
                    else:
                        self.fig.canvas.draw()
                        self.fig.canvas.flush_events()
                        self.update_canvas = False
                except (KeyboardInterrupt, SystemExit):
                    self.file_monitor.stop_file_monitor()
                    self.file_monitor.thread_handler.join()
                    print "Exiting..."
                    break
        else:
            self.do_plotting()
            self.fig.canvas.draw()
            plt.show()

    def progressive_plot(self, power_spectrum = False, normalize = False, log_plot = False, timestamp=None, channels=[], antennas=[], polarizations=[], sample_start=0, sample_end=0, n_samples_view=0):
        plt.close()
        plt.ion()
        # try:
        #     file = self.load_file(timestamp)
        # except Exception as e:
        #     print "Can't load file: ", e.message
        #     raise
        complex_func = numpy.vectorize(self.complex_abs)
        self.plot(power_spectrum = power_spectrum, normalize = normalize, log_plot = log_plot, real_time=False, timestamp=timestamp,channels=channels,antennas=antennas, polarizations=polarizations, n_samples=n_samples_view)

        #now start real plotting
        current_sample_start = sample_start
        while (current_sample_start+n_samples_view) < sample_end:
            #print current_sample_start
            data = self.read_data(timestamp=timestamp, channels=channels, antennas=antennas, polarizations=polarizations, n_samples=n_samples_view, sample_offset=current_sample_start)
            sub_data = complex_func(data[:,:,:,:])

            if self.plot_normalize:
                max_data = numpy.amax(sub_data)
                if(max_data>0):
                    sub_data = sub_data/max_data

            if self.plot_log:
                sub_data = 10 * math.log10(sub_data)

            if self.plot_powerspectrum:
                sub_data = numpy.mean(sub_data, 3)

            plt.waitforbuttonpress()

            #now start real plotting
            if not self.plot_powerspectrum:
                plot_cnt = 1
                for antenna_idx in xrange(0, len(antennas)):
                    for polarization_idx in xrange(0, len(polarizations)):
                        self.images[plot_cnt-1].set_data(sub_data[:,antenna_idx,polarization_idx,:])
                        self.images[plot_cnt-1].autoscale()
                        plot_cnt += 1
                self.update_canvas = True
            else:
                plot_cnt = 1
                for antenna_idx in xrange(0, len(antennas)):
                    for polarization_idx in xrange(0, len(polarizations)):
                        self.images[plot_cnt-1].set_ydata(sub_data[:,antenna_idx,polarization_idx])
                        self.subplots[plot_cnt-1].relim()
                        self.subplots[plot_cnt-1].autoscale_view()
                        plot_cnt += 1
                self.update_canvas = True

            # for antenna_idx in xrange(0, len(antennas)):
            #     for polarization_idx in xrange(0, len(polarizations)):
            #         self.images[plot_cnt-1].set_data(sub_data[:,antenna_idx,polarization_idx,:])
            #         self.images[plot_cnt-1].autoscale()
            #         plot_cnt += 1

            current_sample_start += n_samples_view

            #single colorbar
            if not self.plot_powerspectrum:
                im = self.images[len(self.images)-1]
                self.fig.subplots_adjust(right=0.8)
                cbar_ax = self.fig.add_axes([0.85, 0.15, 0.05, 0.7])
                if plot_cnt==1:
                    self.fig.colorbar(im, cax=cbar_ax)

            self.fig.canvas.draw()
            plt.show(block=False)
            print "Drawn!"
        plt.show()
        print "All file processed"

    def read_data(self, timestamp=None, channels=[], antennas=[], polarizations=[], n_samples=0, sample_offset=0):
        output_buffer = numpy.zeros([len(channels),len(antennas),len(polarizations), n_samples],dtype=self.ctype)
        try:
            file = self.load_file(timestamp)
            if not file is None:
                temp_dset = file["root"]
                temp_timestamp = temp_dset.attrs['timestamp']
            else:
                print "Invalid file timestamp, returning empty buffer."
                return output_buffer
        except Exception as e:
            print "Can't load file for data reading: ", e.message
            raise

        data_flushed = False
        while not data_flushed:
            try:
                file_items = temp_dset.attrs.items()
                file_groups = file.values()
                file_groups_names = [elem.name for elem in file_groups]
                for channel_idx in xrange(0, len(channels)):
                    current_channel = channels[channel_idx]
                    channel_name = "/"+"channel_" + str(current_channel)
                    if channel_name in file_groups_names:
                        channel_grp = file["channel_" + str(current_channel)]
                        if channel_grp.values()[0].name == channel_name+"/data":
                            dset = channel_grp["data"]
                            dset_rows = dset.shape[0]
                            dset_columns = dset.shape[1]
                            nof_items = dset[0].size
                            if (dset_rows == temp_dset.attrs["n_antennas"] * temp_dset.attrs["n_pols"]) and (dset_columns >= temp_dset.attrs["n_samples"]):
                                for antenna_idx in xrange(0, len(antennas)):
                                    current_antenna = antennas[antenna_idx]
                                    for polarization_idx in xrange(0, len(polarizations)):
                                        current_polarization = polarizations[polarization_idx]
                                        if sample_offset+n_samples > nof_items:
                                            output_buffer[channel_idx,antenna_idx,polarization_idx,:] = dset[(current_antenna*self.n_pols)+current_polarization, 0:nof_items]
                                        else:
                                            output_buffer[channel_idx,antenna_idx,polarization_idx,:] = dset[(current_antenna*self.n_pols)+current_polarization, sample_offset:sample_offset+n_samples]
                data_flushed = True
            except Exception as e:
                print "File appears to be in construction, re-trying."
                print "Closing file..."
                self.close_file(file)
                print "Sleeping..."
                time.sleep(5)
                print "Reloading file..."
                file = self.load_file(temp_timestamp)
        return output_buffer

    def write_data(self, data_ptr=None, timestamp=None):
        file = self.create_file(timestamp)
        # self.close_file(file)
        #file = self.load_file(timestamp)

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
    channels = 16
    antennas = 16
    pols = 2
    #samples = 131072
    samples = 128
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
    data = numpy.array([(a[i], b[i]) for i in range(0,len(a))], dtype=ctype)
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

    # print "Plotting"
    # channel_file = ChannelFormatFileManager(root_path="/media/andrea/hdf5", mode=FileModes.Read)
    # start = time.time()
    # channel_file.plot(timestamp=0, channels=range(0, 2), antennas=range(0, 2), polarizations=range(0, pols), n_samples=samples, sample_offset=0)
    # #channel_file.progressive_plot(timestamp=0, channels=range(0, channels), antennas=range(0, 2), polarizations=range(0, pols), sample_start=0, sample_end=samples, n_samples_view=10)
    # end = time.time()
    # print end - start

    channel_file_mgr = ChannelFormatFileManager(root_path="/media/andrea/hdf5", mode=FileModes.Read)
    #channel_file_mgr.progressive_plot(channels=range(0, channels), antennas=range(0, 2), polarizations=range(0, pols), sample_start=0, sample_end=samples, n_samples_view=10)
    #channel_file_mgr.plot(channels=range(0,4), antennas=range(0, 1), polarizations=range(0, 2), n_samples=samples, sample_offset=0)
    #channel_file_mgr.plot(power_spectrum = True, normalize = False, log_plot = False, real_time=True, channels=range(0,4), antennas=range(0, 1), polarizations=range(0, 2), n_samples=samples, sample_offset=0)
    channel_file_mgr.progressive_plot(power_spectrum = True, normalize = False, log_plot = False, channels=range(0, channels), antennas=range(0, 2), polarizations=range(0, pols), sample_start=0, sample_end=samples, n_samples_view=10)


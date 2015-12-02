from aavs_file import AAVSFileManager, FileModes, FileTypes
from matplotlib import pyplot as plt
import time
import numpy
import math
import sys

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
        data_flushed = False
        while not data_flushed:
            raw_grp = file["raw_"]
            dset = raw_grp["data"]
            nof_items = dset[0].size
            try:
                for antenna_idx in xrange(0, len(antennas)):
                    current_antenna = antennas[antenna_idx]
                    for polarization_idx in xrange(0, len(polarizations)):
                        current_polarization = polarizations[polarization_idx]
                        if sample_offset+n_samples > nof_items:
                            output_buffer[antenna_idx,polarization_idx,:] = dset[(current_antenna*self.n_pols)+current_polarization, 0:nof_items]
                        else:
                            output_buffer[antenna_idx,polarization_idx,:] = dset[(current_antenna*self.n_pols)+current_polarization, sample_offset:sample_offset+n_samples]
                data_flushed = True
            except Exception as e:
                print "File appears to be in construction, re-trying."
                self.close_file(file)
                file = self.load_file(timestamp)
        return output_buffer

    def do_plotting(self):
        timestamp = self.plot_timestamp
        channels = self.plot_channels
        antennas = self.plot_antennas
        polarizations = self.plot_polarizations
        n_samples = self.plot_n_samples
        sample_offset = self.plot_sample_offset

        data = self.read_data(timestamp=timestamp, antennas=antennas, polarizations=polarizations, n_samples=n_samples, sample_offset=sample_offset)

        #now start real plotting
        miny = sys.maxsize
        maxy = -sys.maxsize - 1
        plot_cnt = 1
        for antenna_idx in xrange(0, len(antennas)):
            for polarization_idx in xrange(0, len(polarizations)):
                self.plots[plot_cnt-1].set_ydata(data[antenna_idx,polarization_idx,:])
                if min(data[antenna_idx,polarization_idx,:])<miny:
                    miny = min(data[antenna_idx,polarization_idx,:])
                if max(data[antenna_idx,polarization_idx,:])>maxy:
                    maxy = max(data[antenna_idx,polarization_idx,:])
                self.subplots[plot_cnt-1].relim()
                self.subplots[plot_cnt-1].autoscale_view()
                plot_cnt += 1

        plot_cnt=1
        for antenna_idx in xrange(0, len(antennas)):
            for polarization_idx in xrange(0, len(polarizations)):
                self.subplots[plot_cnt-1].set_ylim([miny, maxy])
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
        dummy_data = numpy.zeros(n_samples)
        total_plots = len(antennas) * len(polarizations)
        plot_div_value = total_plots / 2.0;

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
                line, = subplot.plot(range(0, n_samples),dummy_data)
                subplot.set_title("Antenna: " + str(current_antenna) + " - Polarization: " + str(current_polarization), fontsize=9)
                self.plots.append(line)
                self.subplots.append(subplot)
                plt.xlabel('Time (sample)', fontsize=9)
                plt.ylabel('Amplitude', fontsize=9)
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

    def progressive_plot(self, timestamp=None, antennas=[], polarizations=[], sample_start=0, sample_end=0, n_samples_view=0):
        plt.ion()
        try:
            file = self.load_file(timestamp)
        except Exception as e:
            print "Can't load file: ", e.message
            raise

        self.plot(real_time=False, timestamp=timestamp,antennas=antennas, polarizations=polarizations, n_samples=n_samples_view)

        #now start real plotting
        current_sample_start = sample_start
        while (current_sample_start+n_samples_view) <= sample_end:
            #print current_sample_start
            plot_cnt = 1
            data = self.read_data(timestamp=timestamp, antennas=antennas, polarizations=polarizations, n_samples=n_samples_view, sample_offset=current_sample_start)
            for antenna_idx in xrange(0, len(antennas)):
                for polarization_idx in xrange(0, len(polarizations)):
                    self.plots[plot_cnt-1].set_ydata(data[antenna_idx,polarization_idx,:])
                    self.subplots[plot_cnt-1].relim()
                    self.subplots[plot_cnt-1].autoscale_view()
                    plot_cnt += 1
            current_sample_start += n_samples_view
            self.fig.canvas.draw()
            plt.show(block=False)
            plt.waitforbuttonpress()
            print "Drawn!"
        plt.show()
        print "All file processed"

    def write_data(self, data_ptr=None, timestamp=None):
        file = self.create_file(timestamp)
        self.close_file(file)
        file = self.load_file(timestamp)

        n_pols = self.main_dset.attrs['n_pols']
        n_antennas = self.main_dset.attrs['n_antennas']
        n_samp = self.main_dset.attrs['n_samples']
        self.main_dset.attrs['timestamp'] = timestamp

        raw_grp = file["raw_"]
        dset = raw_grp["data"]
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

if __name__ == '__main__':
    antennas = 16
    pols = 2
    #samples = 1048576 * 1 #(1MB * 1)
    samples = 1024
    runs = 1

    raw_file_mgr = RawFormatFileManager(root_path="/media/andrea/hdf5", mode=FileModes.Write)
    raw_file_mgr.set_metadata(n_antennas=antennas, n_pols=pols, n_samples=samples)
    #data = numpy.zeros(antennas * pols * samples, dtype='int8')
    data = numpy.arange(0,antennas * pols * samples,dtype='int8')

    start = time.time()
    for i in xrange(0, 1):
        for run in xrange(0, runs):
            raw_file_mgr.write_data(timestamp=run, data_ptr=data)
            #raw_file_mgr.append_data(timestamp=run, data_ptr=data)
    end = time.time()
    bits = (antennas * pols * samples * runs * 8)
    mbs = bits * 1.25e-7
    print "Write speed: " + str(mbs/(end - start)) + " Mb/s"

    # raw_file_mgr = RawFormatFileManager(root_path="/media/andrea/hdf5", mode=FileModes.Read)
    # print "reading back out"
    # start = time.time()
    # buffer = raw_file_mgr.read_data(timestamp=0, antennas=range(0, antennas), polarizations=range(0, pols), n_samples=samples)
    # print buffer.size
    # end = time.time()
    # print end - start

    # print "Plotting"
    # raw_file_mgr = RawFormatFileManager(root_path="/media/andrea/hdf5", mode=FileModes.Read)
    # start = time.time()
    # raw_file_mgr.plot(timestamp=0, antennas=range(0, 2), polarizations=range(0, pols), n_samples=samples, sample_offset=0)
    # #raw_file_mgr.progressive_plot(timestamp=0, antennas=range(0, 1), polarizations=range(0, 2), sample_start=0, sample_end=samples, n_samples_view=128)
    # end = time.time()
    # print end - start

    raw_file_mgr = RawFormatFileManager(root_path="/media/andrea/hdf5", mode=FileModes.Read)
    raw_file_mgr.plot(antennas=range(0, 1), polarizations=range(0, 2), n_samples=samples, sample_offset=0)

    raw_file_mgr.plot(real_time=True, antennas=range(0, 1), polarizations=range(0, 2), n_samples=samples, sample_offset=0)

import h5py
import numpy
import math
from abc import abstractmethod
from enum import Enum
import os
from scipy.signal.windows import slepian
import threading
import time
import zope.event
import signal
import sys
from threading import Thread


class FileTypes(Enum):
    Raw = 1
    Channel = 2
    Beamformed = 3


class FileModes(Enum):
    Read = 1
    Write = 2


class NewFileAddedEvent(object):
    def __init__(self, filename):
        self.filename = filename

    def get_name(self):
        return self.filename


class FileMonitor(Thread):
    def __init__(self, root_path='.', type=FileTypes.Raw, poll_delay=1):
        super(FileMonitor, self).__init__()
        self.root_path = root_path
        self.type = type
        self.poll_delay = poll_delay
        self.terminate = False
        del zope.event.subscribers[:]
        if not self.__check_path():
            print "Invalid directory"
            self.valid = False
        else:
            self.valid = True

    def run(self):
        counter = 0
        if self.valid:
            current_file_list = self.__get_file_list()
            while not self.terminate:
                try:
                    print "[" + str(counter) + "] - Polling for new files..."
                    time.sleep(self.poll_delay)
                    next_file_list = self.__get_file_list()
                    if not set(current_file_list) == set(next_file_list):
                        if len(next_file_list) > len(current_file_list):  # new file(s) added
                            print "\t [" + str(counter) + "] - New file detected!"
                            # We have a list of matched filename, sort by last modified date and get latest one
                            new_filename = sorted(next_file_list, cmp=lambda a, b: -1 if os.stat(a).st_mtime > os.stat(
                                b).st_mtime else 1)[0]
                            event = NewFileAddedEvent(filename=new_filename)
                            zope.event.notify(event)
                    current_file_list = next_file_list
                    counter += 1
                except (KeyboardInterrupt, SystemExit):
                    self.file_monitor.stop_file_monitor()
                    print "Exiting thread..."
            print "Monitor thread terminated."
        self.terminate = False

    def stop_file_monitor(self):
        self.terminate = True

    def start_file_monitor(self):
        self.terminate = False
        self.start()

    def __get_file_list(self):
        if self.type == FileTypes.Raw:
            filename_prefix = "raw_"
        elif self.type == FileTypes.Channel:
            filename_prefix = "channel_"
        elif self.type == FileTypes.Beamformed:
            filename_prefix = "beamformed_"

        matched_files = []
        if self.valid:
            files = next(os.walk(self.root_path))[2]
            for file in files:
                if file.startswith(filename_prefix) and file.endswith(".hdf5"):
                    matched_files.append(os.path.join(self.root_path, file))
        return matched_files

    def __check_path(self):
        if os.path.isdir(self.root_path):
            return True
        else:
            return False

    def add_subscriber(self, subscriber):
        zope.event.subscribers.append(subscriber)


# class FileMonitor(object):
#     # Class constructor
#     def __init__(self, root_path = '.', type=FileTypes.Raw):
#         self.root_path = root_path
#         self.type = type
#         self.thread_handler = threading.Thread(target=self.__run_file_monitor, args=(1,), daemon=True)
#         #self.thread_handler.daemon = True
#         self.terminate = False
#         del zope.event.subscribers[:]
#         if not self.__check_path():
#             print "Invalid directory"
#             self.valid = False
#         else:
#             self.valid = True
#
#     def __run_file_monitor(self, delay):
#         counter = 0
#         if self.valid:
#             current_file_list = self.__get_file_list()
#             while not self.terminate:
#                 try:
#                     print "[" + str(counter) + "] - Polling for new files..."
#                     time.sleep(delay)
#                     next_file_list = self.__get_file_list()
#                     if not set(current_file_list) == set(next_file_list):
#                         if len(next_file_list) > len(current_file_list): #new file(s) added
#                             print "\t [" + str(counter) + "] - New file detected!"
#                             # We have a list of matched filename, sort by last modified date and get latest one
#                             new_filename = sorted(next_file_list, cmp=lambda a, b: -1 if os.stat(a).st_mtime > os.stat(b).st_mtime else 1)[0]
#                             event = NewFileAddedEvent(filename=new_filename)
#                             zope.event.notify(event)
#                     current_file_list = next_file_list
#                     counter += 1
#                 except (KeyboardInterrupt, SystemExit):
#                     self.file_monitor.stop_file_monitor()
#                     print "Exiting thread..."
#             print "Monitor thread terminated."
#         self.terminate = False
#
#     def start_file_monitor(self):
#         if not self.thread_handler.isAlive():
#             self.terminate = False
#             self.thread_handler.start()
#         else:
#             print "Thread already running..."
#
#     def stop_file_monitor(self):
#         self.terminate = True
#
#     def __get_file_list(self):
#         if self.type == FileTypes.Raw:
#             filename_prefix = "raw_"
#         elif self.type == FileTypes.Channel:
#             filename_prefix = "channel_"
#         elif self.type == FileTypes.Beamformed:
#             filename_prefix = "beamformed_"
#
#         matched_files = []
#         if self.valid:
#             files = next(os.walk(self.root_path))[2]
#             for file in files:
#                 if file.startswith(filename_prefix) and file.endswith(".hdf5"):
#                     matched_files.append(os.path.join(self.root_path, file))
#         return matched_files
#
#     def __check_path(self):
#         if os.path.isdir(self.root_path):
#             return True
#         else:
#             return False
#
#     def add_subscriber(self, subscriber):
#         zope.event.subscribers.append(subscriber)

class AAVSFileManager(object):
    # Class constructor
    def __init__(self, root_path='', type=None, mode=FileModes.Read):
        self.type = type
        self.root_path = root_path
        self.mode = mode
        self.ctype = numpy.dtype([('real', numpy.int8), ('imag', numpy.int8)])

        # some default values
        self.real_time_timestamp = 0
        self.plot_timestamp = 0
        self.plot_channels = []
        self.plot_antennas = []
        self.plot_polarizations = []
        self.plot_n_samples = 0
        self.plot_sample_offset = 0

        self.update_canvas = False

        signal.signal(signal.SIGTERM, self.signal_term_handler)
        self.file_monitor = FileMonitor(root_path=root_path, type=type, poll_delay=1)
        self.file_monitor.add_subscriber(self.event_receiver)

    # def handle_close(self, evt):
    #     self.file_monitor.stop_file_monitor()

    @abstractmethod
    def configure(self, file):
        pass

    @abstractmethod
    def do_plotting(self):
        pass

    @abstractmethod
    def plot(self, real_time=True, timestamp=0, channels=[], antennas=[], polarizations=[], n_samples=0,
             sample_offset=0):
        pass

    def signal_term_handler(self, signal, frame):
        print 'Exiting in ~5 seconds...'
        self.stop_monitoring()
        time.sleep(5)
        sys.exit(0)

    def event_receiver(self, event):
        print 'Event received: ' + event.get_name()
        filename_ext = os.path.basename(event.get_name())
        filename, file_ext = os.path.splitext(filename_ext)
        filename_parts = filename.split('_')
        self.plot_timestamp = filename_parts[1]
        self.real_time_timestamp = filename_parts[1]
        self.do_plotting()

    def set_metadata(self, n_antennas=16, n_pols=2, n_stations=1, n_beams=1, n_tiles=1, n_chans=512, n_samples=0):
        self.n_antennas = n_antennas
        self.n_pols = n_pols
        self.n_stations = n_stations
        self.n_beams = n_beams
        self.n_tiles = n_tiles
        self.n_chans = n_chans
        self.n_samples = n_samples

    def complex_abs(self, value):
        return math.sqrt((value[0] ** 2) + (value[1] ** 2))

    def ingest_data(self, data_ptr=None, timestamp=0, append=False):
        if append:
            self.append_data(data_ptr=data_ptr, timestamp=timestamp)
        else:
            self.write_data(data_ptr=data_ptr, timestamp=timestamp)

    def check_root_integrity(self, file):
        integrity = True
        try:
            # check for root dataset in file
            file.require_dataset("root", shape=(1,), dtype='float16', exact=True)
            file_dset = file.get("root", default=None)
            if not file_dset == None:
                attrs_found = file_dset.attrs.items()
                dict_attrs_found = dict(attrs_found)
                if not dict_attrs_found.has_key("timestamp"):
                    integrity = False
                if not dict_attrs_found.has_key("n_antennas"):
                    integrity = False
                if not dict_attrs_found.has_key("n_pols"):
                    integrity = False
                if not dict_attrs_found.has_key("n_stations"):
                    integrity = False
                if not dict_attrs_found.has_key("n_beams"):
                    integrity = False
                if not dict_attrs_found.has_key("n_tiles"):
                    integrity = False
                if not dict_attrs_found.has_key("n_chans"):
                    integrity = False
                if not dict_attrs_found.has_key("n_samples"):
                    integrity = False
                if not dict_attrs_found.has_key("type"):
                    integrity = False
            else:
                integrity = False
        except Exception as e:
            integrity = False
        finally:
            return integrity

    def load_file(self, timestamp=None):
        if self.type == FileTypes.Raw:
            filename_prefix = "raw_"
        elif self.type == FileTypes.Channel:
            filename_prefix = "channel_"
        elif self.type == FileTypes.Beamformed:
            filename_prefix = "beamformed_"

        full_filename = None
        if not timestamp is None:
            full_filename = os.path.join(self.root_path, filename_prefix + str(timestamp) + ".hdf5")

        if timestamp is None or (not os.path.isfile(full_filename)):
            matched_files = []
            files = next(os.walk(self.root_path))[2]
            for file in files:
                if file.startswith(filename_prefix) and file.endswith(".hdf5"):
                    matched_files.append(os.path.join(self.root_path, file))
                    # We have a list of matched filename, sort by last modified date and get latest one
                    full_filename = sorted(matched_files, cmp=lambda a, b: -1 if os.stat(a).st_mtime > os.stat(b).st_mtime else 1)[0]

        if not full_filename is None:
            file_read = False
            slept_time = 0
            try:
                while not file_read and slept_time < 5:
                    file = h5py.File(full_filename, 'r+')
                    if self.check_root_integrity(file):
                        self.main_dset = file["root"]
                        self.n_antennas = self.main_dset.attrs['n_antennas']
                        self.n_pols = self.main_dset.attrs['n_pols']
                        self.n_stations = self.main_dset.attrs['n_stations']
                        self.n_beams = self.main_dset.attrs['n_beams']
                        self.n_tiles = self.main_dset.attrs['n_tiles']
                        self.n_chans = self.main_dset.attrs['n_chans']
                        self.n_samples = self.main_dset.attrs['n_samples']
                        file_read = True
                    else:
                        print str(slept_time) + " - Waiting for file integrity checks in " + full_filename
                        time.sleep(1)
                        slept_time += 1
                if not file_read:
                    raise RuntimeError(
                        'Requested file is either corrupt, or perpetually unavailable for further processing.')
                else:
                    return file
            except Exception as e:
                raise

    def create_file(self, timestamp=None):
        if self.type == FileTypes.Raw:
            filename_prefix = "raw_"
        elif self.type == FileTypes.Channel:
            filename_prefix = "channel_"
        elif self.type == FileTypes.Beamformed:
            filename_prefix = "beamformed_"
        full_filename = os.path.join(self.root_path, filename_prefix + str(timestamp) + ".hdf5")

        # check if file exists, delete if it does (we want to create here!)
        if os.path.isfile(full_filename):
            os.remove(full_filename)

        file = h5py.File(full_filename, 'w')
        os.chmod(full_filename, 0776);
        self.close_file(file)
        file = h5py.File(full_filename, 'r+')


        # if self.mode == FileModes.Read:
        #     file = h5py.File(full_filename, 'r+')
        #     os.chmod(full_filename, 0776);
        # elif self.mode == FileModes.Write:
        #     file = h5py.File(full_filename, 'w')
        #     os.chmod(full_filename, 0776);

        self.main_dset = file.create_dataset("root", (1,), chunks=True, dtype='float16')

        self.main_dset.attrs['timestamp'] = timestamp
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

    def stop_monitoring(self):
        self.file_monitor.stop_file_monitor()
        self.file_monitor.join()

    def start_monitoring(self):
        self.file_monitor.start_file_monitor()

# if __name__ == '__main__':
#     file_monitor = FileMonitor(root_path="/media/andrea/hdf5", type=FileTypes.Raw)
#     file_monitor.start_file_monitor()
#     #file_monitor.stop_file_monitr()

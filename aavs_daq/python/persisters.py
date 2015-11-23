__author__ = 'Alessio Magro'

from abc import abstractmethod
from enum import Enum
import h5py



class FileTypes(Enum):
    Raw = 1
    Channel = 2
    Beamformed = 3


class FileModes(Enum):
    Read = 1
    Write = 2

# --------------------------------------------------------- AAVS FILE --------------------------------------------------
class AAVSFile(object):
    # Class constructor

    def __init__(self, path = '', type = None, mode = FileModes.Read):
        self.type = type
        if mode == FileModes.Read:
            self.file = h5py.File(path, 'r')
        elif mode == FileModes.Write:
            self.file = h5py.File(path, 'w')
        self.main_dset = self.file.create_dataset("root", (10,), chunks=True,  dtype='float16')

    @abstractmethod
    def configure(self):
        pass

    def set_metadata(self, n_antennas = 16, n_pols = 2, n_stations = 1, n_beams = 1, n_tiles = 1, n_chans = 512, n_samples = 0):
        self.main_dset.attrs['n_antennas'] = n_antennas
        self.main_dset.attrs['n_pols'] = n_pols
        self.main_dset.attrs['n_stations'] = n_stations
        self.main_dset.attrs['n_beams'] = n_beams
        self.main_dset.attrs['n_tiles'] = n_tiles
        self.main_dset.attrs['n_chans'] = n_chans
        self.main_dset.attrs['n_samples'] = n_samples
        self.main_dset.attrs['type'] = self.type.value
        self.configure()

    @abstractmethod
    def ingest_data(self, data_ptr = None, timestamp = 0):
        """Method documentation"""
        return

# --------------------------------------------------------- BEAM FILE --------------------------------------------------
class BeamFormatFile(AAVSFile):

    # Class constructor
    def __init__(self, path = '', mode = FileModes.Read):
        super(BeamFormatFile, self).__init__(path=path, type=FileTypes.Raw, mode=mode)

    def configure(self):
        n_pols = self.main_dset.attrs['n_pols']
        n_samp = self.main_dset.attrs['n_samples']
        n_chans = self.main_dset.attrs['n_chans']
        for polarity in xrange(0, n_pols):
            polarity_grp = self.file.create_group("polarity_"+str(polarity))
            for channel in xrange(0, n_chans):
                channel_subgrp = polarity_grp.create_group("channel_"+str(channel))
                dset = channel_subgrp.create_dataset("data", (n_samp,), chunks=True,  dtype='complex64', maxshape=(None,))

    def ingest_data(self, data_ptr=None, timestamp=0):
        n_pols = self.main_dset.attrs['n_pols']
        n_samp = self.main_dset.attrs['n_samples']
        n_chans = self.main_dset.attrs['n_chans']
        self.main_dset.attrs['timestamp'] = timestamp
        for polarity in xrange(0, n_pols):
            polarity_grp = self.file["polarity_"+str(polarity)]
            for channel in xrange(0, n_chans):
                channel_subgrp = polarity_grp["channel_"+str(channel)]
                dset = channel_subgrp["data"]
                start_idx = (polarity * n_chans * n_samp) + channel
                end_idx = (polarity + 1) * n_chans * n_samp
                dset[:] = data_ptr[start_idx : end_idx : n_chans]
        self.file.flush()
        self.file.close()


# ------------------------------------------------------- CHANNEL FILE -------------------------------------------------
class ChannelFormatFile(AAVSFile):

    # Class constructor
    def __init__(self, path = '', mode = FileModes.Read):
        super(ChannelFormatFile, self).__init__(path=path, type=FileTypes.Raw, mode=mode)

    def configure(self):
        n_pols = self.main_dset.attrs['n_pols']
        n_antennas = self.main_dset.attrs['n_antennas']
        n_samp = self.main_dset.attrs['n_samples']
        n_chans = self.main_dset.attrs['n_chans']
        for channel in xrange(0, n_chans):
            channel_grp = self.file.create_group("channel_"+str(channel))
            for antenna in xrange(0, n_antennas):
                antenna_subgrp = channel_grp.create_group("antenna_"+str(antenna))
                for polarity in xrange(0, n_pols):
                    pol_subgrp = antenna_subgrp.create_group("polarity_"+str(polarity))
                    pol_subgrp.create_dataset("data", (n_samp,), chunks=True,  dtype='complex64', maxshape=(None,))

    def ingest_data(self, data_ptr=None, timestamp=0):
        n_pols = self.main_dset.attrs['n_pols']
        n_antennas = self.main_dset.attrs['n_antennas']
        n_samp = self.main_dset.attrs['n_samples']
        n_chans = self.main_dset.attrs['n_chans']
        self.main_dset.attrs['timestamp'] = timestamp
        for channel in xrange(0, n_chans):
            channel_grp = self.file["channel_" + str(channel)]
            for antenna in xrange(0, n_antennas):
                antenna_subgrp = channel_grp["antenna_" + str(antenna)]
                for polarity in xrange(0, n_pols):
                    pol_subgrp = antenna_subgrp["polarity_" + str(polarity)]
                    dset = pol_subgrp["data"]
                    start_idx = (channel * n_samp * n_pols * n_antennas) + (n_pols * antenna) + polarity
                    end_idx = ((channel + 1) * n_samp * n_pols * n_antennas)
                    dset[:] = data_ptr[start_idx : end_idx : n_antennas * n_pols]
        self.file.flush()
        self.file.close()


# --------------------------------------------------------- BEAM FILE --------------------------------------------------
class RawFormatFile(AAVSFile):

    # Class constructor
    def __init__(self, path = '', mode = FileModes.Read):
        super(RawFormatFile, self).__init__(path=path, type=FileTypes.Raw, mode=mode)

    def configure(self):
        n_pols = self.main_dset.attrs['n_pols']
        n_antennas = self.main_dset.attrs['n_antennas']
        n_samp = self.main_dset.attrs['n_samples']
        for antenna in xrange(0, n_antennas):
            antenna_grp = self.file.create_group("antenna_"+str(antenna))
            for polarity in xrange(0, n_pols):
                pol_subgrp = antenna_grp.create_group("polarity_"+str(polarity))
                dset = pol_subgrp.create_dataset("data", (n_samp,), chunks=True,  dtype='int8', maxshape=(None,))

    def ingest_data(self, data_ptr=None, timestamp=0):
        n_pols = self.main_dset.attrs['n_pols']
        n_antennas = self.main_dset.attrs['n_antennas']
        n_samp = self.main_dset.attrs['n_samples']
        self.main_dset.attrs['timestamp'] = timestamp
        for antenna in xrange(0, n_antennas):
            antenna_grp = self.file["antenna_" + str(antenna)]
            for polarity in xrange(0, n_pols):
                pol_subgrp = antenna_grp["polarity_" + str(polarity)]
                dset = pol_subgrp["data"]
                start_idx = antenna * n_samp * n_pols + polarity
                dset[:] = data_ptr[start_idx : start_idx + (n_samp * n_pols) : n_pols]
        self.file.flush()
        self.file.close()

if __name__ == '__main__':
    import time

    antennas = 16
    pols = 2
    samples = 1024
    raw_file = RawFormatFile(path="/home/andrea/test_raw.hdf5", mode=FileModes.Write)
    raw_file.set_metadata(n_antennas=antennas, n_pols=pols, n_samples=samples)
    raw_file.configure()
    data=[]
    for antenna in xrange(0,antennas):
        for sample in xrange(0,samples):
            data.append(sample)
            data.append(-sample)
    start = time.time()
    raw_file.ingest_data(timestamp=0, data_ptr=data)
    end = time.time()
    print end - start
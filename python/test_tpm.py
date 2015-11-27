from pyfabil import TPM, Device
from pyslalib import slalib
import numpy as np
import math

__author__ = 'Alessio Magro'

# --------------------------------------------- Beamformer Class ---------------------------------------


class Beamformer(object):
    """ Helper class for generating beamforming coefficients """

    def __init__(self, tile, nof_channels, nof_antennas, nof_pols, nof_beams, polarisation_fpga_map = None):
        """ Beamforming weight generation class
        :param tile: Reference to tile object
        :param nof_channels: Number of channels
        :param nof_antennas: Number of antennas
        :param nof_pols: Number of polarisations
        :param nof_beams: Number of beams
        :param polarisation_fpga_map: Mapping between polarisation index and FPGA index
        """

        # Initialise class member
        self._tile         = tile
        self._nof_channels = nof_channels
        self._nof_antennas = nof_antennas
        self._nof_pols     = nof_pols
        self._nof_beams    = nof_beams
        self._pol_fpga_map = polarisation_fpga_map if polarisation_fpga_map is not None else {0: 0, 1: 1}
        self._value_conversion_table = None

    def set_weights(self, weights):
        """ Set weights provided externally.
        :param weights Weights should be a numpy array with polarisation changing in the first dimension,
                       antenna in the second dimension and channel in the third dimension
        :return:
        """

        # Weights must be a numpy multi-dimensional array
        if type(weights) is not np.ndarray:
            raise Exception("Weights parameter to set wieghts must be a numpy array")

        # Weights shape must match beamformer parameters
        if np.shape(weights) != (self._nof_pols, self._nof_antennas, self._nof_channels, 2):
            raise Exception("Invalid weights shape")

        # Loop over polarisations
        for pol in range(self._nof_pols):
            # Loop over antennas
            for antenna in range(self._nof_antennas):

                # Convert weights to 8-bit values, reverse array and combine every 4 values into 32-bit words
                coeffs = weights[pol, antenna, :, :].flatten()[::-1]
                coeffs = self.convert_weights(coeffs)
                values = []
                for i in range(0, len(coeffs), 4):
                    value =  coeffs[i + 0]         |  \
                            (coeffs[i + 1] << 8)   |  \
                            (coeffs[i + 2] << 16)  |  \
                            (coeffs[i + 3] << 24)
                    values.append(value)

                self._tile.tpm.tpm_test_firmware[self._pol_fpga_map[pol]].download_beamforming_weights(values, antenna)

    def convert_weights(self, weights, signed=False):
        """ Convert weights from float (assuming range is between 0 and 1) to 8-bit
        :param weights: Input weight matrix
        :param signed: Use signed (-1 to 1) or unsigned (0 t0 1) values
        :return: Converted weight matrix
        """

        # If value conversion table is none, convert it
        if self._value_conversion_table is None:
            if signed:
                self._value_conversion_table = np.arange(256) * (1 / 127.0) - 1
            else:
                self._value_conversion_table = np.arange(128) * (1 / 127.0)

        # Apply conversion
        values = np.empty(np.size(weights), dtype='int8')
        for i, w in enumerate(weights):
            for j, val in enumerate(self._value_conversion_table):
                if val >= w:
                    values[i] = j
                    break

        return values

    def generate_empty_weights(self):
        """
        :return: Return an empty numpy array of the correct shape
        """
        return np.zeros((self._nof_pols, self._nof_antennas, self._nof_channels, 2))

    def _convert_coordinates(self, lat, long, ra_ref, dec_ref, date, time):
        """ Accurate conversion from equatorial coordiantes (RA, DEC) to Spherical (TH,PH) coordinates.
        The code uses the pyslalib library for a number of functions from the SLALIB Fortran library converted to Python.
        :param lat: latitude (decimal degrees)
        :param long: longitude (decimal degrees)
        :param ra_ref: RA(J2000) (decimal hours)
        :param dec_ref: Dec(J2000) (decimal degrees)
        :param date: vector date [iyear, imonth, iday]
        :param time: vector time [ihour imin isec]
        :return: [theta, pi]: Theta and Phi angles (degrees)
        """

        const_2pi = 2.0 * math.pi
        d2r = math.pi / 180
        r2d = 180 / math.pi

        # Conversion factor seconds of time to days
        const_st2day = 1.0/(24 * 3600)

        # Specify latitude and longitude (radians)
        lat *= d2r
        long *= d2r

        # Specify catalogued position (J2000 coordinates, radians)
        ra_ref = ra_ref * 15 * d2r
        dec_ref *= d2r

        # Specify current time and date %
        isec   = time[2]
        imin   = time[1]
        ihour  = time[0]
        iday   = date[2]
        imonth = date[1]
        iyear  = date[0]

        # Convert current UTC to Modified Julian date
        djm, j1   = slalib.sla_cldj(iyear, imonth, iday)
        fdutc, j2 = slalib.sla_dtf2d(ihour, imin, isec)
        djutc     = djm + fdutc

        # Calculate Greenwich Mean Sidereal Time from MJD
        gmst1 = slalib.sla_gmst(djutc)

        # Add longitude and Equation of Equinoxes for Local Apparent ST
        djtt = djutc + slalib.sla_dtt(djutc)*const_st2day
        last = gmst1 + long + slalib.sla_eqeqx(djtt)
        if last < 0.0:
            last += const_2pi

        # Convert catalogued position to apparent RA, Dec at current date
        pr = 0.e0
        pd = 0.e0
        px = 0.e0
        rv = 0.e0
        eq = 2000.0e0
        [raobs, decobs] = slalib.sla_map(ra_ref, dec_ref, pr, pd, px, rv, eq, djutc)

        # Get Hour Angle and Declination
        ha = last - raobs
        if ha < -math.pi:
            ha += const_2pi

        if ha > math.pi:
            ha -= const_2pi
        dec = decobs

        # Convert to Azimuth and Elevation
        azim, elev = slalib.sla_de2h(ha, dec, lat)

        theta = (90 - elev * r2d).real
        phi = (azim * r2d).real

        return [theta, phi]

# ------------------------------------------------ Tile Class ---------------------------------------

class Tile(object):

    def __init__(self, ip="10.0.10.2", port=10000):
        self._ip   = ip
        self._port = port
        self.tpm   = None

    # ---------------------------- Main functions ------------------------------------

    def connect(self, initialise=False, simulation=False):
        # Connect to board
        self.tpm = TPM(ip=self._ip, port=self._port, initialise=initialise, simulator=simulation)

        # Load tpm test firmware for both FPGAs (no need to load in simulation)
        if not simulation:
            self.tpm.load_plugin("TpmTestFirmware", device=Device.FPGA_1)
            self.tpm.load_plugin("TpmTestFirmware", device=Device.FPGA_2)

    def initialise(self):
        # Connect and initliase

        # Connect to board
        self.connect(initialise=True)

        # Initialise firmware plugin
        # Try except temporary due to fault board
        try:
            for firmware in self.tpm.tpm_test_firmware:
                firmware.initialise_firmware()
        except:
            pass

        # Enable streaming
        self.tpm["board.regfile.c2c_stream_enable"] = 0x1

        # Synchronise FPGAs
        self.sync_fpgas()

        # Temporary
        self.tpm[0x30000024] = 0x0

    def program_fpgas(self, bitfile="/home/lessju/Code/TPM-Access-Layer/bitfiles/xtpm_xcku040_tpm_top_wrap_timestamp.bit"):
        self.connect(simulation=True)
        self.tpm.download_firmware(Device.FPGA_1, bitfile)

    # ---------------------------- Synchronisation routines ------------------------------------
    def sync_fpgas(self):
        devices = ["fpga1", "fpga2"]
        print "Syncing FPGAs"
        for f in devices:
            self.tpm['%s.pps_manager.pps_gen_tc' % f] = 0xA6E49BF  #700 MHz!

        # setting sync time
        for f in devices:
            self.tpm["%s.pps_manager.sync_time_write_val" % f] = 0x0

        # sync time write command
        for f in devices:
            self.tpm["%s.pps_manager.sync_time_cmd.wr_req" % f] = 0x1

        self.check_synchornisation()

    def check_synchornisation(self):
        t0, t2 = 0, 1
        while t0 != t2:
            t0 = self.tpm["fpga1.pps_manager.sync_time_read_val"]
            t1 = self.tpm["fpga2.pps_manager.sync_time_read_val"]
            t2 = self.tpm["fpga1.pps_manager.sync_time_read_val"]

        fpga = "fpga1" if t0 > t1 else "fpga2"
        for i in range(abs(t1 - t0)):
            print "Decrementing %s by 1" % fpga
            self.tpm["%s.pps_manager.sync_time_cmd.down_req" % fpga] = 0x1

    def synchronise_operation(self):

        # Arm FPGAs
        for fpga in self.tpm.tpm_fpga:
            fpga.fpga_arm_force()

        # Read arm time
        t0 = self.tpm["fpga1.pps_manager.sync_time_read_val"]

        # Set arm time
        delay = 2
        for fpga in self.tpm.tpm_fpga:
            fpga.fpga_apply_sync_delay(t0 + delay)

    # ---------------------------- Wrapper for data acquisition ------------------------------------
    def send_raw_data(self):
        """ Send raw data from the TPM """
        self.synchronise_operation()
        for i in range(len(self.tpm.tpm_test_firmware)):
            self.tpm.tpm_test_firmware[i].send_raw_data()

    def send_channelised_data(self, number_of_samples = 128):
        """ Send channelized data from the TPM """
        self.synchronise_operation()
        for i in range(len(self.tpm.tpm_test_firmware)):
            self.tpm.tpm_test_firmware[i].send_channelised_data(number_of_samples)

    def send_channelised_data_continuous(self, channel_id, number_of_samples = 128):
        """ Continuously send channelised data from a single channel
        :param channel_id: Channel ID
        """
        self.synchronise_operation()
        for i in range(len(self.tpm.tpm_test_firmware)):
            self.tpm.tpm_test_firmware[i].send_channelised_data_continuous(channel_id, number_of_samples)

    def stop_channelised_data_continuous(self):
        """ Stop sending channelised data """
        for i in range(len(self.tpm.tpm_test_firmware)):
            self.tpm.tpm_test_firmware[i].stop_channelised_data_continuous()

    def send_beam_data(self):
        """ Send beam data from the TPM """
        self.synchronise_operation()
        for i in range(len(self.tpm.tpm_test_firmware)):
            self.tpm.tpm_test_firmware[i].send_beam_data()

    def __str__(self):
        return str(self.tpm)

if __name__ == "__main__":
    tile = Tile()
   # tile.program_fpgas()
   # tile.initialise()
  #  tile.connect()
  #  tile.send_raw_data()

    # beamformer = Beamformer(tile, 512, 16, 2, 1)
    # weights = beamformer.generate_empty_weights()
    # for p in range(1):
    #     for a in range(16):
    #         weights[p,a] = (np.arange(1024) / 1024.0).reshape((512,2))
    # beamformer.set_weights(weights)


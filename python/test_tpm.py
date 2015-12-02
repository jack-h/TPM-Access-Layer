from pyfabil import TPM, Device
from pyslalib import slalib
from time import sleep
from sys import exit
import numpy as np
import threading
import logging
import math
import time
import os

__author__ = 'Alessio Magro'

# --------------------------------------------- Beamformer Class ---------------------------------------
class AntennaArray(object):
    """ Class representing antenna array """
    def __init__(self, reference_latitude, reference_longitude):
        self._ref_lat    = reference_latitude
        self._ref_lon    = reference_longitude
        self._x          = None
        self._y          = None

    def positions(self):
        """
        :return: Antenna positions
        """
        return self._x, self._y

    def lat(self):
        """ Return reference latitude
        :return: reference latitude
        """
        return self._ref_lat

    def long(self):
        """ Return reference longitude
        :return: reference longitude
        """
        return self._ref_lon

    def load_from_file(self, filepath):
        """ Load antenna positions from file
        :param filepath: Path to file
        """
        pass


class Beamformer(object):
    """ Helper class for generating beamforming coefficients """

    def __init__(self, tile, nof_channels, nof_antennas, nof_pols, nof_beams,
                array = None, polarisation_fpga_map = None):
        """ Beamforming weight generation class
        :param tile: Reference to tile object
        :param nof_channels: Number of channels
        :param nof_antennas: Number of antennas
        :param nof_pols: Number of polarisations
        :param nof_beams: Number of beams
        :param array: AntennaArray object, required for source pointing
        :param polarisation_fpga_map: Mapping between polarisation index and FPGA index
        """

        # Initialise class member
        self._tile         = tile
        self._nof_channels = nof_channels
        self._nof_antennas = nof_antennas
        self._nof_pols     = nof_pols
        self._nof_beams    = nof_beams
        self._pol_fpga_map = polarisation_fpga_map if polarisation_fpga_map is not None else {0: 0, 1: 1}
        self._array        = array
        self._value_conversion_table = None
        self.weights      = None

    def download_weights(self):
        """ Set weights provided externally. """

        # Weights must be a numpy multi-dimensional array
        if type(self.weights) is not np.ndarray:
            raise Exception("Weights parameter to set wieghts must be a numpy array")

        # Weights shape must match beamformer parameters
        if np.shape(self.weights) != (self._nof_pols, self._nof_antennas, self._nof_channels, 2):
            raise Exception("Invalid weights shape")

        # Loop over polarisations
        for pol in range(self._nof_pols):
            # Loop over antennas
            for antenna in range(self._nof_antennas):

                # Convert weights to 8-bit values, reverse array and combine every 4 values into 32-bit words
                coeffs = self.weights[pol, antenna, :, :].flatten()
                coeffs = self.convert_weights(coeffs)
                values = []
                for i in range(0, len(coeffs), 4):
                    value =  coeffs[i + 0]         |  \
                            (coeffs[i + 1] << 8)   |  \
                            (coeffs[i + 2] << 16)  |  \
                            (coeffs[i + 3] << 24)
                    values.append(value)

                self._tile.tpm.tpm_test_firmware[self._pol_fpga_map[pol]].download_beamforming_weights(values, antenna)

    def convert_weights(self, coeffs, signed=False):
        """ Convert weights from float (assuming range is between 0 and 1) to 8-bit
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
        values = np.empty(np.size(coeffs), dtype='int8')
        for i, w in enumerate(coeffs):
            for j, val in enumerate(self._value_conversion_table):
                if val >= w:
                    values[i] = j
                    break

        return values

    def generate_empty_weights(self, ones=False):
        """ Generate a matrix containing only ones or zeros
        :param ones: Fill matrix with ones, if False fill it with zeros
        :return: Return a weight matrix containing only ones or zeros
        """
        if ones:
            self.weights = np.ones((self._nof_pols, self._nof_antennas, self._nof_channels, 2))
        else:
            self.weights = np.zeros((self._nof_pols, self._nof_antennas, self._nof_channels, 2))

    def set_antennas_channels(self, antennas=None, channels=None, polarisations=None):
        """ Generate beamforming coefficients to set particular channels and antennas, for particular polarisations
        :param antennas: Antennas to set
        :param channels: Channels to set
        :param polarisations: Polarisation to which set is applied
        :return: Weight matrix
        """
        self._apply_value_antennas_channels(antennas=antennas, 
                                            channels=channels, 
                                            polarisations=polarisations, 
                                            value=1)

    def mask_antennas_channels(self, antennas=None, channels=None, polarisations=None):
        """ Generate beamforming coefficients to mask particular channels and antennas, for particular polarisations
        :param antennas: Antennas to mask
        :param channels: Channels to mask
        :param polarisations: Polarisation to which mask is applied
        :return: Weight matrix
        """
        self._apply_value_antennas_channels(antennas=antennas, 
                                            channels=channels, 
                                            polarisations=polarisations, 
                                            value=0)

    def _apply_value_antennas_channels(self, antennas=None, channels=None, polarisations=None, value=1):
        """ Generate beamforming coefficients to apply value to particular channels and antennas, for particular polarisations
        :param antennas: Antennas to apply value
        :param channels: Channels to apply value
        :param polarisations: Polarisation to which value is applied
        :param value: value to set 
        :return: Weight matrix
        """

        # Check if polarisation is specified, otherwise apply to all
        pols = range(self._nof_pols) if polarisations is None \
            else [polarisations] if type (polarisations) is not list else polarisations

        # Check antenna and channel selection
        if antennas is None and channels is None:
            print "Antenna and channels list must be specified"

        # Optimsed for all channel masking
        if channels is None:
            ants = range(self._nof_antennas) if antennas is None \
            else [antennas] if type(antennas) is not list else antennas

            # Apply masking
            for p in pols:
                for a in ants:
                    self.weights[p, a, :, :] = np.zeros((self._nof_channels, 2)) * value

            return

        # Optimsed for all antenna masking
        if antennas is None:
            chans = range(self._nof_channels) if channels is None \
                    else [channels] if type(channels) is not list else channels

            # Apply masking
            for p in pols:
                for c in chans:
                    self.weights[p, :, c, :] = np.zeros((self._nof_antennas, 2)) * value

            return

        # Convert antennas and channels to lists
        ants = range(self._nof_antennas) if antennas is None \
            else [antennas] if type(antennas) is not list else antennas
        chans = range(self._nof_channels) if channels is None \
            else [channels] if type(channels) is not list else channels

        # Apply masking
        for p in pols:
            for a in ants:
                for c in channels:
                    self.weights[p, a, c, :] = [0, 0]

    def point_array(self, ra, dec, date, time):
        """ Point array to specified RA and DEC
        :param ref: RA(J2000) (decimal hours)
        :param ref: Dec(J2000) (decimal degrees)
        :param date: vector date [iyear, imonth, iday]
        :param time: vector time [ihour imin isec]
        """

        # Check if we have a reference AntennaArray
        if self._array is None:
            print "Need an AntennaArray reference to generate pointing weights"
            return

        # Check if antenna positions are set
        x, y = self._array.positions()
        if None in [x, y]:
            print "AntennaArray positions not set"
            return

        # Convert coordinates to theta and phi
        theta, phi = self._convert_coordinates(self._array.lat(), self._array.lat(),
                                               ra, dec, date, time)

        # Apply theta and phi to array and generate weights
        # TODO: Frequency information required here
        r = 10e9
        dx0 = r * math.sin(theta) * math.cos(phi) - x
        dy0 = r * math.sin(theta) * math.sin(phi) - y
        dz0 = r * math.cos(theta) # Z should be included here if it is known
        Wc = math.exp(-1j * k0 * math.sqrt(dx0**2 + dy0**2 + dz0**2))


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

        # Threads for continuously sending data
        self._RUNNING = 2
        self._ONCE    = 1
        self._STOP    = 0
        self._daq_threads = { }

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

        # Set destination and source IP/MAC/ports for 10G cores
        self.tpm.tpm_10g_core[0].set_src_mac(0x620000000002)
        self.tpm.tpm_10g_core[0].set_dst_mac(0xF452144C4A60)
        self.tpm.tpm_10g_core[0].set_src_ip("192.168.7.12")
        self.tpm.tpm_10g_core[0].set_dst_ip("192.168.7.1")
        self.tpm.tpm_10g_core[0].set_src_port(0xF0D0)
        self.tpm.tpm_10g_core[0].set_dst_port(0xF0D1)

        self.tpm.tpm_10g_core[1].set_src_mac(0x620000000003)
        self.tpm.tpm_10g_core[1].set_dst_mac(0xF452144C4A61)
        self.tpm.tpm_10g_core[1].set_src_ip("192.168.7.11")
        self.tpm.tpm_10g_core[1].set_dst_ip("192.168.8.1")
        self.tpm.tpm_10g_core[1].set_src_port(0xF0D0)
        self.tpm.tpm_10g_core[1].set_dst_port(0xF0D2)

        # Temporary
        self.tpm[0x30000024] = 0x0

        # Temporary: enable test pattern for channelised data
        try:
            self.tpm['fpga1.regfile.test_gen_walking'] = 0x1
            self.tpm['fpga2.regfile.test_gen_walking'] = 0x1
        except:
            pass

        # Temporary: Set beamforming truncation range
        try:
            self.tpm['fpga1.beamf.truncate_adj'] = 0x6
            self.tpm['fpga2.beamf.truncate_adj'] = 0x6
        except:
            pass

    def program_fpgas(self, bitfile="/home/lessju/Code/TPM-Access-Layer/bitfiles/xtpm_xcku040_tpm_top_wrap_truncate3.bit"):
        self.connect(simulation=True)
        self.tpm.download_firmware(Device.FPGA_1, bitfile)

    def get_temperature(self):
        """ Get board temperature """
        self.tpm[0x40000004] = 0x5
        self.tpm[0x40000000] = 0x2118
        temp = self.tpm[0x40000008]
        temp = ((temp >> 8) & 0x00FF) | ((temp << 8) & 0x1F00)
        return temp * 0.0625

    # ---------------------------- Synchronisation routines ------------------------------------
    def sync_fpgas(self):
        devices = ["fpga1", "fpga2"]

        for f in devices:
            self.tpm['%s.pps_manager.pps_gen_tc' % f] = 0xA6E49BF  # 700 MHz!

        # Setting sync time
        for f in devices:
            self.tpm["%s.pps_manager.sync_time_write_val" % f] = int(time.time())

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

    def synchronised_data_operation(self):
        # Arm FPGAs
        for fpga in self.tpm.tpm_fpga:
            fpga.fpga_arm_force()

        # Wait while previous data requests are processed
        while self.tpm['fpga1.lmc_gen.request'] != 0 or  \
              self.tpm['fpga2.lmc_gen.request'] != 0:
            logging.info("Waiting for enable to be reset")
            sleep(0.5)

        # Read arm time
        t0 = self.tpm["fpga1.pps_manager.sync_time_read_val"]

        # Set arm time
        delay = 2
        for fpga in self.tpm.tpm_fpga:
            fpga.fpga_apply_sync_delay(t0 + delay)

    # ---------------------------- Wrapper for data acquisition: RAW ------------------------------------
    def _send_raw_data(self, period = 0):
        """ Repeatedly send raw data from the TPM """
        # Loop indefinitely if a period is defined
        while(self._daq_threads['RAW'] != self._STOP):
            # Data transmission should be syncrhonised across FPGAs
            self.synchronised_data_operation()

            # Send data from all FPGAs
            for i in range(len(self.tpm.tpm_test_firmware)):
                self.tpm.tpm_test_firmware[i].send_raw_data()

            # Period should be >= 2, otherwise return
            if self._daq_threads['RAW'] == self._ONCE:
                return

            # Sleep for defined period
            sleep(period)

        # Finished looping, exit
        self._daq_threads.pop('RAW')

    def send_raw_data(self, period = 0):
        """ Send raw data from the TPM """
        # Period sanity check
        if period <= 2:
            self._daq_threads['RAW'] = self._ONCE
            self._send_raw_data()
            self._daq_threads.pop('RAW')
            return

        # Stop any other streams
        self.stop_data_transmission()

        # Create thread which will continuously send raw data
        t = threading.Thread(target = self._send_raw_data, args = (period,))
        self._daq_threads['RAW'] = self._RUNNING
        t.start()

    def stop_raw_data(self):
        """ Stop sending raw data """
        if 'RAW' in self._daq_threads.keys():
            self._daq_threads['RAW'] = self._STOP

    # ---------------------------- Wrapper for data acquisition: CHANNEL ------------------------------------
    def _send_channelised_data(self, number_of_samples=128, period=0):
        """ Send channelized data from the TPM """
        # Loop indefinitely if a period is defined
        while(self._daq_threads['CHANNEL'] != self._STOP):
            # Data transmission should be syncrhonised across FPGAs
            self.synchronised_data_operation()

            # Send data from all FPGAs
            for i in range(len(self.tpm.tpm_test_firmware)):
                self.tpm.tpm_test_firmware[i].send_channelised_data(number_of_samples)

            # Period should be >= 2, otherwise return
            if self._daq_threads['CHANNEL'] == self._ONCE:
                return

            # Sleep for defined period
            sleep(period)

        # Finished looping, exit
        self._daq_threads.pop('CHANNEL')

    def send_channelised_data(self, number_of_samples=128, period=0):
        """ Send channelised data from the TPM """
        # Period sanity check
        if period <= 2:
            self._daq_threads['CHANNEL'] = self._ONCE
            self._send_channelised_data()
            self._daq_threads.pop('CHANNEL')
            return

        # Stop any other streams
        self.stop_data_transmission()

        # Create thread which will continuously send raw data
        t = threading.Thread(target = self._send_channelised_data, args = (number_of_samples,period,))
        self._daq_threads['CHANNEL'] = self._RUNNING
        t.start()

    def stop_channelised_data(self):
        """ Stop sending channelised data """
        if 'CHANNEL' in self._daq_threads.keys():
            self._daq_threads['CHANNEL'] = self._STOP

    # ---------------------------- Wrapper for data acquisition: BEAM ------------------------------------
    def _send_beam_data(self, period = 0):
        """ Send beam data from the TPM """
        # Loop indefinitely if a period is defined
        while(self._daq_threads['BEAM'] != self._STOP):
            # Data transmission should be syncrhonised across FPGAs
            self.synchronised_data_operation()

            # Send data from all FPGAs
            for i in range(len(self.tpm.tpm_test_firmware)):
                self.tpm.tpm_test_firmware[i].send_beam_data()

            # Period should be >= 2, otherwise return
            if self._daq_threads['BEAM'] == self._ONCE:
                return

            # Sleep for defined period
            sleep(period)

        # Finished looping, exit
        self._daq_threads.pop('BEAM')

    def send_beam_data(self, period = 0):
        """ Send beam data from the TPM """
        # Period sanity check
        if period <= 2:
            self._daq_threads['BEAM'] = self._ONCE
            self._send_beam_data()
            self._daq_threads.pop('BEAM')
            return

    def stop_beam_data(self):
        """ Stop sending raw data """
        if 'BEAM' in self._daq_threads.keys():
            self._daq_threads['BEAM'] = self._STOP

    # ---------------------------- Wrapper for data acquisition: CSP ------------------------------------
    def send_csp_data(self, samples_per_packet, number_of_samples):
        """ Send CSP data
        :param samples_per_packet: Number of samples in a packet
        :param number_of_samples: Total number of samples to send
        :return:
        """
        
        # Manually set arm force
        for fpga in self.tpm.tpm_fpga:
            fpga.fpga_disarm_force()

        for i in range(len(self.tpm.tpm_test_firmware)):
            self.tpm.tpm_test_firmware[i].send_csp_data(samples_per_packet, number_of_samples)

    # ---------------------------- Wrapper for data acquisition: CONT CHANNEL ----------------------------
    def send_channelised_data_continuous(self, channel_id, number_of_samples = 128):
        """ Continuously send channelised data from a single channel
        :param channel_id: Channel ID
        """
        self.synchronised_data_operation()
        for i in range(len(self.tpm.tpm_test_firmware)):
            self.tpm.tpm_test_firmware[i].send_channelised_data_continuous(channel_id, number_of_samples)

    def stop_channelised_data_continuous(self):
        """ Stop sending channelised data """
        for i in range(len(self.tpm.tpm_test_firmware)):
            self.tpm.tpm_test_firmware[i].stop_channelised_data_continuous()

    def stop_data_transmission(self):
        """ Stop all data transmission from TPM"""
        for k, v in self._daq_threads.iteritems():
            if v == self._RUNNING:
                logging.info("Stopping transmission of %s data" % k)
                self._daq_threads[k] = self._STOP

    def __str__(self):
        return str(self.tpm)

if __name__ == "__main__":

    # Use OptionParse to get command-line arguments
    from optparse import OptionParser
    from sys import argv, stdout

    parser = OptionParser(usage="usage: %test_tpm [options]")
    parser.add_option("-a", "--nof_antennas", action="store", dest="nof_antennas",
                      type="int", default=16, help="Number of antennas [default: 16]")
    parser.add_option("-c", "--nof_channels", action="store", dest="nof_channels",
                      type="int", default=512, help="Number of channels [default: 512]")
    parser.add_option("-b", "--nof_beams", action="store", dest="nof_beams",
                      type="int", default=1, help="Number of beams [default: 1]")
    parser.add_option("-p", "--nof_pols", action="store", dest="nof_polarisations",
                      type="int", default=2, help="Number of polarisations [default: 2]")
    parser.add_option("-f", "--bitfile", action="store", dest="bitfile",
                      default=None, help="Bitfile to use (-P still required) [default: Local bitfile]")
    parser.add_option("-P", "--program", action="store_true", dest="program",
                      default=False, help="Program FPGAs [default: False]")
    parser.add_option("-T", "--test", action="store_true", dest="test",
                      default=False, help="Load test firmware (-P still required) [default: False]")
    parser.add_option("-I", "--initialise", action="store_true", dest="initialise",
                      default=False, help="Initialie TPM [default: False]")
    parser.add_option("-B", "--initialise-beamformer", action="store_true", dest="beamformer",
                  default=False, help="Initialie beamformer [default: False]")
    (conf, args) = parser.parse_args(argv[1:])

    # Set logging
    log = logging.getLogger('')
    log.setLevel(logging.INFO)
    format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    ch = logging.StreamHandler(stdout)
    ch.setFormatter(format)
    log.addHandler(ch)

    # Create Tile
    tile = Tile()

    # Porgam FPGAs if required
    if conf.program:
        logging.info("Programming FPGAs")
        if conf.test:
            logging.info("Using test firmware (xtpm_xcku040_tpm_top_wrap_timestamp.bit)")
            tile.program_fpgas(bitfile="/home/lessju/Code/TPM-Access-Layer/bitfiles/xtpm_xcku040_tpm_top_wrap_timestamp.bit")
        elif conf.bitfile is not None:
            logging.info("Using bitfile %s" % conf.bitfile)
            if os.path.exists(conf.bitfile) and os.path.isfile(conf.bitfile):
                tile.program_fpgas(bitfile=conf.bitfile)
            else:
                logging.error("Could not load bitfile %s, check filepath" % conf.bitfile)
                exit(-1)
        else:
            logging.info("Using local bitfile")
            tile.program_fpgas()

    # Initialise TPM if required
    if conf.initialise:
        logging.info("Initialising TPM")
        tile.initialise()

    tile.connect()

    # Initialise beamformer if required
    beamformer = None
    if conf.beamformer:
        logging.info("Initialising beamformer")
        beamformer = Beamformer(tile, conf.nof_channels, conf.nof_antennas, conf.nof_polarisations, conf.nof_beams)

    # Example commands (to generate weigts, mask antennas and download coefficients to TPM
    #beamformer.generate_empty_weights(ones=True)
    #beamformer.mask_antennas_channels(antennas=[2,4,6])
    #beamformer.download_weights()



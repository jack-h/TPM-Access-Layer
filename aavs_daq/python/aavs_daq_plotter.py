#!/usr/bin/env python

import logging

__author__ = 'Alessio Magro'

from persisters import *

# Configuration object, will be filled in by optparse
conf = { }

def extract_values(values):
    """ Extract values from string representation of list
    :param values: String representation of values
    :return: List of values
    """

    # Return list
    converted = []
    #try:
    # Loop over all comma separated values
    for item in values.split(","):
        # Check if item contains a semi-colon
        if item.find(":") > 0:
            index = item.find(":")
            lower = item[:index]
            upper = item[index+1:]
            converted.extend(range(int(lower), int(upper)))
        else:
            converted.append(int(item))
    #except:
    #    raise Exception("Invalid values parameter: %s" % values)

    return converted

def plot_raw_data():
    """ Plot raw data """
    global conf
    raw_plot = RawFormatFileManager(root_path=conf.directory, mode=FileModes.Read)
    raw_plot.plot(real_time=conf.real_time,
                  timestamp=conf.timestamp,
                  antennas=conf.antennas,
                  polarizations=conf.polarisations,
                  n_samples=conf.nof_samples,
                  sample_offset=conf.sample_offset)

def plot_channel_data():
    """ Plot channelised data """
    global conf
    channel_plot = ChannelFormatFileManager(root_path=conf.directory, mode=FileModes.Read)
    channel_plot.plot(real_time=conf.real_time,
                      timestamp=conf.timestamp,
                      channels=conf.channels,
                      antennas=conf.antennas,
                      polarizations=conf.polarisations,
                      n_samples=conf.nof_samples,
                      sample_offset=conf.sample_offset,
	              log_plot=conf.log,
                      power_spectrum=conf.power_spectrum,
		      normalize=conf.normalize)

def plot_beam_data():
    """ Plot beam data """
    global conf
    beam_plot = BeamFormatFileManager(root_path=conf.directory, mode=FileModes.Read)
    beam_plot.plot(real_time=conf.real_time,
                   timestamp=conf.tiemstamp,
                   channels=conf.channels,
                   polarizations=conf.polarisations,
                   n_samples=conf.nof_samples,
                   sample_offset=conf.sample_offset)

# Script entry point
if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv, stdout

    parser = OptionParser(usage="usage: %aavs_daq_plotter [options]")

    # Plotting modes
    parser.add_option("-R", "--plot_raw_data", action="store_true", dest="plot_raw_data",
                      default=False, help="Plot raw data [default: False]")
    parser.add_option("-C", "--plot_channel_data", action="store_true", dest="plot_channel_data",
                      default=False, help="Plot channelised data [default: False]")
    parser.add_option("-B", "--plot_beam_data", action="store_true", dest="plot_beam_data",
                      default=False, help="Plot beam data [default: False]")

    # Plotting parameters
    parser.add_option("-r", "--real_time", action="store_true", dest="real_time",
                      default=False, help="Continuously update plot with incoming data [default: False]")
    parser.add_option("-l", "--log", action="store_true", dest="log",
                      default=False, help="Log the data (10log(X)) [default: False]")
    parser.add_option("-x", "--power_spectrum", action="store_true", dest="power_spectrum",
                      default=False, help="Compute the power spectrum of the data [default: False]")
    parser.add_option("-n", "--normalize", action="store_true", dest="normalize",
                      default=False, help="Normalize the data [default: False]")

    parser.add_option("-t", "--timestamp", action="store", dest="timestamp",
                      default=None, help="Timestamp to plot [default: Latest file in directory]")
    parser.add_option("-d", "--data_directory", action="store", dest="directory",
                      default="/data", help="Data directory [default: /data]")
    parser.add_option("-p", "--polarisations", action="store", dest="polarisations",
                      default="0,1", help="Polarisations to plot [default: All]")
    parser.add_option("-a", "--antennas", action="store", dest="antennas",
                      default="0:15", help="Antennas to plot [default: All]")
    parser.add_option("-c", "--channels", action="store", dest="channels",
                      default="0:511", help="Channels to plot [default: All]")
    parser.add_option("-s", "--nof_samples",action="store", dest="nof_samples",
                      type='int', default=1024, help="Number of samples to plot [default: 1024]")
    parser.add_option("-o", "--sample_offset", action="store", dest="sample_offset",
                      default=0, help="Sample offset [default: 0]")

    (conf, args) = parser.parse_args(argv[1:])

    # Set logging
    log = logging.getLogger('')
    log.setLevel(logging.DEBUG)
    format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    ch = logging.StreamHandler(stdout)
    ch.setFormatter(format)
    log.addHandler(ch)

    # Check if any mode was chosen
    if not any([conf.plot_beam_data, conf.plot_channel_data, conf.plot_raw_data]):
        logging.error("No plotting mode was set. Exiting")
        exit(0)

    # If real-time plotting is set, check that only one plotting mode is chosen
    if conf.real_time and sum([conf.plot_beam_data, conf.plot_raw_data, conf.plot_raw_data]) > 1:
        logging.error("Only one plotting mode can be chosen when real-time is enabled. Exiting")
        exit(0)

    # Check if directory exists
    if not (os.path.exists(conf.directory) and os.path.isdir(conf.directory)):
        logging.error("Specified directory (%s) does not exist or is not a directory" % conf.directory)
        exit(0)

    # Parse all string-representation parameters
    conf.antennas = extract_values(conf.antennas)
    conf.channels = extract_values(conf.channels)
    conf.polarisations = extract_values(conf.polarisations)

    # Do plots
    if conf.plot_raw_data:
        plot_raw_data()
    if conf.plot_channel_data:
        plot_channel_data()
    if conf.plot_beam_data:
        plot_beam_data()

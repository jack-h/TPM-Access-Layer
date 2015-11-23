from optparse import OptionParser
import numpy as np
import corr
import sys
import time

def set_incrementor(roach, name, inc_by, inc_every, base_cnt=2**14):
    roach.write_int(name+'_inc_by', inc_by * base_cnt/inc_every)

def set_item(roach, name, id_num, val=None):
    roach.write_int(name+'_id', id_num)
    if val is not None:
        roach.write_int(name+'_val', val)

def set_packet_rate(roach, period, payload):
    roach.write_int('pkt_sim_period', period) # in 156 MHz clocks
    roach.write_int('pkt_sim_payload_len', payload) # in 64 bit words
    print 'Packet rate: %d PPS'%(156e6/period)
    print 'Data rate: %.4f Gb/s'%(156e6/period * (payload + 52 / 8) * 64 / 1e9)

def ip_str2int(ip_str):
    dest_ip_int = 0
    for xn, x in enumerate(map(int, ip_str.split('.'))):
        dest_ip_int += (x<<((3-xn)*8))
    return dest_ip_int

def default_mode(opts):
    # Configure header properties
    print "Default mode"
    print 'Configuring headers'
    set_item(roach, 'payload_len', 0x10, opts.payload_len*8)
    set_item(roach, 'ref_time', 0x11, int(time.time()))
    set_item(roach, 'stat_tile', 0x12)
    roach.write_int('stat_tile_station', 1)
    roach.write_int('stat_tile_tile', 2)
    set_item(roach, 'time_stamp', 0x13)
    set_incrementor(roach, 'time_stamp', 1, 2**14)
    set_item(roach, 'payload_pointer', 0x14)
    set_incrementor(roach, 'payload_pointer', 0, 1)
    set_item(roach, 'ant_chan_id', 0x15)
    set_incrementor(roach, 'ant_chan_id_chan', 1, )
    set_incrementor(roach, 'ant_chan_id_ant', 1, opts.n_ants)
    roach.write_int('ant_chan_id_n_chans', opts.n_chans)
    roach.write_int('ant_chan_id_n_ants', opts.n_ants)

    # Configure test vector data
    print 'Loading TVG data'
    tvg = np.arange(2**16, dtype='>h')
    roach.write('payload_bram', tvg.tostring())

    # configure packet generation rate
    print 'Configuring packet timer'
    set_packet_rate(roach, opts.period, opts.payload_len + 8)

def debug_mode(opts):
    pass

def aavs_channel_mode(opts):
    print "AAVS Channel mode. Ignoring antenna, channel, period and payload_len options"

    sampling_freq      = 400e6
    nants              = 16
    npol               = 2
    nchan              = 1
    totchan            = 512
    samps_per_packet   = 31
    packets_per_second = 25200
    payload_len = (2 * npol * nchan * nants * samps_per_packet) / 8
    period             = (156e6/opts.data_rate) * (payload_len + 8 + 13) * 64 / 1e9

    # Configure header properties
    print 'Configuring headers'
    set_item(roach, 'payload_len', 0x10, payload_len * 8)
    set_item(roach, 'ref_time', 0x11, int(time.time()))
    set_item(roach, 'stat_tile', 0x12)
    roach.write_int('stat_tile_station', 1)
    roach.write_int('stat_tile_tile', 1)
    set_item(roach, 'time_stamp', 0x13)

    set_incrementor(roach, 'time_stamp', 1, 1)

    set_item(roach, 'payload_pointer', 0x14)
    set_incrementor(roach, 'payload_pointer', 0, 1)
    set_item(roach, 'ant_chan_id', 0x15)
    set_incrementor(roach, 'ant_chan_id_chan', 1, packets_per_second)
    set_incrementor(roach, 'ant_chan_id_ant', 1, 2**20)
    roach.write_int('ant_chan_id_n_chans', 1)
    roach.write_int('ant_chan_id_n_ants', nants)

    # Configure test vector data
    print 'Loading TVG data'
    tvg = np.arange(2**16, dtype='>h')
    roach.write('payload_bram', tvg.tostring())

    # configure packet generation rate
    print 'Configuring packet timer'
    set_packet_rate(roach, period, payload_len + 8)

BOFFILE = 'channelised_spead_sim_2015_Aug_31_1729.bof'

if __name__ == "__main__":

    p = OptionParser()
    p.set_usage('script.py <ROACH_HOSTNAME_or_IP> [options]')
    p.set_description(__doc__)
    p.add_option('-p', '--noprogram', dest='noprogram', action='store_true',
                 help='Don\'t program the FPGA.')
    p.add_option('-b', '--boffile', dest='boffile', type='str', default=BOFFILE,
                 help='Specify the bof file to load')
    p.add_option('-c', '--chans', dest='n_chans', type='int', default=1024,
                 help='Number of channels. Default:1024')
    p.add_option('-a', '--ants', dest='n_ants', type='int', default=16,
                 help='Number of antennas. Default:16')
    p.add_option('-i', '--dest_ip', dest='dest_ip', type='str', default='10.0.0.10',
                 help='Destination IP. Default: 10.0.0.10')
    p.add_option('-P', '--port', dest='dest_port', type='int', default=10000,
                 help='Destination port. Default: 10000')
    p.add_option('-l', '--payload_len', dest='payload_len', type='int', default=64,
                 help='Payload length in 64 bit words. Default: 64')
    p.add_option('-t', '--period', dest='period', type='int', default=1000000,
                 help='Period of packet transmission in 156MHz clock cycles. Default: 1000000')
    p.add_option('-r', '--data_rate', dest='data_rate', type='float', default=9.9,
                 help="Desired output data rate in Gb/s. Default: 9.9 Gb/s")
    p.add_option('-m', '--mode', dest='mode', type='str', default='default',
                 help='Select operational mode. Available: [debug, aavs_channel]')
    opts, args = p.parse_args(sys.argv[1:])

    if not args:
        print 'Please specify a ROACH board. \nExiting.'
        exit()
    else:
        print 'Connecting to roach', args[0]
        roach = corr.katcp_wrapper.FpgaClient(args[0])
    time.sleep(0.1)

    if not opts.noprogram:
        print 'Programming with', opts.boffile
        roach.progdev(opts.boffile)
    time.sleep(0.1)

    # Configure tge core
    print 'Configuring 10gbe core'
    roach.write_int('dest_ip', ip_str2int(opts.dest_ip))
    roach.write_int('port', opts.dest_port)
    roach.config_10gbe_core('ten_Gbe_v2', 0x001122334455, ip_str2int('10.0.0.100'), opts.dest_port, [0xffffffffffff]*256) #broadcast all packetsS

    # Select operational mode
    if opts.mode == 'default':
        default_mode(opts)
    elif opts.mode == 'debug':
        debug_mode(opts)
    elif opts.mode == 'aavs_channel':
        aavs_channel_mode(opts)

    # reset everything
    print 'resetting'
    roach.write_int('pkt_sim_enable', 0)
    roach.write_int('rst', 3)
    roach.write_int('rst', 0)
    roach.write_int('pkt_sim_enable', 1)

    while True:
        print 'Packets sent: %d'%roach.read_int('eof_cnt')
        time.sleep(1)

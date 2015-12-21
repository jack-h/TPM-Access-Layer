# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2013
# ASTRON (Netherlands Institute for Radio Astronomy) <http://www.astron.nl/>
# P.O.Box 2, 7990 AA Dwingeloo, The Netherlands
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

""" script for Stati functions
"""
###############################################################################

# In this script the basic statistics plottting / displaying functions are described. 
# This file is used wit apertif_beamformer.py

# System imports

import array
import numpy as np
import scipy as sp
import scipy.io as spio

import pylab as pl

#import unb_hw as unb
#from tools import *
#import unb_apertif as apr
#from eth_udp_diag import *
from pyfabil.base.utils import *


class statiConfiguration:

    def __init__(self, fft_size = 1024, nof_wb_ffts = 2, bsn_period = 1.0*1024/800000000, blocks_per_sync = 781250, stati_input_bits = 16,\
                       wb_factor = 4, nof_bf_units = 4):
        self.c_fft_size                 = fft_size
        self.c_nof_wb_ffts              = nof_wb_ffts
        self.c_bsn_period               = bsn_period
        self.c_blocks_per_sync          = blocks_per_sync
        self.c_stati_input_bits         = stati_input_bits
        self.c_wb_factor                = wb_factor
        self.c_nof_bf_units             = nof_bf_units

class Stati_functions:

  def __init__(self, st_conf):
        self.st_conf = st_conf
        self.c_sync_interval = st_conf.c_blocks_per_sync*st_conf.c_bsn_period
        self.si_data = array.array('b')
        self.si_label=[]
        self.si_nr=[]
        self.rd_data=[]
        self.fdata = []
        self.sum_fdata = []
#        self.f_as = []
        self.nof_fpoints = []
        self.nof_channels=[]
        self.nof_samples=[]
        self.nof_data_words=[]
        self.ddr_data=[]
        self.data_type=[]
        self.bits=8
        self.fs=800
        self.sub_stati=[]
        self.db_sub_stati=[]
        self.bl_st=[]
        self.bl_data=[]
        self.ol_data=[]
        self.ol_fdata = []
        #self.cor_phase_data =[]
        self.cor_product =[]
        self.cor_x_data=[]
        #self.cor_amplitude_data=[]
        self.x_label=[]
        self.xcor_label=[]
        self.FFT_stati_gain=-18
        f_as = []
     #   for k in range(apr.c_fft_size/2):
     #       f_as.append(float(k*400)/(apr.c_fft_size/2));
        self.sb_fas = f_as
        self.show_figs = 1
        self.pl_sb_data=[]
        self.pl_bl_data=[]



# Functions fot translating samples
  def raw_snap_shot_capture(self, tc, mon, monPeriod=16, monNofWords=256, vlevel=5, store_data='no', file_number=1):
        #
        # Function to calculate the spectrum from the raw ADC samples
        #
        # monPeriod   : ADC 750 MHz input sinus aliases to 50 MHz so period of 16 samples @ 800 MSps
        # monNofWords : Maximum is mon[0].c_ram_sz = 256 words to fit 1024 samples
        #
        if store_data != 'yes':
            for sp in tc.spNrs:
                mon[sp].overwrite_buffer()
            tc.sleep(1)
        # Read the ADU handler SP monitor buffers that got captured at the sync period
        rd_data_sp_oriented=[]
        rd_data=[]
        for sp in tc.spNrs:
            rd_data.append(mon[sp].read_buffer(monPeriod, monNofWords, vLevel=6))
        self.rd_data=rd_data
        if store_data == 'yes':
            self.words_2_samples(tc)
            file_name = 'Capture_' + str(file_number) + '.mat'
            spio.savemat(file_name, {'si_label':self.si_label, 'raw_data':self.si_data}, appendmat=False)
#            spio.savemat(file_name, {'raw_data':rd_data}, appendmat=False)
            for sp in tc.spNrs:
                mon[sp].overwrite_buffer()



  def words_2_samples(self, tc, data_type='cap'):
          #
          # The rd_data contains a list of lists of ADUH SP monitor buffer data.
          # Default all 4 local SP are used and then the 2-dim rd_data contains:
          #   [[buffer data of A=SP0 for all BN in the test],
          #    [buffer data of B=SP1 for all BN in the test],
          #    [buffer data of C=SP2 for all BN in the test],
          #    [buffer data of D=SP3 for all BN in the test]]
          # The actual BN in the test are specified via tc.nodeBnIndices
          # The actual SP in the test that were read for each BN are specified via tc.spNrs
          # The order of the SP signal paths in the 2-dim rd_data is [tc.spNrs][tc.nodeBnIndices]
          # First reorder the 2-dim rd_data into a 1-dim data list of incrementing channel numbers
          #
          data=[]
          si_label=[]
          si_nr=[]
          if data_type=='ddr':
            data = self.ddr_data
            for channel_nr in range(len(data)):
              label = 'SI '+ str(channel_nr)
              si_label.append(label)
              si_nr.append(channel_nr)
              self.data_type='DDR3'
          else:
            rd_data=self.rd_data
            for bi in range(tc.nofBnNodes):
              bn = tc.nodeBnIndices[bi]
              for si in range(tc.nofSp):
                sp = tc.spNrs[si]
                channel_nr = bn*unb.c_nof_sp+sp
                data.append(rd_data[si][bi][:])
                label = 'SI '+ str(channel_nr)
                si_label.append(label)
                si_nr.append(channel_nr)
            self.data_type='Capture'
          self.nof_channels=len(data)
          # Continue with the 1-dim data list
          ch_samples=[]
          data_words=[]
          adcHalf = 2**(self.bits-1)
          adcNorm = 2**self.bits
          adcMask = adcNorm-1
          for channel_cnt in range(self.nof_channels):
            ch_samples=[]
            for word_cnt in range(len(data[0])):
              sample_word = data[channel_cnt][word_cnt]
              conv_sample = (sample_word >> 24) & adcMask
              if conv_sample >= adcHalf:
                conv_sample = conv_sample - adcNorm
              ch_samples.append(conv_sample)
              conv_sample = (sample_word >> 16) & adcMask
              if conv_sample >= adcHalf:
                conv_sample = conv_sample - adcNorm
              ch_samples.append(conv_sample)
              conv_sample = (sample_word >> 8) & adcMask
              if conv_sample >= adcHalf:
                conv_sample = conv_sample - adcNorm
              ch_samples.append(conv_sample)
              conv_sample = (sample_word >> 0) & adcMask
              if conv_sample >= adcHalf:
                conv_sample = conv_sample - adcNorm
              ch_samples.append(conv_sample)
            data_words.append(ch_samples)
          self.si_label=si_label
          self.si_nr=si_nr
          self.nof_data_words=word_cnt+1
          self.si_data=data_words

  def pwr_time_domain(self, remove_dc=False):
          """
              calculate the RMS power
          """
          data = np.array(self.si_data)
          bits  = self.bits
          if remove_dc:
              data = data-transpose([np.mean(data,axis=1)]*1024)
          ms_data = (np.sum(data*data,axis=1))/len(data[0])+10**-3
          pwr_data = 10*sp.log10(ms_data)-20*sp.log10(2**(self.bits-1))+3 # +3 dB for CW p-p to effective is srtq(2) of 3dB
          return list(pwr_data)

  def fft_data(self, data_window = 'no'):
          #
          # Function to calculate the spectrum from the raw ADC samples
          # data_window can be used to add hanning window, remove FFT leakage
          #
          data = self.si_data
          self_fdata=[]
          data_length = len(data[0])
          if data_window == 'yes' :
            window = np.hanning(data_length)
          else:
            window = np.ones(data_length)
          for cnt in range(len(data)):
            f_points = data_length
            fdata = sp.fft(data[cnt]*window)/(2**(self.bits-1)*data_length)
            fdata = np.fft.fftshift(fdata)
            fas=np.array(range(f_points),'float')
            f_as=(fas*self.fs)/f_points
            f_as = f_as - self.fs/2
            self_fdata.append(fdata)
            self.f_as=f_as
            self.nof_fpoints = f_points
          self.fdata = self_fdata

  # FUNCTIONS FOR PLOTTING DATA

  def plot_time_freq(self, figs='one', xas ='freq_z2', lim_axis='on', plot_Str='time_frequency', fig_nr=1, pl_legend='on', window='no', avg_on = 'yes'):
          #
          # Function to plot the time domain data of the signal input.
          #
          # figs options:
          # multi         -> plot all signal input in separate figure
          # one           -> plot all signal inputs in one figure
          #
          # plot_Str options:
          # time          -> plot only time domain data
          # frequency     -> plot only frequency domain datat
          # tim_frequency -> plot both
          # xas options:
          # - freq            --> down sampled frequency number
          # - freq_z2         --> frequency number in zone 2
          #

          data = self.si_data
          data_label=self.si_label
          if (plot_Str=='time_frequency') | (plot_Str=='frequency'):
            self.fft_data(window)
            f_as = self.f_as
            fdata = self.fdata
          f_points = self.nof_fpoints
          if self.show_figs == 1:
            pl.figure(fig_nr)
            pl.clf()
          channel_order = np.argsort(self.si_nr)
          for sp_cnt in range(len(data)):
            ch_index = channel_order[sp_cnt]
            if figs == 'one' and self.show_figs == 1:
              pl.figure(fig_nr)
            elif self.show_figs == 1:
              pl.figure(ch_index)
            if plot_Str=='time_frequency':
              subp_h = pl.subplot(211)
            if (plot_Str=='time_frequency') | (plot_Str=='time'):
              pl.plot(data[ch_index], label=data_label[ch_index])
              pl.grid(True)
              pl.xlabel('time (sample nr) (only first 16 are plotted) ')
              pl.ylabel('LSB ')
              pl.ylim([-(2**7)-10, (2**7)+10])
              pl.xlim([0, 16])
            if figs == 'one' :
              if pl_legend =='on':
                pl.legend()
              title_string = self.data_type
            else:
              title_string = data_label[ch_index] + ' '
            if window=='yes':
              title_string = title_string + ' Hanning window used'
            pl.title(title_string )
            if plot_Str=='time_frequency' :
              pl.subplot(212)
            if (plot_Str=='time_frequency') | (plot_Str=='frequency'):
              xdata_base = f_as[f_points/2:]
              xdata=[]
              if (xas=='freq_z2'):
                xlabel = 'Frequency Zone 2 (MHz)'
                for x_point_cnt in range(len(xdata_base)):
                  xdata.append(self.fs-xdata_base[x_point_cnt])
              else:
                xlabel = 'Down Sampled Frequency (MHz)'
                for x_point_cnt in range(len(xdata_base)):
                  xdata.append(xdata_base[x_point_cnt])

              pw_fdata = fdata[ch_index] * np.conj(fdata[ch_index])
              if avg_on == 'yes':
                temp= np.shape(self.sum_fdata)
                if temp[0] > 1:
                  pw_fdata = np.add(self.sum_fdata, pw_fdata)
                  self.sum_fdata = pw_fdata

              db_fdata = 10*sp.log10(np.abs(pw_fdata+10**-9))+6
              pl.plot(xdata, db_fdata[f_points/2:], label=data_label[ch_index])
              freq_ylabel = 'Power (dBFS)'
              pl.ylabel(freq_ylabel)
              pl.xlabel(xlabel )
              if (figs == 'one') & (pl_legend =='on'):
                pl.legend()
              pl.grid(True)
              if lim_axis=='on':
                pl.ylim([-90, 0])
            #file_name = 'time_freq_' + str(data_label[ch_index]) + '.png'
            #pl.savefig(file_name)
          if self.show_figs == 1:
            pl.draw()
          self.dump_data(fdata, xdata, x_label=xlabel, y_label=freq_ylabel, title=plot_Str, filename = 'Plot_data_dump.txt')
          self.dump_data(data, range(1024), x_label='sample', y_label='level', title='Capture', filename = 'Cap_data_dump.txt')

  def plot_histogram(self, fig_nr=1, pl_legend='off', nof_signal_inputs=8, bits=8):
          data = self.si_data
          x_label='LSB'
          y_label='Number of Occurrences'
          title= 'Histogram'
          if nof_signal_inputs > len(data):
            nof_signal_inputs = len(data)
          pl.figure(fig_nr)
          pl.clf()
          for cnt in range(nof_signal_inputs):
            hist_data, hist_xas = np.histogram(data[cnt][:],bins=2**bits, range=(-128.5, 127.5))
            label_stri = 'SI ' + str(cnt)
            pl.plot(hist_xas[:-1], hist_data, label=label_stri)
          pl.grid(True)
          pl.xlabel(x_label)
          pl.ylabel(y_label)
          pl.xlim([-(2**bits/2),(2**bits/2)])
          pl.title(title)
          if pl_legend=='on':
            pl.legend()


  def plot_init(self):
          if self.show_figs ==  1:
            pl.ion()

  def plot_last(self):
          if self.show_figs ==  1:
            pl.ioff()
            pl.show()

  def close_figs(self, tc):
          if self.show_figs ==  1:
            pl.ion()
            tc.append_log(3, 'CLOSE all figures')
            pl.show()

  def show_figs_disabled(self, tc):
          self.show_figs = 0
          tc.append_log(3, 'Figures won\'t be shown on screen')


  def print_stati(self, tc, input_type ='cap', vlevel=0):
          #
          # Function for printing status information of ADU inputs.
          # Data captured with "words_2_samples"
          #
          if input_type == 'udp':
              data = np.real(self.ol_data[0])
              bits  = 16
              si_nr = range(len(data))
              si_label = ['BL  ' + str(i) for i in si_nr]
          else:
              data = self.si_data
              bits  = self.bits
              si_nr = self.si_nr
              si_label = self.si_label
          max_data=[]
          min_data=[]
          avg_data=[]
          pwr_data=[]
          range_data=[]
          range_bits=[]
          nof_samples = len(data[0])

          LSB_FS = 20*sp.log10(2**(bits-1))

          for cnt in range(len(data)):
            max_data.append(max(data[cnt]))
            min_data.append(min(data[cnt]))
            avg_data.append(np.mean(data[cnt]))

            pwr=0
            for smp_cnt in range(nof_samples):
              pwr += data[cnt][smp_cnt]**2
            db_pwr = 10*sp.log10(pwr/nof_samples)+3 # +3 dB for CW p-p to effective is srtq(2) of 3dB
            pwr_data.append(db_pwr-LSB_FS)
            #max_lsb = (max_data[cnt] - min_data[cnt])/2           # range without DC offset
            max_lsb = np.max([abs(max_data[cnt]), abs(min_data[cnt])])    # Range with DC offset, +xdB to make Full Scale
            range_lsb = float(max_lsb) / 2**(self.bits-1)
            range_data.append(20*sp.log10(range_lsb))
            range_bits.append(sp.log10(max_data[cnt]-min_data[cnt])/sp.log10(2))


          si_order = np.argsort(si_nr)
          tc.append_log(vlevel, ' ')
          tc.append_log(vlevel, '|-----------------------------------------------------------------------------------|')
          if input_type =='ddr':
              tc.append_log(vlevel, '| DDR Range information                                                             |')
          else:
              tc.append_log(vlevel, '| Capture Range information                                                         |')
          tc.append_log(vlevel, '|-----------------------------------------------------------------------------------|')
          tc.append_log(vlevel, '| SI   | MAX (LSB) | MIN (LSB) | AVG (LSB) | PWR (dBFS) |Range (dBFS)| Range (bits) |')
          tc.append_log(vlevel, '|------|-----------|-----------|-----------|------------|------------|--------------|')

          for cnt in range(len(data)):
            si_index = si_order[cnt]
            stri = '| ' + "%4i" %int(si_label[si_index][2:]) + ' |   '
            stri = stri + "%4i" %max_data[si_index] + '    |   '
            stri = stri + "%4i" %min_data[si_index] + '    |   '
            stri = stri + "%4.2f" %avg_data[si_index] + '   |    '
            stri = stri + "%3.2f" %pwr_data[si_index] + '  |   '
            stri = stri + "%3.2f" %range_data[si_index] + '   | '
            stri = stri + "  %3.2f" %range_bits[si_index] + '       |'
            tc.append_log(vlevel, stri)
          tc.append_log(vlevel, '|-----------------------------------------------------------------------------------|')
          tc.append_log(vlevel, ' ')

  def print_bit_stati(self, tc, input_type ='cap', vlevel=3):
          #
          # Function for printing bit information of ADU inputs.
          #
          if input_type == 'udp':
              data = np.real(self.ol_data[0])
              bits  = 16
              si_nr = range(24) #len(data))
              si_label = ['BL  ' + str(i) for i in si_nr]
          else:
              data = self.si_data
              bits  = self.bits
              si_nr = self.si_nr
              si_label = self.si_label
          max_data=[]
          bit=[]
          ret_bits=[]
          nof_samples=len(data[0])
          tc.append_log(vlevel, ' ')
          tc.append_log(vlevel, '|-------------------------------------------------------------------------------|')
          if input_type =='ddr':
            tc.append_log(vlevel, '| DDR Bit information                                                           |')
          elif input_type =='udp':
            tc.append_log(vlevel, '| UDP Bit information (only real part)                                          |')
          else:
            tc.append_log(vlevel,'| Capture Bit toggling information                                              |')
          tc.append_log(vlevel, '|-------------------------------------------------------------------------------|')
          tc.append_log(vlevel, '| SI    | bit 0 | bit 1 | bit 2 | bit 3 | bit 4 | bit 5 | bit 6 | bit 7 | STATI | ')
          tc.append_log(vlevel, '|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|')
          si_order = np.argsort(si_nr)

          for cnt in range(len(data)):
            si_index = si_order[cnt]
            bit = self.bits*[0]
            #bit=[]
            #for bit_cnt in range(self.bits):
              #bit.append(0)
            for smp_cnt in range(len(data[0])):
              bin_data = bin(int(data[si_index][smp_cnt])+2**(self.bits-1))
              for bit_cnt in range(len(bin_data)-2):
                if bin_data[-(bit_cnt+1)]=='1':
                  bit[bit_cnt] +=1
            stri = '| ' + "%4i" %int(si_label[si_index][2:]) + '  |  '
            #stri = '| ' + si_label[si_index] + ' | '
            bits_ok ='  OK '
            for bit_cnt in range(len(bit)):
              stri = stri + "%4i" %bit[bit_cnt] + ' |  '
              if (bit[bit_cnt] < (nof_samples*0.30) ) | (bit[bit_cnt] > (nof_samples*0.7) ):
                bits_ok = ' NOK '
            stri = stri + bits_ok + '| '
            tc.append_log(vlevel, stri)
            ret_bits.append([(i*100)/len(data[0]) for i in bit]) # normalize return value to %
          tc.append_log(vlevel,'|-------------------------------------------------------------------------------|')
          tc.append_log(vlevel, ' ')
          return ret_bits


  def DDR_take_snap(self, tc, nof_blocks, bsSrc, dc, bsSpOn, bsSpOff, c_bsn_latency_1s):
    c_bsn_latency = c_bsn_latency_1s*4

    # [DS]: disable signal path so we can re-enable it at a certain BSN
    # [DS]: disable signal path so we can re-enable it at a certain BSN
    bsnNow = bsSrc.read_current_bsn()[tc.nofBnNodes-1]
    print bsnNow
    bsnSpOff = bsnNow + 2048
    bsSpOff.write_scheduled_bsn(bsnSpOff)
    bsnNow = bsSrc.read_current_bsn()[tc.nofBnNodes-1]
    bsnDiff = bsnSpOff - bsnNow
    if bsnDiff > 0:
        tc.append_log(3, 'SP disable scheduled in time (%d > 0)' % bsnDiff)
    else:
        tc.append_log(3, 'SP disable scheduled too late (%d < 0)' % bsnDiff)
        tc.set_result('FAILED')
    tc.append_log(3, '')

    # [DS]: Enable signal path after a pretty long delay: we want the DDR3 modules to be prepared first.
    bsnNow = bsSrc.read_current_bsn()[tc.nofBnNodes-1]
    bsnSpOn = bsnNow + c_bsn_latency
    bsSpOn.write_scheduled_bsn(bsnSpOn)
    bsnNow = bsSrc.read_current_bsn()[tc.nofBnNodes-1]
    bsnDiff = bsnSpOn - bsnNow
    if bsnDiff > 0:
        tc.append_log(3, 'SP enable scheduled in time (%d > 0)' % bsnDiff)
    else:
        tc.append_log(3, 'SP enable scheduled too late (%d < 0)' % bsnDiff)
        tc.set_result('FAILED')
    tc.append_log(3, '')

    # [DS]: Send the store_blocks command. The signal path should not be enabled yet (hence the long BSN delay). The DDR3 modules will
    #       simply wait until the signal path is enabled and trigger a write sequence when the first block comes in.
    dc.store_blocks(2*nof_blocks)

  def import_samples(self, nof_blocks, dc):
    rd_data=[]
    x_data=[]
    y_data=[[]]
    for cnt in range(nof_blocks):
      ddr_data = []
      ddr_data.append(dc.pop_blocks(1))
      for node_cnt in range(len(ddr_data[0])):
        if cnt == 0:
          x_data.append([])
        x_data[node_cnt].extend(ddr_data[0][node_cnt])
      ddr_data = []
      ddr_data.extend([dc.pop_blocks(1)])
      for node_cnt in range(len(ddr_data[0])):
        if cnt == 0:
          y_data.append([])
        y_data[node_cnt].extend(ddr_data[0][node_cnt])

    for cnt in range(len(x_data)):
      rd_data.append(x_data[cnt])
      rd_data.append(y_data[cnt])
    self.ddr_data=rd_data

  def subband_stati_capture(self, st, store_data='no', calc_dB='yes', file_number=1):
    #
    # Function that reads the subband statistics from the statistics unit
    # that is placed directly after the wideband poly phase filter. This
    # function reads the data and reorders it to compensate for the
    # alternating output format of the poly phase filter.
    #
    # It returns the statistics in two lists:
    #
    #    sub_stati[SI][SB]    = "real" data values
    #    db_sub_stati[SI][SB] = normalized data values
    #
    #    Where SI = Signal Input number
    #          SB = Subband number
    #
    #    The return values are also stored in attributes of this class in
    #    order to be used in plot functions.


    print 'Read Subband Statistics Samples'
    nofBnNodes = 4
    nodeBnIndices = range(4,8)
    nofSp = 4
    spNrs = range(4)

    norm_dB=0
    si_label=[]
    si_nr=[]
    data = []
    sub_stati=[]
    db_sub_stati=[]
    for k in range(self.st_conf.c_nof_wb_ffts):
        for l in range(self.st_conf.c_wb_factor):
            data.append(np.abs(st[k*self.st_conf.c_wb_factor + l].read_stats(5)))

    for input_cnt in range( len(data[0])):
        spectrum1 = []
        spectrum2 = []
        spectrum3 = []
        spectrum4 = []
        for k in range(self.st_conf.c_wb_factor):
            for l in range(self.st_conf.c_fft_size/(2*self.st_conf.c_wb_factor)):
                spectrum1.append(float(data[k][input_cnt][2*l])); # +1 for Log10
                spectrum2.append(float(data[k][input_cnt][2*l+1]));
                spectrum3.append(float(data[self.st_conf.c_wb_factor+k][input_cnt][2*l]));
                spectrum4.append(float(data[self.st_conf.c_wb_factor+k][input_cnt][2*l+1]));

        sub_stati.append(spectrum1)
        sub_stati.append(spectrum2)
        sub_stati.append(spectrum3)
        sub_stati.append(spectrum4)


    if calc_dB == 'yes':
        for bi in range(nofBnNodes):
            bn = nodeBnIndices[bi]
            for si in range(nofSp):
                sp = spNrs[si]
                channel_nr = bn*16+sp
                label = 'SI'+ str(channel_nr)
                si_label.append(label)
                si_nr.append(channel_nr)
                input_cnt = bi*4+sp
                db_sub_stati_single=[]
                for k in range(self.st_conf.c_wb_factor*self.st_conf.c_fft_size/8):
                    db_sub_stati_single.append(10*math.log10(sub_stati[input_cnt][k]+1)-norm_dB)
                db_sub_stati.append(db_sub_stati_single)


    f_as = []
    for k in range(self.st_conf.c_fft_size/2):
        f_as.append(float(k*400)/(self.st_conf.c_fft_size/2));
    self.sb_fas = f_as

    self.sub_stati = sub_stati
    self.si_label=si_label
    self.si_nr=si_nr
    self.db_sub_stati = db_sub_stati
    if store_data == 'yes':
        file_name = 'SubStati_' + str(file_number) + '.mat'
        spio.savemat(file_name, {'sub_stati':sub_stati, 'si_nr': si_nr, 'fas': f_as}, appendmat=False)

    print 'Subband Statistics Samples taken and reordered'

    return (sub_stati, db_sub_stati)

  def plot_subband_stati(self, figs='one', lim_axis='on', bck_fft='off', norm='dB', fig_nr=1, xas='freq_z2', pl_legend='on', file_type = 'txt', file_number=1):
          #
          # Function plotting the subband statistics
          #
          # figs options:
          # one         --> All signal input in single plot
          #
          # Lim_axis >> limits the Y-axis
          # back_fft >> add subplot with the auto correlation function (back FFT)
          # fig_nr   >> number of the figure
          # xas options:
          # - bin             --> frequency channel number
          # - freq            --> down sampled frequency number
          # - freq_z2         --> frequency number in zone 2
          #
          # pl_legend  options
          # 'on'  --> plot legend in figure
          # other --> no legend, can be handy.. legend block part of the plot
          #
          # norm options
          # 'dB'  --> dB scale
          # 'raw' --> raw subband data
          # 'sqrt'--> linear data
          #

          clim_min = -90 #-1*(self.bits*6+10*np.log10(apr.c_fft_size/2)+10)

          # Select the data format
          if norm =='dB':
            stri_ylabel = 'Power (dB)'
            pl_sub_stati = self.db_sub_stati
          elif norm =='dBFS':
            stri_ylabel = 'Power (dB)' #FS)'
            pl_sub_stati=[]
            for c_cnt in range(len(self.db_sub_stati)):
              pl_sub_stati_si=[]
              for r_cnt in range(len(self.db_sub_stati[0])):
                pl_sub_stati_si.append(self.db_sub_stati[c_cnt][r_cnt] - self.FFT_stati_gain)
              pl_sub_stati.append(pl_sub_stati_si)
          elif norm == 'sqrt':
            stri_ylabel = 'Power A'
            pl_sub_stati = []
            for row_cnt in range(len(self.sub_stati)):
              single_sub_stati=[]
              for col_cnt in range(len(self.sub_stati[0])):
                single_sub_stati.append(np.sqrt(self.sub_stati[row_cnt][col_cnt]/self.st_conf.c_blocks_per_sync))
              pl_sub_stati.append(single_sub_stati)
          else:
            pl_sub_stati = self.sub_stati
            stri_ylabel = 'Power A^2'

          if figs=='one' and self.show_figs == 1:
            pl.figure(fig_nr)
            pl.clf()

          channel_order = np.argsort(self.si_nr)
          for pl_cnt in range(len(pl_sub_stati)):
            channel_index = channel_order[pl_cnt]
            if figs=='multi' and self.show_figs == 1:
              pl.figure(channel_index)
              pl.clf()
            if bck_fft=='on':
              ifftdata=[]
              fftdata=[]
              for smp_cntb in range(len(self.sub_stati[pl_cnt])):
                fftdata.append(self.sub_stati[pl_cnt][smp_cntb]/self.st_conf.c_blocks_per_sync)
              for smp_cnt in range(len(self.sub_stati[pl_cnt])):
                index = len(self.sub_stati[pl_cnt])-smp_cnt-1
                fftdata.append(self.sub_stati[pl_cnt][index]/self.st_conf.c_blocks_per_sync)
              ifftdata = sp.fft(fftdata)/self.st_conf.c_fft_size
              ifftdata = np.fft.fftshift(ifftdata)
              if self.show_figs == 1:
                pl.subplot(211)
            if xas=='freq':
              xdata = self.sb_fas
              xlabel = 'Down Sampled Frequency (MHz)'
              if self.show_figs == 1:
                pl.plot(xdata, pl_sub_stati[channel_index], label=self.si_label[channel_index] )
            elif xas=='freq_z2':
              xdata = []
              for xdata_cnt in range(len(self.sb_fas)):
                xdata.append(self.fs-self.sb_fas[xdata_cnt])
              xlabel = 'Frequency Zone 2 (MHz)'
              if self.show_figs == 1:
                pl.plot(xdata, pl_sub_stati[channel_index], label=self.si_label[channel_index] )
            else:
              xlabel = 'Subband nr'
              if self.show_figs == 1:
                pl.plot(pl_sub_stati[channel_index], label=self.si_label[channel_index] )
                pl.xlim([0, self.st_conf.c_fft_size/2])
            if self.show_figs == 1:
              pl.grid(True)
              pl.xlabel(xlabel)
              pl.ylabel(stri_ylabel)
            if lim_axis=='on' and self.show_figs == 1:
              pl.ylim([clim_min, 0])
            if figs=='one':
              stri = 'Subband Statistics'
            else:
              stri = 'Subband statistics input ' + str(channel_index)
            if self.show_figs == 1:
              pl.title(stri)
            if (figs=='one') & (pl_legend=='on') & (self.show_figs == 1):
              pl.legend()
            if (bck_fft=='on') & (self.show_figs == 1):
              pl.subplot(212)
              pl.plot(ifftdata, label=self.si_label[channel_index] )
              pl.grid(True)
              pl.xlabel('Time samples')
              pl.ylabel('Amplitude [?]')
              pl.xlim([0, self.st_conf.c_fft_size])
              if figs=='one':
                stri = 'AUTO Correlation Function '
              else:
                stri = 'Auto Correlation Function ' + str(channel_index)
              pl.title(stri)
              if figs=='one':
                pl.legend()
          if self.show_figs == 1:
            pl.draw()
          self.pl_sb_data = pl_sub_stati
          # if file_type == 'txt':
          #         self.dump_data(self.sub_stati, xdata, x_label=xlabel, y_label='Power (dB) ', title=stri, filename = 'Sub_stati_dump.txt')


  def ssse(self, tc, vlevel=3, input_type='stati',harms = 7):
          snr_ret=[]
          if (input_type =='cap') | (input_type =='ddr'):
            self.fft_data(data_window = 'no')
            cap_fdata = self.fdata
            fdata=[]
            for ch_index in range(len(cap_fdata)):
              row_data=[]
              freq_start = len(cap_fdata[ch_index])/2
              row_fdata = cap_fdata[ch_index] * np.conj(cap_fdata[ch_index])
              fdata.append(np.abs(row_fdata[freq_start:]))
            f_points = len(fdata[0])
          elif input_type =='udp':
            fdata = self.ol_fdata
            f_points = (apr.c_fft_size/2)+len(fdata[0])
          else:
            fdata = self.sub_stati
            f_points = len(fdata[0])
          collar_size_first= 20
          #stri = 'Removed harmonics : ' + str(harms) + ' margin fundamental ' + str(collar_size_first)
          #tc.append_log(vlevel, stri)
          tc.append_log(vlevel, ' ')
          tc.append_log(vlevel,   '|------------------------------------------------|')
          if input_type =='cap':
            tc.append_log(vlevel, '| Capture input CW signal quality                |')
          elif input_type =='ddr':
            tc.append_log(vlevel, '| DDR input CW signal quality                    |')
          elif input_type =='udp':
            tc.append_log(vlevel, '| UDP offload CW signal quality                  |')
          else:
            tc.append_log(vlevel, '| Subband Stati CW signal quality                |')
          tc.append_log(vlevel, '|------------------------------------------------|')
          tc.append_log(vlevel, '| SI    |  SNR  | SINAD | SFDR  |Median | ENOB   | ')
          tc.append_log(vlevel, '|       | (dB)  | (dB)  | (dBc) | (dBc) | (bit)  | ')
          tc.append_log(vlevel, '|-------|-------|-------|-------|-------|--------|')

          for cnt in range(len(fdata)):
            freq_start = 1
            ref_fr_data = fdata[cnt][freq_start:]
            med_ref_fr_data = np.median(ref_fr_data)
            fr_data = ref_fr_data
            med_ref_fr_data = np.median(fr_data)
            p_harm=[]
            for harm_cnt in range(harms):
              if harm_cnt < 1:
                collar_size=collar_size_first
              else :
                collar_size=1
              ind = np.argmax(fr_data[:-collar_size])
              p_harm.append(sum(fr_data[ind-collar_size:ind+collar_size])+10**-12) # add small number for 10Log10
              for fill_cnt in range(-collar_size,collar_size):
                fr_data[ind+fill_cnt]= (med_ref_fr_data)
            stri=""
            sinad = 10*sp.log10(abs(p_harm[0]/(sum(p_harm[1:])+abs(sum(fr_data)))))
            snr = 10*sp.log10(abs(p_harm[0]/abs(sum(fr_data)+10**-20)))
            sfdr = 10*sp.log10(abs(p_harm[0]/p_harm[1]))
            media = 10*sp.log10(abs(med_ref_fr_data))
            enob = (sinad-1.76)/6.02
            stri = '|   ' + "%2d" %cnt + '  | ' + "%2.2f" %snr + ' | ' + "%2.2f" %sinad + ' | ' + "%2.2f" %sfdr + ' | ' + "%2.2f" %media + ' | '+ "%2.2f" %enob + '  |'
            snr_ret.append(snr)
            tc.append_log(vlevel, stri)
          tc.append_log(vlevel, '|-------|-------|-------|-------|-------|--------|')
          tc.append_log(vlevel, ' ')
          return snr_ret


  def plot_subband_color(self, tc, fig_nr=1, xas='freq'):
          #
          # Function plotting the subband statistics
          #
          # fig_nr   >> number of the figure
          # xas options
          # - freq      --> normal first nyquist axis
          # - freq_z2   --> freqeuncies for second nyquist zone
          # - bin       --> bin.
          #
          db_sub_stati = self.db_sub_stati
          si_nr= self.si_nr
          clim_min = -1*(self.bits*6+10*np.log10(apr.c_fft_size/2)+10)
          channels = np.max(si_nr) - np.min(si_nr)+2 # +1 don't mis last +1 plot last... bug
          data_matrix = np.ones((channels, apr.c_fft_size))
          ch_index=0

          for ch_cnt in range(channels):
            if ((ch_cnt+np.min(si_nr)) in si_nr):
              for samp_cnt in range(apr.c_fft_size/2):
                  data_matrix[ch_cnt][samp_cnt]=db_sub_stati[ch_index][samp_cnt]
              ch_index +=1
            else:
              for samp_cnt in range(apr.c_fft_size/2):
                  data_matrix[ch_cnt][samp_cnt]= -9999

          y_data = np.arange(np.min(si_nr),np.min(si_nr)+channels)

          if xas=='freq_z2':
            xdata = []
            for ydata_cnt in range(len(self.sb_fas)):
              xdata.append(self.fs-self.sb_fas[ydata_cnt])
            x_data = np.array(xdata)
            xlabel = 'Frequency Zone 2 (MHz)'
          elif xas=='freq':
            xlabel = 'Down Sampled Frequency (MHz)'
            x_data = np.array(self.sb_fas)
          else:
            xlabel = 'Frequency bin'
            x_data = np.array(range(apr.c_fft_size/2))

          if self.show_figs == 1:
            pl.figure(fig_nr)
            pl.clf()
          pl.pcolormesh(x_data, np.array(y_data), np.array(data_matrix))
          cbar = pl.colorbar()
          cbar.set_label('Output power dB')
          #pl.clim([clim_min, 10])
          pl.ylim([np.min(si_nr), np.max(si_nr)])
          pl.ylabel('Input number')
          pl.xlabel(xlabel)
          if channels-1 > len(si_nr):
            title_stri = 'Subband Statistics MIND THE GAP !'
          else:
            title_stri = 'Subband Statistics'

          pl.title(title_stri)
          if self.show_figs == 1:
            pl.draw()

  def beamlet_stati_capture(self, st, skip_wait='yes', store_data='no', file_number=1 , iblets=[], nof_beamlets_per_iblet=[]):
          #
          # This function reads the beamlet statistics from the FPGAs.
          # The beamlet statistics are generated right after the beamformer.
          #
          # It returns a list with the beamlet statistics (bl_data)
          # The format of the returned list is:
          #
          #    bl_data[BFU][BL]
          #
          #    Where BFU = beamformer unit number
          #           BL = beamlet number
          #

          print  'Read Beamlet Statistics Samples'
          nofFnNodes = 4

          bl_data=[]            # Beamlet data
          for i in range(len(st)):
              bl_data.append(flatten(st[i].read_stats()))

          self.bl_data = bl_data
          if store_data == 'yes':
              single_row_beamlet_data=[]
              sb_oriented_bl=[]
              max_beams   =np.max(np.max(nof_beamlets_per_iblet))
              nof_stats = len(bl_data[0])
              for node_cnt in range (nofFnNodes):
                for BFunit_cnt in range(apr.c_nof_bf_units):
                  for stat_cnt in range(nof_stats):
                    single_row_beamlet_data.append(bl_data[node_cnt*apr.c_nof_bf_units+BFunit_cnt][stat_cnt])
              stati_cnt=0
              for iblet_cnt in range(len(iblets)):
                  single_sb=range(max_beams)# Make array with correct size to override...
                  for nof_beamlets_per_iblet_cnt in range(nof_beamlets_per_iblet[iblet_cnt]):
                      single_sb[nof_beamlets_per_iblet_cnt]=(single_row_beamlet_data[stati_cnt])
                      stati_cnt+=1
                  sb_oriented_bl.append(single_sb)
              file_name = 'BeamletStati_' + str(file_number) + '.mat'
              spio.savemat(file_name, {'beam_stati':sb_oriented_bl, 'iblets' : iblets, 'nof_beamlets_per_iblet': nof_beamlets_per_iblet, 'number':file_number}, appendmat=False)

          print 'Beamlet Statistics Samples taken'
          return bl_data

  def plot_beamlet_raw(self, plot_type='color', norm='no',fig_nr=1):
          #
          # Function plotting the beamlet statistics raw (256x)
          #
          # fig_nr   >> number of the figure
          # plot_type options:
          # - 'color'    --> 3D color plot
          # - 'bolletje' --> plot with circles
          # norm options:
          # - 'no' --> no normalisationsvn
          # - 'dB' --> dB scale
          #

          pl_data=self.bl_data

          norm_data=[]


          for rw_cnt in range(len(pl_data)):
            rw_data = []
            for cl_cnt in range(len(pl_data[rw_cnt])):
              if norm=='dB':
                temp = 10*np.log10(pl_data[rw_cnt][cl_cnt]+1)
                c_label = 'Output power dB'
              elif norm=='no':
                temp = pl_data[rw_cnt][cl_cnt]
                c_label = 'Output power raw'
              else:
                temp = np.sqrt(pl_data[rw_cnt][cl_cnt]/apr.c_bsn_period)
                c_label = 'Output power lin. norm.'
              rw_data.append(temp)
            norm_data.append(rw_data)
          plot_data=norm_data

          if self.show_figs == 1:
            pl.figure(fig_nr)
            pl.clf()
          if plot_type=='bolletje':
            for cnt in range(len(plot_data)):
              pl.plot(plot_data[cnt], 'o', label=('BF Cell '+ str(cnt)))
            pl.grid(True)
            pl.xlabel('Beamlet nr')
            pl.ylabel(c_label)
            pl.legend()
            stri = 'BeamLet Power '
            pl.title(stri)
            if self.show_figs == 1:
              pl.draw()

          else:
            pl.pcolormesh(np.array(plot_data))
            stri = 'Beamlet Statistics'
            pl.title(stri)
            cbar = pl.colorbar()
            cbar.set_label(c_label)
            #pl.clim([clim_min, 10])
            pl.ylim([0, len(pl_data)])
            pl.xlim([0, len(pl_data[0])])
            pl.xlabel('Beamlet')
            pl.ylabel('Beamformer Unit')
            if self.show_figs == 1:
              pl.draw()

  def plot_beamlet_subband(self, bf, iblets=[], nof_beamlets_per_iblet=[], beams_to_plot=1, lim_axis='on', norm='no', plot_type='color',fig_nr=1, pl_legend='on', xas='freq_z2',store_results='off', single_plot ='yes', file_number=1):
      #
      # Function plotting the beamlet statistics subband oriënted (256x)
      #
      # fig_nr   >> number of the figure
      # plot_type options:
      # - 'color'--> 3D color plot
      # - 'freq' --> normal line plot (2D)
      # norm options:
      # - 'no' --> no normalisation
      # - 'dB' --> dB scale
      # iblets  >> offsets between the subbands in the BFunit (number of beams for subband)
      # pl_legend  options
      # 'on' --> plot legend in figure
      # other --> no legend, can be handy.. legend block part of the plot
      # xas options:
      # - bin             --> frequency channel number
      # - freq            --> down sampled frequency number
      # - freq_z2         --> frequency number in zone 2
      # - lim_freq _z2       --> limit frequency axis
      # lim_axis options:
      # - on              --> Y-axis are fixed for full scale range
      # - off             --> Y-axis adjusted to level to plot

      bl_data = self.bl_data
      file_type = 'mat'

      sb_oriented_bl = []
      nofFnNodes = 4
      c_nof_bf_units  = 4

      print 'Reorder data'
      # make data flat array
      single_row_beamlet_data = []
      max_beams = np.max(np.max(nof_beamlets_per_iblet))
      for node_cnt in range(nofFnNodes):
          for BFunit_cnt in range(c_nof_bf_units):
              for stat_cnt in range(len(bl_data[node_cnt * 4 + BFunit_cnt])):
                  single_row_beamlet_data.append(bl_data[node_cnt * 4 + BFunit_cnt][stat_cnt])
      # make data [subband][beam]-oriented
      stati_cnt = 0
      sb_oriented_bl = []
      for iblet_cnt in range(len(iblets)):
          single_sb = range(max_beams)  # Make array with correct size to override...
          for nof_beamlets_per_iblet_cnt in range(nof_beamlets_per_iblet[iblet_cnt]):
              single_sb[nof_beamlets_per_iblet_cnt] = (single_row_beamlet_data[stati_cnt])
              stati_cnt += 1
          sb_oriented_bl.append(single_sb)

      # order the subband from low-to-high (needed when SS is set nonlinear)
      if len(iblets) < 3:
          pl_data = np.transpose(sb_oriented_bl)
          subbands = range(len(pl_data[0]))
          x_label = 'Random Subband (bin)'
          x_data = subbands
          xas = 'bin'
      else:
          x_label = 'Subband nr'
          subband_order = np.argsort(iblets)
          subbands = np.sort(iblets)
          ro_pl_data = []
          for of_cnt in subband_order:
              ro_pl_data.append(sb_oriented_bl[of_cnt])
          pl_data = np.transpose(ro_pl_data)

          # make frequency axis
          x_data = []
          if (xas == 'freq') | (xas == 'freq_z2') | (xas == 'lim_freq_z2'):
              if (xas == 'freq_z2'):
                  x_label = 'Frequency Zone 2 (MHz)'
              else:
                  x_label = 'Down Sampled Frequency (MHz)'
              for cnt in range(len(subbands)):
                  freq_point = self.sb_fas[subbands[cnt]]
                  if (xas == 'freq_z2') | (xas == 'lim_freq_z2'):
                      freq_point = self.fs - freq_point
                  x_data.append(freq_point)
          else:
              x_label = 'Subband Nr.'
              x_data = subbands

      print 'Normalize data'

      norm_data = []
      phase_data = []
      for row_cnt in range(len(pl_data)):
          row_amplitude_data = []
          row_phase_data = []
          for cl_cnt in range(len(pl_data[row_cnt])):
              abs_data = np.abs(pl_data[row_cnt][cl_cnt])
              if norm == 'dB':
                  temp = 10 * np.log10(abs_data + 1)
              elif norm == 'no':
                  temp = abs_data
              else:
                  temp = np.sqrt(pl_data[row_cnt][cl_cnt] / apr.c_bsn_period)
              row_amplitude_data.append(temp)
              if plot_type == 'complex':
                  row_phase_data.append(np.angle(pl_data[row_cnt][cl_cnt]))
              else:
                  row_phase_data.append(0)
          norm_data.append(row_amplitude_data)
          phase_data.append(row_phase_data)
      amplitude_data = norm_data

      if norm == 'dB':
          c_label = 'Output power (dB)'
      elif norm == 'no':
          c_label = 'Output power raw'
      else:
          c_label = 'Output power lin. norm.'

      stri = 'Beamlet Statistics '
      if self.show_figs == 1:
          print 'Plot Data'
          pl.figure(fig_nr)
          pl.clf()

      if plot_type == 'color':
          max_beams += 1  # Add 1 to plot last beam
          pl.pcolormesh(np.array(x_data), np.array(range(max_beams)), np.array(amplitude_data(range(max_beams))))
          cbar = pl.colorbar()
          cbar.set_label(c_label)
          pl.ylabel('Beam nr')
          pl.ylim([0, max_beams])
      elif (plot_type == 'freq') | (plot_type == 'complex'):
          if plot_type == 'complex':
              subplots = 2
          else:
              subplots = 1
          for cnt in range(beams_to_plot):
              if single_plot == 'no' and self.show_figs == 1:
                  pl.figure(fig_nr + cnt)
                  pl.clf()
              for subplot_cnt in range(subplots):
                  pl.subplot(subplots, 1, subplot_cnt + 1)
                  if subplot_cnt == 1:
                      pl.plot(x_data, phase_data[cnt], label=('Beam ' + str(cnt)))
                      pl.ylabel('Phase (RAD)')
                      pl.ylim([-4, 4])
                  else:
                      pl.plot(x_data, amplitude_data[cnt], label=('Beam ' + str(cnt)))
                      pl.ylabel(c_label)
                      if lim_axis == 'on':
                          pl.ylim([50, 140])
                      pl.title(stri)
                  if xas == 'freq':
                      pl.xlim([0, self.fs / 2])
                  elif xas == 'lim_freq_z2':
                      temp_gys = 0
                  elif xas == 'freq_z2':
                      pl.xlim([self.fs / 2, self.fs])
                  elif xas == 'bin':
                      pl.xlim([0, 512])
                  pl.grid(True)
              if pl_legend == 'on':
                  pl.legend()
              pl.xlabel(x_label)
      if self.show_figs == 1:
          pl.draw()

      self.pl_bl_data = amplitude_data
      # if store_results == 'on':
      #     if file_type == 'txt':
      #         self.dump_data(pl_data, x_data, x_label=x_label, y_label=c_label, title=stri, filename='beam_lets_dump.txt')
      #     else:
      #         file_name = 'Beamletdata_' + str(file_number) + '.mat'
      #         spio.savemat(file_name,
      #                      {'pl_data': pl_data, 'x_data': x_data, 'x_label': x_label, 'y_label': c_label, 'title': stri},
      #                      appendmat=False)
      if self.show_figs == 1:
          print 'Plot ready'

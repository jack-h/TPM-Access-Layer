import netproto.rmp as rmp
from bsp.spi import spi
from struct import *
import numpy as np
import time

class TPM_BSP(spi):
   def pll_out_set(self,idx):
      type = self.pll_out_config[idx]
      if type == "clk":
         reg0 = 0x0;
         reg1 = 0x0;
         reg2 = 0x0;
      elif type == "clk_div_4":
         reg0 = 0x0;
         reg1 = 0x0;
         reg2 = 0x3;
      elif type == "sysref":
         reg0 = 0x40;
         reg1 = 0x0;
         reg2 = 0x0;
      elif type == "sysref_hstl":
         reg0 = 0x40;
         reg1 = 0x80;
         reg2 = 0x0;
      else:
         reg0 = 0x0;
         reg1 = 0x0;
         reg2 = 0x0;
      return reg0,reg1,reg2 

   def pll_start(self,freq):
      """!@brief This function performs the PLL initialization procedure as implemented in ADI demo.

      @param freq -- int -- PLL output frequency in MHz. Supported frequency are 700,800,1000 MHz
      """
      print "Setting PLL. Frequency is " + str(freq)
      
      if freq != 1000 and freq != 800 and freq != 700:
         print "Frequency " + str(freq) + " MHz is not currently supported."
         print "Switching to default frequency 700 MHz"
         freq = 700

      rmp.wr32(0x30000008,0)
      time.sleep(1);
      rmp.wr32(0x30000008,1)
      
      self.wr_pll(0x0,0x1)
      while(True):
         if self.rd_pll(0x0)&0x1 == 0:
            break

      self.wr_pll(0xf,0x1);
     
      if self.board == "XTPM":
         self.pll_secure_wr(0x100,0x1);
         self.pll_secure_wr(0x102,0x1);
         #self.pll_secure_wr(0x104,0x8);
         self.pll_secure_wr(0x104,0xA);  #VCXO100MHz
         self.pll_secure_wr(0x106,0x14); #VCXO100MHz ##mod
         self.pll_secure_wr(0x107,0x13); #not disable holdover
         old = 0
         if old == 1:
            self.pll_secure_wr(0x108,0x10);
         else:
            self.pll_secure_wr(0x108,0x38); #VCXO100MHz ##mod  ##10MHZ: 0x38
         self.pll_secure_wr(0x109,0x4); 
         if old == 1:
            self.pll_secure_wr(0x10A,0x0); 
         else:
            self.pll_secure_wr(0x10A,0x2);  ###10MHZ: 0x2 
      else:
         self.pll_secure_wr(0x100,0x1);
         self.pll_secure_wr(0x102,0x1);
         self.pll_secure_wr(0x104,0x8);
         self.pll_secure_wr(0x106,0x14);
         self.pll_secure_wr(0x107,0x13);
         self.pll_secure_wr(0x108,0x2A);
         self.pll_secure_wr(0x109,0x4);
         self.pll_secure_wr(0x10A,0x0);
      
      if self.board == "XTPM":
         self.pll_secure_wr(0x200,0xe6);
         if freq == 1000:
            self.pll_secure_wr(0x201,10);
            self.pll_secure_wr(0x202,0x33);
            self.pll_secure_wr(0x203,0x10);
            self.pll_secure_wr(0x204,4);       #M1
            self.pll_secure_wr(0x205,0x2);
            self.pll_secure_wr(0x207,0x2);     
            self.pll_secure_wr(0x208,10-1);    #N2
         elif freq == 800:
            self.pll_secure_wr(0x201,10);
            self.pll_secure_wr(0x202,0x33);
            self.pll_secure_wr(0x203,0x10);
            self.pll_secure_wr(0x204,5);       #M1
            self.pll_secure_wr(0x205,0x2);
            self.pll_secure_wr(0x207,0x2);
            self.pll_secure_wr(0x208,8-1);     #N2
         elif freq == 700:
            self.pll_secure_wr(0x201,0xC8);
            ##self.pll_secure_wr(0x201,0x09);
            ###self.pll_secure_wr(0x201,0xC9);
            self.pll_secure_wr(0x202,0x33);
            self.pll_secure_wr(0x203,0x10);
            self.pll_secure_wr(0x204,0x5);     #M1
            ##self.pll_secure_wr(0x204,0x4);   #M1
            ###self.pll_secure_wr(0x204,0x3);  #M1
            self.pll_secure_wr(0x205,0x2);
            self.pll_secure_wr(0x207,0x2);
            self.pll_secure_wr(0x208,7-1);     #N2
            ##self.pll_secure_wr(0x208,9-1);   #N2
            ###self.pll_secure_wr(0x208,13-1); #N2
         else:
            print "Error PLL frequency not supported"   
      else:
         self.pll_secure_wr(0x200,0xe6);
         if freq == 1000:
            self.pll_secure_wr(0x201,0x19);
            self.pll_secure_wr(0x202,0x13);
            self.pll_secure_wr(0x203,0x10);
            self.pll_secure_wr(0x204,0x4); 
            self.pll_secure_wr(0x205,0x2);
            self.pll_secure_wr(0x207,0x2);     
            self.pll_secure_wr(0x208,0x18); 
         elif freq == 800:
            self.pll_secure_wr(0x201,0x46);
            self.pll_secure_wr(0x202,0x33);
            self.pll_secure_wr(0x203,0x10);
            self.pll_secure_wr(0x204,0x5); 
            self.pll_secure_wr(0x205,0x2);
            self.pll_secure_wr(0x207,0x1);
            self.pll_secure_wr(0x208,0x4); 
         elif freq == 700:
            self.pll_secure_wr(0x201,0xeb);
            self.pll_secure_wr(0x202,0x13);
            self.pll_secure_wr(0x203,0x10);
            self.pll_secure_wr(0x204,0x5); 
            self.pll_secure_wr(0x205,0x2);
            self.pll_secure_wr(0x207,0x4);
            self.pll_secure_wr(0x208,0x22);
         else:
            print "Error PLL frequency not supported"
         
      print "Setting PLL outputs"
      for n in range(14):
         reg0,reg1,reg2 = self.pll_out_set(n)
         self.pll_secure_wr(0x300+3*n+0,reg0);
         self.pll_secure_wr(0x300+3*n+1,reg1);
         self.pll_secure_wr(0x300+3*n+2,reg2);

      print "Setting SYSREF"
      self.pll_secure_wr(0x400,0x14);
      #self.pll_secure_wr(0x400,0x00);
      #self.pll_secure_wr(0x401,0x20);
      #self.pll_secure_wr(0x402,0x10);
      self.pll_secure_wr(0x403,0x96);
      print "Disabling unused channels"
      self.pll_secure_wr(0x500,0x10);
      pd = 0
      for c in range(14):
         if self.pll_out_config[c] == "unused":
            pd |= 2**c
      #self.pll_secure_wr(0x501,0xf0);
      self.pll_secure_wr(0x501,pd&0xFF);
      #self.pll_secure_wr(0x502,0x1c);
      self.pll_secure_wr(0x502,(pd&0xFF00)>>8);      
            
      while(True):
         if self.rd_pll(0xf) == 0:
            break
      self.wr_pll(0xf,0x1);

      self.pll_secure_wr(0x203,0x10);

      while(True):
         if self.rd_pll(0xf) == 0:
            break
      self.wr_pll(0xf,0x1);

      self.pll_secure_wr(0x203,0x11);
      while(True):
         if self.rd_pll(0xf) == 0:
            break
      self.wr_pll(0xf,0x1);

      self.wr_pll(0x403,0x97);
      while(True):
         if self.rd_pll(0xf) == 0:
            break
      self.wr_pll(0xf,0x1);

      self.wr_pll(0x32a,0x1);
      while(True):
         if self.rd_pll(0xf) == 0:
            break
      self.wr_pll(0xf,0x1);

      self.wr_pll(0x32a,0x0);
      while(True):
         if self.rd_pll(0xf) == 0:
            break
      self.wr_pll(0xf,0x1);

      self.wr_pll(0x203,0x10);
      self.wr_pll(0xf,0x1);
      self.wr_pll(0x203,0x11);
      self.wr_pll(0xf,0x1);

      print hex(self.rd_pll(0x509))
      
      while(True):
         if (self.rd_pll(0x509) & 0x1) == 0x0:
            break
         else:
            print "VCO calibration..."

      self.wr_pll(0x403,0x97);
      self.wr_pll(0xf,0x1);

      self.wr_pll(0x32A,0x1);
      self.wr_pll(0xf,0x1);

      self.wr_pll(0x32A,0x0);
      self.wr_pll(0xf,0x1);
      
      while(True):
         rd = self.rd_pll(0x508)
         print "register 0x508 " + hex(rd)
         print "register 0x509 " + hex(self.rd_pll(0x509))
         if rd == 0xF2 or rd == 0xe7:
            print "PLL Locked!"
            break
         else:
            print "PLL not Locked!"
            #xx = raw_input()
            #break
         
   def adc_single_start(self,idx,bit):
      """!brief This function performs the ADC configuration and initialization procedure as implemented in ADI demo.

      @param idx -- int -- ADC SPI index, legal value with ADI FMC are 0x1 and 0x2 
      @param bit -- int -- Sample bit width, supported value are 8,14
      """
      print "Setting ADC " + str(idx) + " @" + str(bit) + " bit"
      if bit != 14 and bit != 8 :
         print "Bit number " + str(bit) + " is not supported."
         print "Switching to 8 bits"
         bit = 8
      
      self.wr_adc(idx,0x0,0x1);
      while(True):
         if(self.rd_adc(idx,0x0)&0x1==0):
            break

      #self.wr_adc(idx,0x16,0x6C);
      self.wr_adc(idx,0x18,0x44);#input buffer current 3.0X
      #self.wr_adc(idx,0x25,0x0);
      #self.wr_adc(idx,0x30,0x10);
      
      self.wr_adc(idx,0x120,0x0);#sysref
      
      self.wr_adc(idx,0x550,0x00);#test pattern
      self.wr_adc(idx,0x573,0x00);#test pattern
      
      if (True):#idx == 1:
         self.wr_adc(idx,0x551,0x11);#test pattern
         self.wr_adc(idx,0x552,0x22);#test pattern
         self.wr_adc(idx,0x553,0x33);#test pattern
         self.wr_adc(idx,0x554,0x44);#test pattern
         self.wr_adc(idx,0x555,0x55);#test pattern
         self.wr_adc(idx,0x556,0x66);#test pattern
         self.wr_adc(idx,0x557,0x77);#test pattern
         self.wr_adc(idx,0x558,0x88);#test pattern
         
         self.wr_adc(idx,0x551,0x11);#test pattern
         self.wr_adc(idx,0x552,0x55);#test pattern
         self.wr_adc(idx,0x553,0x33);#test pattern
         self.wr_adc(idx,0x554,0x55);#test pattern
         self.wr_adc(idx,0x555,0x55);#test pattern
         self.wr_adc(idx,0x556,0x55);#test pattern
         self.wr_adc(idx,0x557,0x77);#test pattern
         self.wr_adc(idx,0x558,0x55);#test pattern
      else:
         self.wr_adc(idx,0x551,0x00);#test pattern
         self.wr_adc(idx,0x552,0x11);#test pattern
         self.wr_adc(idx,0x553,0x22);#test pattern
         self.wr_adc(idx,0x554,0x33);#test pattern
         self.wr_adc(idx,0x555,0x44);#test pattern
         self.wr_adc(idx,0x556,0x55);#test pattern
         self.wr_adc(idx,0x557,0x66);#test pattern
         self.wr_adc(idx,0x558,0x77);#test pattern

      self.wr_adc(idx,0x571,0x15);
      #self.wr_adc(idx,0x572,0x80);  #force CGS
      self.wr_adc(idx,0x572,0x10);   #SYNC CMOS level
      #print "sync CMOS " + hex(self.rd_adc(idx,0x572))
      
      self.wr_adc(idx,0x58b,0x81);
      self.wr_adc(idx,0x58d,0x1f);
      if bit == 14:
         self.wr_adc(idx,0x58f,0xF);
         self.wr_adc(idx,0x590,0x2F);
         self.wr_adc(idx,0x570,0x88);
         self.wr_adc(idx,0x58b,0x83);
         self.wr_adc(idx,0x590,0x2F);
         #lane remap
         self.wr_adc(idx,0x5b2,0x00);
         self.wr_adc(idx,0x5b3,0x01);
         self.wr_adc(idx,0x5b5,0x02);
         self.wr_adc(idx,0x5b6,0x03);
         self.wr_adc(idx,0x5b0,0xAA);
      else:
         self.wr_adc(idx,0x58f,0x7);
         self.wr_adc(idx,0x590,0x27);
         self.wr_adc(idx,0x570,0x48);
         #self.wr_adc(idx,0x570,0x0);
         self.wr_adc(idx,0x58b,0x81);
         #self.wr_adc(idx,0x58b,0x03);
         print "0x58b is " + str(self.rd_adc(idx,0x58b));
         self.wr_adc(idx,0x590,0x27);
         #lane remap
         self.wr_adc(idx,0x5b2,0x00);
         self.wr_adc(idx,0x5b3,0x01);
         self.wr_adc(idx,0x5b5,0x00);
         self.wr_adc(idx,0x5b6,0x01);
         self.wr_adc(idx,0x5b0,0xFA);#xTPM unused lane power down
            
      self.wr_adc(idx,0x571,0x14);
      
      
         
      #while(True):                        #PLL locked
      #   if(self.rd_adc(idx,0x56f)!=0x80):
      #      break
      #   else:
      #      print "ADC PLL not locked!"
      if bit == 14:
         if (self.rd_adc(idx,0x58b)!=0x83):    #jesd lane number
            print "Number of lane is not correct"
      else:
         if (self.rd_adc(idx,0x58b)!=0x81):    #jesd lane number
            print "Number of lane is not correct"
      if (self.rd_adc(idx,0x58c)!=0):          #octets per frame
         print "Number of octets per frame is not correct"
      if (self.rd_adc(idx,0x58d)!=0x1f):       #frames per multiframe
         print "Number of frame per multiframe is not correct"
      if (self.rd_adc(idx,0x58e)!=1):          #virtual converters
         print "Number of virtual converters is not correct"
      print "ADC " + str(idx) + " configured!"
      
   def adc_start(self,idx,bit):
      """!@brief Wrapper function performing ADC configuration"

      @param idx -- int -- ADC SPI index, legal value with ADI FMC are 0x1 and 0x2.
                    "all" cycles through 1 and 2.
      @param bit -- int -- Sample bit width, supported value are 8,14
      """
      if self.board == "XTPM":
         idx_list = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
      else:
         idx_list = [0,1]
     
      if idx == "all":
         for n in idx_list:
            self.adc_single_start(n,bit)
      else:
         self.adc_single_start(idx,bit)
         
   def jesd_core_start(self,fpga_idx,core_idx,bit):
      """!@brief This function performs the FPGA internal JESD core configuration and initialization procedure as implemented in ADI demo.

      @param bit -- int -- Sample bit width, supported value are 8,14
      """
      print "Setting JESD core @" + str(bit) + " bit"
      if bit != 14 and bit != 8 :
         print "Bit number " + str(bit) + " is not supported."
         print "Switching to 8 bits"
         bit = 8
      rmp.wr32(0x00010008+fpga_idx*0x10000000+core_idx*0x1000, 0x1);
      rmp.wr32(0x00010010+fpga_idx*0x10000000+core_idx*0x1000, 0x0); #sysref
      rmp.wr32(0x0001000C+fpga_idx*0x10000000+core_idx*0x1000, 0x1); #scrambling
      rmp.wr32(0x00010020+fpga_idx*0x10000000+core_idx*0x1000, 0x0);
      rmp.wr32(0x00010024+fpga_idx*0x10000000+core_idx*0x1000, 0x1f);
      if self.board == "XTPM":
         rmp.wr32(0x00010028+fpga_idx*0x10000000+core_idx*0x1000, 0x7); #xTPM
      else:
         if bit == 14:
            rmp.wr32(0x00010028, 0x7);
         else:
            rmp.wr32(0x00010028, 0x3);
      rmp.wr32(0x0001002C+fpga_idx*0x10000000+core_idx*0x1000, 0x1);
      rmp.wr32(0x00010004+fpga_idx*0x10000000+core_idx*0x1000, 0x1);
      
   def fpga_start(self,idx,input_list,enabled_list):
      """!@brief This function starts the FPGA acquisition and data downloading through 1Gbit Ethernet
      """
      filter_list = []
      for n in input_list:
         if n in enabled_list:
            filter_list.append(n)

      disabled_input = 0xFFFF
      for input in filter_list:
         mask = 1 << input
         disabled_input = disabled_input ^ mask
      
      rmp.wr32(0x30000008, 0x0081);	#pwdn ADCs
      rmp.wr32(0x30000010, 0x0000);	#0x1 accende ADA
      rmp.wr32(0x3000000C, 0x0);
      
      rmp.wr32(0x00030400+idx*0x10000000, 0x8);#bit per sample
      
      #rmp.wr32(0x0000000C+idx*0x10000000, disabled_input);
      rmp.wr32(0x0001F004+idx*0x10000000, disabled_input);
      #rmp.wr32(0x00000004+idx*0x10000000, 0x1);#xTPM
      rmp.wr32(0x00030404+idx*0x10000000, 0x1);#xTPM
      #rmp.wr32(0x00000008+idx*0x10000000, 0x0);
      rmp.wr32(0x0001F000+idx*0x10000000, 0x0);
      #rmp.wr32(0x00000008+idx*0x10000000, 0x1);
      rmp.wr32(0x0001F000+idx*0x10000000, 0x1);
      
      #time.sleep(2)
      
      #setting default buffer configuration
      for n in range(16):
         rmp.wr32(0x00030000+4*n, n);  #first lane
         rmp.wr32(0x00030100+4*n, n);  #last lane
         rmp.wr32(0x00030200+4*n, n);  #write mux
      rmp.wr32(0x00030300,0xFFFF);     #write mux we
      rmp.wr32(0x00030304,0);          #write mux we shift
      
      #setting buffer configuration
      nof_input = len(filter_list)
      if self.board == "XTPM":
         slot_per_input = 16/nof_input
      else:
         slot_per_input = 8/nof_input
      
      k=0
      for n in sorted(filter_list):
         rmp.wr32(0x00030000+4*n, k); #first lane
         rmp.wr32(0x00030100+4*n, k+(slot_per_input-1)); #last lane
         k += slot_per_input
      for n in range(16):
         if n/slot_per_input < len(filter_list):
            rmp.wr32(0x00030200+4*n, sorted(filter_list)[n/slot_per_input]);  #write mux
      mask = 0
      for n in range(nof_input):
         mask = mask << slot_per_input
         mask |= 0x1
      rmp.wr32(0x00030300,mask);
      rmp.wr32(0x00030304,0);

      #time.sleep(1)   
      #self.wr_adc("all",0x572,0x80);  
      #self.wr_adc("all",0x572,0xC0); #Force ILA and user data phase
      
   def fpga_stop(self):
      """!@brief This function stops the FPGA acquisition and data downloading through 1Gbit Ethernet
      """
      #rmp.wr32(0x00000004, 0x0);
      rmp.wr32(0x00030404, 0x0);
      #rmp.wr32(0x10000004, 0x0);
      #rmp.wr32(0x00000008, 0x0);
      rmp.wr32(0x0001F000, 0x0);
      #rmp.wr32(0x10000008, 0x0);
      time.sleep(1)

   def write_tag_ram(self,tag):
      print "Writing TAG ram..."
      word = 0
      for n in range(4096):
         if n < len(tag):
            word = (word >> 8) | (int(tag[n].encode("hex"),16) << 24)
         else:
            word = (word >> 8) | (int(" ".encode("hex"),16) << 24)
         if n % 4 == 3:
            rmp.wr32(0x00031000+4*(n/4),word)
            word = 0
      
   def acq_start(self,freq,bit,input_list,ada):
      """!@brief This function performs the start-up procedure of the whole system. 
      
      It configures PLL, ADCs and FPGA and starts the data download.

      @param freq -- int -- PLL output frequency in MHz. Supported frequency are 700,800,1000 MHz
      @param bit -- int -- Sample bit width, supported value are 8,14
      """
      if self.board == "XTPM":
         enabled_adc = [0,1,2,3,4,5,6,7]
         fpga_num = 1
         jesd_core_num = 2
      else:
         enabled_adc = [0,1]
         fpga_num = 1
         jesd_core_num = 1
      adc_per_fpga = len(enabled_adc)/fpga_num
      
      self.fpga_stop()
      #Configure PLL
      self.pll_start(freq)
      #Configure all ADC
      for n in enabled_adc:
         self.adc_start(n,bit)
      for n in enabled_adc:
         self.wr_adc(n,0x3F,0x80); #disabling pwdn input pin
      #Configure JESD core
      for f in range (fpga_num):
         for c in range(jesd_core_num):
            self.jesd_core_start(f,c,bit)
      #Start download
      for f in range(fpga_num):
         self.fpga_start(f,input_list,range(adc_per_fpga*2*f,adc_per_fpga*2*(f+1)))
      
      #time.sleep(1)
      
      rmp.wr32(0x00030404+0*0x10000000, 0x0);
      rmp.wr32(0x00030404+1*0x10000000, 0x0);
      
      if ada == True:
         rmp.wr32(0x30000008, 0x281)
         rmp.wr32(0x30000010, 0x5)
         print "ADAs powered on!"
      
      time.sleep(1)
      print "acq_start done!"
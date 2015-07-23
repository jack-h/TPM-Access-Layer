import netproto.rmp as rmp
import numpy as np

class spi:
   def __init__(self, board):
      self.spi_en_matrix = {}
      self.spi_sclk_matrix = {}
      self.pll_out_config = []
      self.board = board
      self.spi_if_base_address = 0 
      if self.board == "XTPM":
         spi_adc_en   = np.array([0,1,2,3,0,1,2,3,0,1,2,3,0,1,2,3])
         spi_adc_sclk = np.array([0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3])
         spi_amp_en   = np.array([0,1,2,3,4,5,6,7,0,1,2,3,4,5,6,7,0,1,2,3,4,5,6,7,0,1,2,3,4,5,6,7])
         spi_amp_sclk = np.array([0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3])
         spi_pll_en   = np.array([0])
         spi_pll_sclk = np.array([0])
         spi_amp_en   += 4 
         spi_amp_sclk += 4 
         spi_pll_en   += (4+8)
         spi_pll_sclk += (4+4)
      else:
         spi_adc_en   = np.array([0,1])
         spi_adc_sclk = np.array([0,0])
         spi_amp_en   = np.array([3,4,5,6])
         spi_amp_sclk = np.array([0,0,0,0])
         spi_pll_en   = np.array([2])
         spi_pll_sclk = np.array([0])

      self.spi_en_matrix   = {"adc": spi_adc_en,
                              "amp": spi_amp_en,
                              "pll": spi_pll_en}
      self.spi_sclk_matrix = {"adc": spi_adc_sclk,
                              "amp": spi_amp_sclk,
                              "pll": spi_pll_sclk}
                              
      if board == "XTPM":
         self.pll_out_config = ["sysref_hstl",	#"sysref_hstl",
                                "unused",       #"clk", 		
                                "clk",          #"unused",	
                                "unused",	      #"unused",
                                "sysref_hstl",	#"sysref_hstl",
                                "unused",	      #"unused",
                                "clk_div_4",    #"unused",
                                "unused",	      #"unused",
                                "clk_div_4",    #"unused",
                                "sysref",	      #"unused",
                                "sysref",	      #"unused",
                                "unused",	      #"unused",
                                "clk_div_4",    #"unused",
                                "clk_div_4"]    #"unused", 
      else:
         self.pll_out_config = ["clk_div_4",
                                "clk_div_4",
                                "sysref",
                                "clk",
                                "unused",
                                "unused",
                                "unused",
                                "unused",
                                "clk",
                                "sysref",
                                "unused",
                                "unused",
                                "unused",
                                "sysref"] 
                                
   def set_spi_if_base_address(self,address):
      self.spi_if_base_address = address
    
   def spi_matrix(self,device,idx):
      spi_en = 0
      spi_sclk = 0
      if idx == "all" and device == "adc":
         for x in spi_adc_en:
            spi_en |= (2**x)
         for x in spi_adc_sclk:
            spi_sclk |= (2**x)
      elif idx != "all":
         spi_en   = 2**(self.spi_en_matrix[device][idx])
         spi_sclk = 2**(self.spi_sclk_matrix[device][idx])
      else:
         raise "\"all\" can be used for adc only" 
      return spi_en,spi_sclk
   
   def spi_access(self,op,spi_en,spi_sclk,add,dat):
      """!@brief Access an SPI connected device
      
      This function provide access to an SPI connected device.
      
      @param op  -- str -- "wr" or "rd"
      @param idx -- int -- This parameter selects the active chip select for the current transaction.
                 When more then one SPI device share clock and data line, it is necessary to
                 specify which device should be addressed.
      @param add -- int -- SPI device address, register offset to be accessed within the SPI device
      @param dat -- int -- Write data for write operations or don't care for read operations
      
      Returns -- int -- read data for read operations or don't care for write operations
      """
      while(True):
         if ((rmp.rd32(self.spi_if_base_address+0x14)&0x1)==0):
            break
      pkt = []
      pkt.append(add)
      pkt.append(dat << 8)
      pkt.append(0x0)
      pkt.append(spi_en)
      pkt.append(spi_sclk)     
      
      rmp.wr32(self.spi_if_base_address,pkt)
      
      if op == "wr":
         rmp.wr32(self.spi_if_base_address+0x14,0x01)
      elif op == "rd":
         rmp.wr32(self.spi_if_base_address+0x14,0x03)
      while(True):
         if ((rmp.rd32(self.spi_if_base_address+0x14)&0x1)==0):
            break
      return (rmp.rd32(self.spi_if_base_address+0x08) & 0xFF)

   def wr_pll(self,add,dat):
      """!@brief Wrapper for PLL write access, SPI idx 0x4"""
      spi_en,spi_sclk = self.spi_matrix("pll",0)
      return self.spi_access("wr",spi_en,spi_sclk,add,dat)
   def rd_pll(self,add):
      """!@brief Wrapper for PLL read access, SPI idx 0x4"""
      spi_en,spi_sclk = self.spi_matrix("pll",0)
      return self.spi_access("rd",spi_en,spi_sclk,add,0x0)
   def wr_adc(self,idx,add,dat):
      """!@brief Wrapper for ADC write access, SPI idx 0x1 or 0x2"""
      spi_en,spi_sclk = self.spi_matrix("adc",idx)
      return self.spi_access("wr",spi_en,spi_sclk,add,dat)
   def rd_adc(self,idx,add):
      """!@brief Wrapper for ADC read access, SPI idx 0x1 or 0x2"""
      spi_en,spi_sclk = self.spi_matrix("adc",idx)
      return self.spi_access("rd",spi_en,spi_sclk,add,0x0)
   
   def pll_secure_wr(self,add,dat):
      """!@brief Securely write PLL registers 
      
      This function read a PLL register and performs a write to that register in case
      the read value differs from dat input parameter. In the ADI demo all the PLL write accesses
      are done this way, I don't know if it is really needed or a simple write is enough...
      
      @param add -- int -- PLL register offset to be accessed
      @param dat -- int -- Write data
      """
      #if rd_pll(add) != dat:
      self.wr_pll(add,dat)
       

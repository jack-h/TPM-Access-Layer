library ieee;
use ieee.std_logic_1164.all;

library <BUS_LIBRARY>;
use <BUS_LIBRARY>.<BUS>_pkg.all;
library <DSN_LIBRARY>;
use <DSN_LIBRARY>.<BUS>_<TOP_LEVEL>_ic_pkg.all;
use <DSN_LIBRARY>.<BUS>_<TOP_LEVEL>_mmap_pkg.all;

entity <BUS>_<TOP_LEVEL>_ic is
   port(
      <BUS_CLK> : in std_logic; 
      <BUS_RST> : in std_logic; 
      
      <BUS>_mosi      : in  t_<BUS>_mosi;       -- signals from master to interconnect
      <BUS>_mosi_arr  : out t_<BUS>_mosi_arr;   -- signals from interconnect to slaves
      
      <BUS>_miso_arr  : in  t_<BUS>_miso_arr;   -- signals from slaves to interconnect
      <BUS>_miso      : out t_<BUS>_miso        -- signals from interconnect to master
   );
end entity;

-------------------------------------------------------------------------------
-- Architecture
-------------------------------------------------------------------------------
architecture behav of <BUS>_<TOP_LEVEL>_ic is
   
   signal axi4lite_miso_int: t_axi4lite_miso;
   signal addr_sel: std_logic_vector(c_axi4lite_addr_w-1 downto 0);
   signal slave_hit_c: std_logic_vector(c_axi4lite_mmap_nof_slave-1 downto 0);
   signal slave_hit_r: std_logic_vector(c_axi4lite_mmap_nof_slave-1 downto 0);
   type t_fsm is (rdy,wr,rd);
   signal fsm: t_fsm;
  
begin
   
   addr_sel <= axi4lite_mosi.awaddr when axi4lite_mosi.awvalid = '1' else axi4lite_mosi.araddr;
   slave_hit_c <= axi4lite_mmap_decoder(addr_sel);
   
   axi4lite_master2slaves(c_axi4lite_mmap_nof_slave,
                          slave_hit_r,
                          slave_hit_r,
                          slave_hit_r,
                          slave_hit_r,
                          slave_hit_r,
                          axi4lite_mosi,axi4lite_mosi_arr);
   axi4lite_slaves2master(c_axi4lite_mmap_nof_slave,
                          slave_hit_r,
                          slave_hit_r,
                          slave_hit_r,
                          slave_hit_r,
                          slave_hit_r,axi4lite_miso_arr,axi4lite_miso_int);
                          
   process(<BUS_CLK>,<BUS_RST>)
   begin
      if rising_edge(<BUS_CLK>) then
         
         case fsm is
            when rdy =>
               if axi4lite_mosi.awvalid = '1' or axi4lite_mosi.arvalid = '1' then
                  slave_hit_r <= slave_hit_c;
               end if;
               if axi4lite_mosi.awvalid = '1' then
                  fsm <= wr;
               elsif axi4lite_mosi.arvalid = '1' then
                  fsm <= rd;
               end if;
            when wr =>
               if axi4lite_mosi.bready = '1' and axi4lite_miso_int.bvalid = '1' then
                  slave_hit_r <= (others=>'0');
                  fsm <= rdy;
               end if;
            when rd =>
               if axi4lite_mosi.rready = '1' and axi4lite_miso_int.rvalid = '1' then
                  slave_hit_r <= (others=>'0');
                  fsm <= rdy;
               end if;
         end case;
          
      end if;
      if <BUS_RST> = '<BUS_RST_VAL>' then
         slave_hit_r <= (others=>'0');
         fsm <= rdy;
      end if;
   end process;
   
   axi4lite_miso <= axi4lite_miso_int;
   
end architecture;

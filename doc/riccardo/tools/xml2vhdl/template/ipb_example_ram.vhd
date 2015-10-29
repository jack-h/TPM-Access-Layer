library IEEE;
use IEEE.std_logic_1164.all;
use ieee.numeric_std.all;

use work.axi4lite_pkg.all;
     
entity ipb_example_ram is
   generic(
      ram_add_width: integer := 4
   );
   port(
      ipb_clk        : in std_logic; 
   
      ipb_miso       : out t_ipb_miso;
      ipb_mosi       : in t_ipb_mosi
   );
end entity;     

architecture ipb_example_ram_a of ipb_example_ram is 
   
   type t_ram is array (0 to 2**ram_add_width-1) of std_logic_vector(ipb_mosi.wdat'length-1 downto 0);
   signal ram: t_ram;
   signal ram_add: std_logic_vector(ram_add_width-1 downto 0);
   signal ram_dat: std_logic_vector(ipb_mosi.wdat'length-1 downto 0);
   
begin

   process(ipb_clk)
   begin
      if rising_edge(ipb_clk) then
         ram_dat <= ram(to_integer(unsigned(ram_add)));
         if ipb_mosi.wreq = '1' then
            ram(to_integer(unsigned(ram_add))) <= ipb_mosi.wdat;
         end if;
         ipb_miso.rack <= ipb_mosi.rreq;
      end if;
   end process;
   
   ram_add <= ipb_mosi.addr(ram_add_width+2-1 downto 0+2);
   
   ipb_miso.rdat <= ram_dat;
   ipb_miso.wack <= '1';
   
end architecture;


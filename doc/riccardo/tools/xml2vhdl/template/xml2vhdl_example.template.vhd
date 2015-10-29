library ieee;
use ieee.std_logic_1164.all;

library <BUS_LIBRARY>;
use <BUS_LIBRARY>.<BUS>_pkg.all;
library <DSN_LIBRARY>;
use <DSN_LIBRARY>.<BUS>_<TOP_LEVEL>_ic_pkg.all;
use <DSN_LIBRARY>.<BUS>_<TOP_LEVEL>_mmap_pkg.all;

entity <BUS>_<TOP_LEVEL>_example is
   port(
      <BUS_CLK> : in std_logic;
      <BUS_RST> : in std_logic;
      
      <BUS>_mosi      : in  t_<BUS>_mosi;       -- signals from master to interconnect
      <BUS>_miso      : out t_<BUS>_miso        -- signals from interconnect to master
   );
end entity;

-------------------------------------------------------------------------------
-- Architecture
-------------------------------------------------------------------------------
architecture struct of <BUS>_<TOP_LEVEL>_example is
   
   signal <BUS>_mosi_arr  : t_<BUS>_mosi_arr(0 to c_axi4lite_mmap_nof_slave-1);   -- signals from interconnect to slaves
   signal <BUS>_miso_arr  : t_<BUS>_miso_arr(0 to c_axi4lite_mmap_nof_slave-1);   -- signals from slaves to interconnect
   
begin
   
   <BUS>_<TOP_LEVEL>_ic_inst: entity work.<BUS>_<TOP_LEVEL>_ic
   port map (
      <BUS_CLK> => <BUS_CLK>,
      <BUS_RST> => <BUS_RST>,
      <BUS>_mosi => <BUS>_mosi,
      <BUS>_mosi_arr => <BUS>_mosi_arr,
      <BUS>_miso_arr => <BUS>_miso_arr,
      <BUS>_miso => <BUS>_miso
   );
<SLAVE_INST>

end architecture;

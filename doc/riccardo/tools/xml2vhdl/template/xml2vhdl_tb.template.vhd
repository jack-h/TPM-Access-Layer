library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library <BUS_LIBRARY>;
use <BUS_LIBRARY>.<BUS>_pkg.all;
library <SLAVE_LIBRARY>;
use <SLAVE_LIBRARY>.<BUS>_<SLAVE_NAME>_pkg.all;

entity <BUS>_<SLAVE_NAME>_tb is
end entity ;

architecture tb of <BUS>_<SLAVE_NAME>_tb is

   signal <BUS_CLK> : std_logic:='0';
   signal <BUS_RST> : std_logic:='0';
   signal <BUS>_mosi : t_axi4lite_mosi;
   signal <BUS>_miso : t_axi4lite_miso;

<REMOVE_IF_BLOCK_ONLY_START>
<REMOVE_IF_NO_FW_WRITE_START>
   signal <BUS>_<SLAVE_NAME>_in_we : <BUS>_<SLAVE_NAME>_decoded; 
   signal <BUS>_<SLAVE_NAME>_in : t_<BUS>_<SLAVE_NAME> 
<REMOVE_IF_NO_FW_WRITE_END>
   signal <BUS>_<SLAVE_NAME>_out_we : <BUS>_<SLAVE_NAME>_decoded; 
   signal <BUS>_<SLAVE_NAME>_out : t_<BUS>_<SLAVE_NAME> 
<REMOVE_IF_BLOCK_ONLY_END>
<MEMORY_BLOCKS_SIGNAL>
  
begin 

   <BUS_CLK> <= not <BUS_CLK> after 5 ns;
   <BUS_RST> <= '<BUS_RST_VAL>' after 0 ns, not('<BUS_RST_VAL>') after 100 ns;
   -----------------------------
   -- <BUS> master instantiation 
   -----------------------------   
   <BUS>_sim_ms_inst: entity <SLAVE_LIBRARY>.<BUS>_<SLAVE_NAME>_sim_ms
   port map(
      <BUS_CLK> => <BUS_CLK>,
      <BUS_RST> => <BUS_RST>,
      
      <BUS>_mosi => <BUS>_mosi,
      <BUS>_miso => <BUS>_miso
   );
   -----------------------------
   -- DUT instantiation 
   -----------------------------
   dut_inst: entity <SLAVE_LIBRARY>.<BUS>_<SLAVE_NAME>
   port map(
      <BUS_CLK> => <BUS_CLK>,
      <BUS_RST> => <BUS_RST>,
      
      <BUS>_mosi => <BUS>_mosi,
      <BUS>_miso => <BUS>_miso,
<MEMORY_BLOCKS_PORTMAP>
<REMOVE_IF_BLOCK_ONLY_START>
<REMOVE_IF_NO_FW_WRITE_START>
      <BUS>_<SLAVE_NAME>_in_we => <BUS>_<SLAVE_NAME>_in_we, 
      <BUS>_<SLAVE_NAME>_in => <BUS>_<SLAVE_NAME>_in, 
<REMOVE_IF_NO_FW_WRITE_END>
      <BUS>_<SLAVE_NAME>_out_we => <BUS>_<SLAVE_NAME>_out_we, 
      <BUS>_<SLAVE_NAME>_out => <BUS>_<SLAVE_NAME>_out, 
<REMOVE_IF_BLOCK_ONLY_END>
);
end architecture;
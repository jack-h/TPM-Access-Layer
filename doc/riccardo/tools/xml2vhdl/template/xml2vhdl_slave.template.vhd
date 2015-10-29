library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library <BUS_LIBRARY>;
use <BUS_LIBRARY>.<BUS>_pkg.all;
library <SLAVE_LIBRARY>;
use <SLAVE_LIBRARY>.<BUS>_<SLAVE_NAME>_pkg.all;
     
entity <BUS>_<SLAVE_NAME> is
<RESET_GENERICS_DEFINITION>
   port(
      <BUS_CLK> : in std_logic;
      <BUS_RST> : in std_logic;
      
      <BUS>_mosi : in t_<BUS>_mosi;
      <BUS>_miso : out t_<BUS>_miso;
<MEMORY_BLOCKS_PORT>
<REMOVE_IF_BLOCK_ONLY_START>
<REMOVE_IF_NO_FW_WRITE_START>
      <BUS>_<SLAVE_NAME>_in_we : in t_<BUS>_<SLAVE_NAME>_decoded;
      <BUS>_<SLAVE_NAME>_in : in t_<BUS>_<SLAVE_NAME>;
<REMOVE_IF_NO_FW_WRITE_END>
      <BUS>_<SLAVE_NAME>_out_we : out t_<BUS>_<SLAVE_NAME>_decoded;
      <BUS>_<SLAVE_NAME>_out : out t_<BUS>_<SLAVE_NAME>;
<REMOVE_IF_BLOCK_ONLY_END>
);
end entity;     

architecture <BUS>_<SLAVE_NAME>_a of <BUS>_<SLAVE_NAME> is 

   signal ipb_mosi : t_ipb_mosi;
   signal ipb_miso : t_ipb_miso;
   
   signal ipb_mosi_arr : t_ipb_<SLAVE_NAME>_mosi_arr;
   signal ipb_miso_arr : t_ipb_<SLAVE_NAME>_miso_arr;
   
<REMOVE_IF_BLOCK_ONLY_START>
   signal <BUS>_<SLAVE_NAME>_int_we : t_<BUS>_<SLAVE_NAME>_decoded;
   signal <BUS>_<SLAVE_NAME>_int_re : t_<BUS>_<SLAVE_NAME>_decoded;
   signal <BUS>_<SLAVE_NAME>_int : t_<BUS>_<SLAVE_NAME>;
<REMOVE_IF_BLOCK_ONLY_END>

begin
   --
   --
   --
   <BUS>_slave_logic_inst: entity <BUS_LIBRARY>.<BUS>_slave_logic
   port map (
      <BUS_CLK> => <BUS_CLK>,
      <BUS_RST> => <BUS_RST>,
      <BUS>_mosi => <BUS>_mosi,
      <BUS>_miso => <BUS>_miso,
      ipb_mosi => ipb_mosi,
      ipb_miso => ipb_miso
   );
   --
   -- blocks_muxdemux
   --
   <BUS>_<SLAVE_NAME>_muxdemux_inst: entity <SLAVE_LIBRARY>.<BUS>_<SLAVE_NAME>_muxdemux
   port map(
      <BUS_CLK> => <BUS_CLK>,
      <BUS_RST> => <BUS_RST>,
      ipb_mosi => ipb_mosi,
      ipb_miso => ipb_miso,
      ipb_mosi_arr => ipb_mosi_arr,
      ipb_miso_arr => ipb_miso_arr   
   );
<MEMORY_BLOCKS_INST>
<REMOVE_IF_BLOCK_ONLY_START>
   --
   -- Address decoder
   --
   <BUS>_<SLAVE_NAME>_int_we <= <BUS>_<SLAVE_NAME>_full_decoder(ipb_mosi_arr(0).addr,ipb_mosi_arr(0).wreq);
   <BUS>_<SLAVE_NAME>_int_re <= <BUS>_<SLAVE_NAME>_full_decoder(ipb_mosi_arr(0).addr,ipb_mosi_arr(0).rreq);
   --
   -- Register write process
   --
   process(<BUS_CLK>,<BUS_RST>)
   begin
      if rising_edge(<BUS_CLK>) then
         --
         -- Write to registers from logic, put assignments here 
         -- if logic has lower priority than <BUS> bus master 
         --
         -- ...
         --
         -- hw_permission="w" or hw_permission="wen"
         -- hw_prio="bus"
         --
<HW_WRITE_REG_BUS_PRIO>
         --====================================================================
         --
         -- Write to registers from <BUS> side, think twice before modifying
         --
         <BUS>_<SLAVE_NAME>_write_reg(ipb_mosi_arr(0).wdat,
                                      <BUS>_<SLAVE_NAME>_int_we,
                                      <BUS>_<SLAVE_NAME>_int);
         --
         --====================================================================
         --
         -- Write to registers from logic, put assignments here 
         -- if logic has higher priority than <BUS> bus master
         --
         -- ...
         --
         -- hw_permission="w" or hw_permission="wen"
         -- hw_prio="logic"
         --
<HW_WRITE_REG_LOGIC_PRIO>
      end if;
      if <BUS_RST> = '<BUS_RST_VAL>' then
         <BUS>_<SLAVE_NAME>_reset(<BUS>_<SLAVE_NAME>_int<RESET_GENERICS_MAP>);
      end if;
   end process;
   
   ipb_miso_arr(0).wack <= '1';
   ipb_miso_arr(0).rack <= '1';
   ipb_miso_arr(0).rdat <= <BUS>_<SLAVE_NAME>_read_reg(<BUS>_<SLAVE_NAME>_int_re,
                                                       <BUS>_<SLAVE_NAME>_int);

   <BUS>_<SLAVE_NAME>_out    <= <BUS>_<SLAVE_NAME>_int; 
   <BUS>_<SLAVE_NAME>_out_we <= <BUS>_<SLAVE_NAME>_int_we;
<REMOVE_IF_BLOCK_ONLY_END>
   
end architecture;


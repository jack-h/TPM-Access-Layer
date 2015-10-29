library ieee;
use ieee.std_logic_1164.all;

library <BUS_LIBRARY>;
use <BUS_LIBRARY>.<BUS>_pkg.all;

package <BUS>_<TOP_LEVEL>_mmap_pkg is  
   --##########################################################################
   -- The AXI4 Lite subsystem is defined by
   --    * number of slaves
   --    * slave names
   --    * slave base addresses
   --
   -- Number of slaves, their names and base addresses are specified in 
   -- t_axi4lite_mmap_slave enum type. This must have a number of elements
   -- equal to the number of implemented slaves. Each element defines a slave
   -- name and corresponding slave id (positionally). Although it seems weird,
   -- base addresses are specified as element of an enum type, this permits to
   -- completely specify the AXI4 Lite subsystem in a single place, and we get
   -- some error checks for free, e.g. no slave can have the same base address
   -- without generating an error.
   --##########################################################################
<SLAVE_TYPE>
   constant c_axi4lite_mmap_nof_slave: positive := (<VHDL_RECORD>'pos(<VHDL_RECORD>'right) - 
                                                    <VHDL_RECORD>'pos(<VHDL_RECORD>'left)  + 1) / 2;
   
   type t_axi4lite_mmap_addr_arr is array (0 to c_axi4lite_mmap_nof_slave-1) of std_logic_vector(c_axi4lite_addr_w-1 downto 0);
   --
   -- THIS CONSTANT HOLDS BASE ADDRESSES. DO NOT MODIFY!
   --
   constant c_axi4lite_mmap_baddr: t_axi4lite_mmap_addr_arr;
   --
   -- THIS CONSTANT HOLDS DECODING MASKS. DO NOT MODIFY!
   --
   constant c_axi4lite_mmap_mask: t_axi4lite_mmap_addr_arr;
   --
   -- THIS FUNCTION CALCULATES BASE ADDRESSES FROM <VHDL_RECORD>. DO NOT MODIFY!
   --
   function axi4lite_mmap_get_baddr return t_axi4lite_mmap_addr_arr;
   --
   -- THIS FUNCTION CALCULATES DECODING MASKS FROM BASE ADDRESSES ARRAY. DO NOT MODIFY!
   --
   function axi4lite_mmap_get_mask(baddr: t_axi4lite_mmap_addr_arr) return t_axi4lite_mmap_addr_arr;
   --
   -- THIS FUNCTION CONVERTS BETWEEN SLAVE NAME AND SLAVE ID. DO NOT MODIFY!
   --
   function axi4lite_mmap_get_id(str_id: <VHDL_RECORD>) return integer;
   --
   -- THIS FUNCTION PERFORMS A SIMPLE ADDRESS DECODER. MODIFY IF NEEDED.
   --
   function axi4lite_mmap_decoder(addr: std_logic_vector) return std_logic_vector;

end package; 

package body <BUS>_<TOP_LEVEL>_mmap_pkg is
   
   function axi4lite_mmap_get_baddr return t_axi4lite_mmap_addr_arr is
      variable ret: t_axi4lite_mmap_addr_arr;
      variable str: string(1 to 8);
      variable ba: std_logic_vector(0 to 31);
      variable slv: std_logic_vector(3 downto 0);
      variable char: character;
   begin
      for n in 0 to c_axi4lite_mmap_nof_slave*2-1 loop
         if n mod 2 = 1 then
            str := <VHDL_RECORD>'image(<VHDL_RECORD>'val(n))(5 to 12);
            assert false
            report "axi4lite_mmap_get_baddr: found base address" & str 
            severity warning;
            for n in 0 to 7 loop
               char := str(n+1);
               assert false
               report "axi4lite_mmap_get_baddr " & char
               severity warning;
               case char is
                  when '0' => slv := X"0";
                  when '1' => slv := X"1";
                  when '2' => slv := X"2";
                  when '3' => slv := X"3";
                  when '4' => slv := X"4";
                  when '5' => slv := X"5";
                  when '6' => slv := X"6";
                  when '7' => slv := X"7";
                  when '8' => slv := X"8";
                  when '9' => slv := X"9";
                  when 'A' => slv := X"A";
                  when 'B' => slv := X"B";
                  when 'C' => slv := X"C";
                  when 'D' => slv := X"D";
                  when 'E' => slv := X"E";
                  when 'F' => slv := X"F";
                  when 'a' => slv := X"a";
                  when 'b' => slv := X"b";
                  when 'c' => slv := X"c";
                  when 'd' => slv := X"d";
                  when 'e' => slv := X"e";
                  when 'f' => slv := X"f";
                  when others => assert false
                                 report "axi4lite_mmap_get_baddr unexpected character " & str(n+1) & " in base address " & str
                                 severity failure;
               end case;
               ba(4*n to 4*(n+1)-1) := slv;
            end loop;
         end if;
         ret(n/2) := ba;
      end loop;
      return ret;
   end function;
   
   function axi4lite_mmap_get_mask(baddr: t_axi4lite_mmap_addr_arr) return t_axi4lite_mmap_addr_arr is
      type t_tree is array (0 to 31) of integer;
      type tt_tree is array (0 to baddr'length-1) of t_tree;
      type ttt_tree is array (0 to baddr'length-1) of tt_tree;
      variable tree: tt_tree;
      variable is_same: ttt_tree;
      variable ret: t_axi4lite_mmap_addr_arr;
      variable is_to_decode: integer;
      variable is_same_seq: integer;
   begin
      for b in 31 downto 0 loop
         --looking if bit b is the same for all base addresses
         for m in 0 to baddr'length-1 loop
            for n in 0 to baddr'length-1 loop 
               is_same(m)(n)(b) := 1;
               if baddr(m)(b) /= baddr(n)(b) then
                  is_same(m)(n)(b) := 0;
               end if;
            end loop;
         end loop;
         --looking if there is a common decoding path of previously decoded bits
         for m in 0 to baddr'length-1 loop
            is_to_decode := 0;
            for n in 0 to baddr'length-1 loop 
               if is_same(m)(n)(b) = 0 then
                  is_same_seq := 1;
                  if b < 31 then
                     for t in 31 downto b+1 loop
                        if tree(n)(t) /= tree(m)(t) then
                           is_same_seq := 0;
                        end if;
                     end loop;
                  end if;
                  if is_same_seq = 1 then
                     is_to_decode := 1;
                  end if;
               end if;
            end loop;
            if is_to_decode = 1 then
               if baddr(m)(b) = '1' then
                  tree(m)(b) := 1;
               else
                  tree(m)(b) := 0;
               end if;
            else
               tree(m)(b) := -1;
            end if;  
         end loop;
      end loop;
      --generating masks
      for n in 0 to baddr'length-1 loop
         for b in 0 to 31 loop
            if tree(n)(b) = -1 then
               ret(n)(b) := '0';
            else
               ret(n)(b) := '1';
            end if;
         end loop;
      end loop;
      return ret;
   end function;
  
   function axi4lite_mmap_get_id(str_id: <VHDL_RECORD>) return integer is
      variable ret: integer := -1;
   begin
      ret := <VHDL_RECORD>'pos(str_id); 
      assert ret mod 2 = 0
      report "axi4lite_mmap_get_id: slave id odd!"
      severity failure;
      return ret/2;     
   end function;
   
   function axi4lite_mmap_decoder(addr: std_logic_vector) return std_logic_vector is
      variable addr_i: std_logic_vector(addr'length-1 downto 0):=addr;
      variable slave_hit: std_logic_vector(c_axi4lite_mmap_nof_slave-1 downto 0);
   begin
      slave_hit := (others=>'1');
      for n in 0 to c_axi4lite_mmap_nof_slave-1 loop
         loop_b:for b in 0 to addr'length-1 loop
            if c_axi4lite_mmap_mask(n)(b) = '1' then
               if c_axi4lite_mmap_baddr(n)(b) /= addr_i(b) then
                  slave_hit(n) := '0';
                  exit loop_b;
               end if;
            end if;
         end loop;
      end loop;
      return slave_hit;
   end function;
   
   constant c_axi4lite_mmap_baddr: t_axi4lite_mmap_addr_arr := axi4lite_mmap_get_baddr;
   constant c_axi4lite_mmap_mask: t_axi4lite_mmap_addr_arr := axi4lite_mmap_get_mask(c_axi4lite_mmap_baddr);

end package body;

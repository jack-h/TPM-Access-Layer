--<h---------------------------------------------------------------------------
--
-- Copyright (C) 2015
-- University of Oxford <http://www.ox.ac.uk/>
-- Department of Physics
--
-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with this program.  If not, see <http://www.gnu.org/licenses/>.
--
-----------------------------------------------------------------------------h>

library ieee;
use ieee.std_logic_1164.all;

package environment_config_pkg is
   
   constant g_c2c_folder: string;
   constant g_c2c_swp_file: string;
   constant g_c2c_stream_file: string;
   
end package;

package body environment_config_pkg is

   constant g_c2c_folder: string := "<g_c2c_folder>";
   constant g_c2c_swp_file: string := "<g_c2c_swp_file>";
   constant g_c2c_stream_file: string := "<g_c2c_stream_file>";
   
end package body;
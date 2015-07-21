__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import *
import logging

"""Peripheral adu_i2c_commander

   MM register map from i2c_commander_aduh_pkg:

  . c_i2c_cmdr_aduh_protocol_commander.nof_protocols         = 16
  . c_i2c_cmdr_aduh_protocol_commander.nof_result_data_max   = 2
  . c_i2c_cmdr_aduh_i2c_mm.protocol_adr_w                    = 13
  . c_i2c_cmdr_aduh_i2c_mm.protocol_nof_dat                  = 5120 hw, 8192 sim
  . c_i2c_cmdr_aduh_i2c_mm.result_adr_w                      = 12
  . c_i2c_cmdr_aduh_i2c_mm.result_nof_dat                    = 4096
  . protocol_status_w = ceil_log2(c_i2c_cmdr_state_max)      = 2
  . result_error_cnt_w = result_adr_w                        = 12

   31             24 23             16 15              8 7               0  wi
  |-----------------|-----------------|-----------------|-----------------|
  |         xxx                             write access issues protocol 0|  0
  |-----------------------------------------------------------------------|
  |         xxx                             write access issues protocol 1|  1
  |-----------------------------------------------------------------------|
  |         xxx                             write access issues protocol 2|  2
  |-----------------------------------------------------------------------|
  |                                  ...                                  | ..
  |-----------------------------------------------------------------------|
  |         xxx                            write access issues protocol 15| 15
  |-----------------------------------------------------------------------|
  |         xxx                      protocol_offset[protocol_adr_w-1:0] 0| 16
  |-----------------------------------------------------------------------|
  |         xxx                      protocol_offset[protocol_adr_w-1:0] 1| 17
  |-----------------------------------------------------------------------|
  |         xxx                      protocol_offset[protocol_adr_w-1:0] 2| 18
  |-----------------------------------------------------------------------|
  |                                  ...                                  | ..
  |-----------------------------------------------------------------------|
  |         xxx                     protocol_offset[protocol_adr_w-1:0] 15| 31
  |-----------------------------------------------------------------------|
  |         xxx                                    result_expected[31:0] 0| 32
  |-----------------------------------------------------------------------|
  |         xxx                                    result_expected[31:0] 1| 33
  |-----------------------------------------------------------------------|
  |                                  ...                                  | ..
  |-----------------------------------------------------------------------|
  |         xxx                                   result_expected[31:0] 15| 47
  |-----------------------------------------------------------------------|
  |         xxx                                      protocol_status[31:0]| 48
  |-----------------------------------------------------------------------|
  |         xxx                                     result_error_cnt[31:0]| 49
  |-----------------------------------------------------------------------|
  |         xxx                                         result_data[7:0] 0| 50
  |-----------------------------------------------------------------------|
  |         xxx                                         result_data[7:0] 0| 51
  |-----------------------------------------------------------------------|

  func_i2c_cmdr_mm_reg_nof_dat() -->
         3*nof_protocols + 1 + 1 + nof_result_data_max = 3*16 + 1 + 1 + 2 = 52
"""

class UniBoardAduI2CCommander(FirmwareBlock):
    """ FirmwareBlock tests class """

    # Protocol commands 0 to 7 from i2c_commander_aduh_pkg
    CMD_READ_TEMP_WI              = 0
    CMD_SET_ADC_WI                = 1
    CMD_SET_ADC_TEST_MODE_WI      = 2
    CMD_SET_ATTENUATION_0_0dB_WI  = 3
    CMD_SET_ATTENUATION_1_0dB_WI  = 4
    CMD_SET_ATTENUATION_10_0dB_WI = 5
    CMD_SET_ATTENUATION_10_6dB_WI = 6
    CMD_SET_CALIBRATION_WI        = 7
    CMD_SAMPLE_SDA_WI             = 15

    # Timeouts in sec
    CMD_DEFAULT_TO                = 0.1
    CMD_BIT_BANG_TO               = 1.0

    # Result locations
    PROTOCOL_STATUS_WI            = 48
    RESULT_ERROR_CNT_WI           = 49
    RESULT_DATA_WI                = 50

    # Protocol commander status from i2c_commander_pkg
    CMDR_IDLE     = 0  # no protocol active
    CMDR_PENDING  = 1  # protocol pending by write event, but not yet activated by sync
    CMDR_BUSY     = 2  # protocol I2C accesses are busy
    CMDR_DONE     = 3  # protocol I2C accesses finished

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_adu_i2c_commander')
    @maxinstances(2)
    def __init__(self, board, **kwargs):
        """ UniBoardBsnSource initialiser
        :param board: Pointer to board instance
        """
        super(UniBoardAduI2CCommander, self).__init__(board)

        # Check if instance ID is in arguments
        if 'instance_id' not in kwargs.keys():
            raise PluginError("UniBoardAduI2CCommander: Instance id must be in arguments")
        self._instance_id = kwargs['instance_id']

        # Required register names
        self._reg_address      = "REG_ADU_I2C_COMMANDER_%s" % self._instance_id
        self._protocol_address = "RAM_ADU_I2C_PROTOCOL_%s"  % self._instance_id
        self._ram_address      = "RAM_ADU_I2C_RESULT_%s"    % self._instance_id


        # Get list of nodes
        if 'nodes' not in kwargs.keys():
            raise PluginError("UniBoardAduI2CCommander: List of nodes not specified")

        # Convert to list of nodes if required
        self._nodes = self.board._get_nodes(kwargs['nodes'])
        if type(self._nodes) is not list:
            self._nodes = [self._nodes]

        # Check if registers are available on all nodes
        for node in self._nodes:
            fpga_number = self.board.device_to_fpga(node)
            register_str = "fpga%d.%s" % (fpga_number, self._reg_address)
            if register_str % () not in self.board.register_list.keys():
                raise PluginError("UniBoardAduI2CCommander: Node %d does not have register %s" % (fpga_number, self._wg_register))

            register_str = "fpga%d.%s" % (fpga_number, self._protocol_address)
            if register_str % () not in self.board.register_list.keys():
                raise PluginError("UniBoardAduI2CCommander: Node %d does not have register %s" % (fpga_number, self._wg_ram))

            register_str = "fpga%d.%s" % (fpga_number, self._ram_address)
            if register_str % () not in self.board.register_list.keys():
                raise PluginError("UniBoardAduI2CCommander: Node %d does not have register %s" % (fpga_number, self._wg_ram))

    #######################################################################################

    def read_protocol_status(self):
        """ Read protocol status
        :return: protocol status
        """
        # Get the register data from the node(s)
        data = self.board.read_register(self._reg_address, offset = self.PROTOCOL_STATUS_WI, n = 1, device = self._nodes)
        return [ node_data[0] for (node, status, node_data) in data ]


        # Use dedicated method for a command that does read I2C data
    def read_temperature(self):
        """ Use dedicated method for a command that does read I2C data
        :return: temperature
        """
        # Write the register data to the node(s) and log the access status
        self.board.write_register(self._reg_address, 0, offset = self.CMD_READ_TEMP_WI, device = self._nodes)

        # Wait until the I2C access has finished on the node(s)
        time.sleep(self.CMD_DEFAULT_TO)

        # Get the register data from the node(s)
        data = self.board.read_register(self._reg_address, offset = self.PROTOCOL_STATUS_WI, n = 3, device = self._nodes)

        # Evaluate per node
        result = []
        for (node, status, node_data) in data:
            if node_data[0] != self.CMDR_DONE:
                raise PluginError("I2C access not finished (%d = %s" % (node_data[0], self.cmdr_status_to_str(node_data[0])))
            if node_data[1] != 0:
                raise PluginError("I2C access went wrong (result error cnt = %d" % node_data[1])
            result.append(node_data[2])
        return result


    def read_sample_sda(self):
        """ Use dedicated method for a command that does read I2C data """
                # Write the register data to the node(s) and log the access status
        self.board.write_register(self._reg_address, 0, offset = self.CMD_SAMPLE_SDA_WI, device = self._nodes)

        # Wait until the I2C access has finished on the node(s)
        time.sleep(self.CMD_DEFAULT_TO)

        # Get the register data from the node(s)
        data = self.board.read_register(self._reg_address, offset = self.PROTOCOL_STATUS_WI, n = 2, device = self._nodes)

        # Evaluate per node
        for (node, status, node_data) in data:
            if node_data[1] != 0:
                raise PluginError("Sampled SDA = '0' is wrong") # SDA is somehow forced to ground
            if node_data[0] != self.CMDR_DONE:
                raise PluginError("I2C access went wrong (result error cnt = %d" % node_data[1])


    def _do_wr_only_cmd(self, cmd_wi, cmd_str, cmd_to):
        """ Use general _do_wr_only_cmd for all commands that only write I2C and do not read I2C data """
        # Write the register data to the node(s)
        self.board.write_register(self._reg_address, 0, offset = cmd_wi, device = self._nodes)

        # Wait until the I2C access has finished on the node(s)
        time.sleep(cmd_to)

        # Get the register data from the node(s)
        data = self.board.read_register(self._reg_address, offset = self.PROTOCOL_STATUS_WI, n = 2, device = self._nodes)

        # Evaluate per node
        for (node, status, node_data) in data:
            if node_data[1] != 0:
                raise PluginError("I2C access went wrong (result error cnt = %d)" % node_data[1])
            if node_data[0] != self.CMDR_DONE:
                raise PluginError("I2C access not finished (%d = %s)" % (node_data[0], self.cmdr_status_to_str(node_data[0])))

    def write_set_adc(self):                self._do_wr_only_cmd(self.CMD_SET_ADC_WI,                'write set ADC',                     self.CMD_BIT_BANG_TO)
    def write_set_adc_test_mode(self):      self._do_wr_only_cmd(self.CMD_SET_ADC_TEST_MODE_WI,      'write set ADC test mode',           self.CMD_BIT_BANG_TO)
    def write_set_attenuation_0_0db(self):  self._do_wr_only_cmd(self.CMD_SET_ATTENUATION_0_0dB_WI,  'write set attenuation[0] = 0 dB',   self.CMD_DEFAULT_TO)
    def write_set_attenuation_1_0db(self):  self._do_wr_only_cmd(self.CMD_SET_ATTENUATION_1_0dB_WI,  'write set attenuation',             self.CMD_DEFAULT_TO)
    def write_set_attenuation_10_0db(self): self._do_wr_only_cmd(self.CMD_SET_ATTENUATION_10_0dB_WI, 'write set attenuation[1:0] = 0 dB', self.CMD_DEFAULT_TO)
    def write_set_attenuation_10_6db(self): self._do_wr_only_cmd(self.CMD_SET_ATTENUATION_10_6dB_WI, 'write set attenuation[1:0] = 6 dB', self.CMD_DEFAULT_TO)
    def write_set_calibration(self):        self._do_wr_only_cmd(self.CMD_SET_CALIBRATION_WI,        'write set calibration',             self.CMD_DEFAULT_TO)

    def read_result_ram(self, n = 10):
        # Get the memory data from the node(s)
        data = self.board.read_register(self._ram_address, n = n, device = self._nodes)
        return [node_data for (node, status, node_data) in data]

    def overwrite_result_ram(self, value = 13):
        # Write the memory data to the node(s)
        self.board.write_register(self._ram_address, 10 * [value], device = self._nodes)

    def read_protocol_ram(self, n = 10):
        # Get the memory data from the node(s)
        data = self.board.read_register(self._protocol_address, n = n, device = self._nodes)
        return [node_data for (node, status, node_data) in data]

    def write_protocol_ram(self, data):
        # Write the memory data to the node(s)
        self.board.write_register(self._protocol_address, data, device = self._nodes)

    def cmdr_status_to_str(self, status):
        """ Convert status to string
        :param status: Status
        :return: String representation
        """
        if status == self.CMDR_IDLE:
            status_str = 'no protocol active'
        elif status == self.CMDR_PENDING:
            status_str = 'protocol pending by write event, but not yet activated by sync'
        elif status == self.CMDR_BUSY:
            status_str = 'protocol I2C accesses are busy'
        elif status == self.CMDR_DONE:
            status_str = 'protocol I2C accesses finished'
        else:
            status_str = 'unknown status code'
        return status_str

    ##################### Superclass method implementations #################################

    def initialise(self):
        """ Initialise FirmwareTest """

        logging.info("UniBoardAduI2CCommander has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("UniBoardAduI2CCommander : Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("UniBoardAduI2CCommander : Cleaning up")
        return True
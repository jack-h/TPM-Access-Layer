#!/usr/bin/env python
# -*- coding:utf-8 -*- 


##############################################################################
## license :
##============================================================================
##
## File :        ROACH_DS.py
## 
## Project :     AAVS Tango ROACH Driver
##
## This file is part of Tango device class.
## 
## Tango is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## Tango is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
## 
## You should have received a copy of the GNU General Public License
## along with Tango.  If not, see <http://www.gnu.org/licenses/>.
## 
##
## $Author :      andrea.demarco$
##
## $Revision :    $
##
## $Date :        $
##
## $HeadUrl :     $
##============================================================================
##            This file is generated by POGO
##    (Program Obviously used to Generate tango Object)
##
##        (c) - Software Engineering Group - ESRF
##############################################################################

"""A Tango device server for the ROACH board."""

__all__ = ["ROACH_DS", "ROACH_DSClass", "main"]

__docformat__ = 'restructuredtext'

import PyTango
import sys
from FPGA_DS import FPGA_DS, FPGA_DSClass
# Add additional import
#----- PROTECTED REGION ID(ROACH_DS.additionnal_import) ENABLED START -----#
from pyfabil import Roach
from pyfabil import Device
from PyTango._PyTango import DevFailed
import pickle
import inspect
#----- PROTECTED REGION END -----#	//	ROACH_DS.additionnal_import

## Device States Description
## ON : Device is ON for alarm/event handling.
## ALARM : Device is ALARM for alarm/event handling.

class ROACH_DS (FPGA_DS):

    #--------- Add you global variables here --------------------------
    #----- PROTECTED REGION ID(ROACH_DS.global_variables) ENABLED START -----#
    
    #----- PROTECTED REGION END -----#	//	ROACH_DS.global_variables

    def __init__(self,cl, name):
        super(ROACH_DS,self).__init__(cl,name)
        self.debug_stream("In __init__()")
        ROACH_DS.init_device(self)
        #----- PROTECTED REGION ID(ROACH_DS.__init__) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	ROACH_DS.__init__
        
    def delete_device(self):
        self.debug_stream("In delete_device()")
        #----- PROTECTED REGION ID(ROACH_DS.delete_device) ENABLED START -----#
        super(ROACH_DS, self).delete_device()
        #----- PROTECTED REGION END -----#	//	ROACH_DS.delete_device

    def init_device(self):
        self.debug_stream("In init_device()")
        self.get_device_properties(self.get_device_class())
        self.attr_board_state_read = 0
        self.attr_is_programmed_read = False
        self.attr_ip_address_read = ''
        self.attr_port_read = 0
        #----- PROTECTED REGION ID(ROACH_DS.init_device) ENABLED START -----#
        self.fpga_instance = Roach()
        #----- PROTECTED REGION END -----#	//	ROACH_DS.init_device

    def always_executed_hook(self):
        self.debug_stream("In always_excuted_hook()")
        #----- PROTECTED REGION ID(ROACH_DS.always_executed_hook) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	ROACH_DS.always_executed_hook

    #-----------------------------------------------------------------------------
    #    ROACH_DS read/write attribute methods
    #-----------------------------------------------------------------------------
    
    def read_board_state(self, attr):
        self.debug_stream("In read_board_state()")
        #----- PROTECTED REGION ID(ROACH_DS.board_state_read) ENABLED START -----#
        #attr.set_value(self.attr_board_state_read)
        super(ROACH_DS, self).read_board_state(attr)
        #----- PROTECTED REGION END -----#	//	ROACH_DS.board_state_read
        
    def read_is_programmed(self, attr):
        self.debug_stream("In read_is_programmed()")
        #----- PROTECTED REGION ID(ROACH_DS.is_programmed_read) ENABLED START -----#
        #attr.set_value(self.attr_is_programmed_read)
        super(ROACH_DS, self).read_is_programmed(attr)
        #----- PROTECTED REGION END -----#	//	ROACH_DS.is_programmed_read
        
    def read_ip_address(self, attr):
        self.debug_stream("In read_ip_address()")
        #----- PROTECTED REGION ID(ROACH_DS.ip_address_read) ENABLED START -----#
        #attr.set_value(self.attr_ip_address_read)
        super(ROACH_DS, self).read_ip_address(attr)
        #----- PROTECTED REGION END -----#	//	ROACH_DS.ip_address_read
        
    def write_ip_address(self, attr):
        self.debug_stream("In write_ip_address()")
        data=attr.get_write_value()
        #----- PROTECTED REGION ID(ROACH_DS.ip_address_write) ENABLED START -----#
        super(ROACH_DS, self).write_ip_address(attr)
        #----- PROTECTED REGION END -----#	//	ROACH_DS.ip_address_write
        
    def read_port(self, attr):
        self.debug_stream("In read_port()")
        #----- PROTECTED REGION ID(ROACH_DS.port_read) ENABLED START -----#
        #attr.set_value(self.attr_port_read)
        super(ROACH_DS, self).read_port(attr)
        #----- PROTECTED REGION END -----#	//	ROACH_DS.port_read
        
    def write_port(self, attr):
        self.debug_stream("In write_port()")
        data=attr.get_write_value()
        #----- PROTECTED REGION ID(ROACH_DS.port_write) ENABLED START -----#
        super(ROACH_DS, self).write_port(attr)
        #----- PROTECTED REGION END -----#	//	ROACH_DS.port_write
        
    
    
        #----- PROTECTED REGION ID(ROACH_DS.initialize_dynamic_attributes) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	ROACH_DS.initialize_dynamic_attributes
            
    def read_attr_hardware(self, data):
        self.debug_stream("In read_attr_hardware()")
        #----- PROTECTED REGION ID(ROACH_DS.read_attr_hardware) ENABLED START -----#
        super(ROACH_DS, self).read_attr_hardware(data)
        #----- PROTECTED REGION END -----#	//	ROACH_DS.read_attr_hardware


    #-----------------------------------------------------------------------------
    #    ROACH_DS command methods
    #-----------------------------------------------------------------------------
    
    def add_command(self, argin):
        """ A generic command that adds a new command entry to the Tango device driver.
        
        :param argin: A string containing a dictionary for fields required for command creation.
        :type: PyTango.DevString
        :return: True if command creation was successful, false if not.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In add_command()")
        argout = False
        #----- PROTECTED REGION ID(ROACH_DS.add_command) ENABLED START -----#
        argout = super(ROACH_DS, self).add_command(argin)
        #----- PROTECTED REGION END -----#	//	ROACH_DS.add_command
        return argout
        
    def connect(self):
        """ Opens the connection to the device.
        
        :param : 
        :type: PyTango.DevVoid
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In connect()")
        #----- PROTECTED REGION ID(ROACH_DS.connect) ENABLED START -----#
        #super(ROACH_DS, self).connect()
        state_ok = self.check_state_flow(inspect.stack()[0][3])
        #state_ok = self.check_state_flow(self.connect.__name__)
        if state_ok:
            try:
                self.fpga_instance.connect(self.attr_ip_address_read, self.attr_port_read)
            except DevFailed as df:
                self.debug_stream("Failed to connect: %s" % df)
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	ROACH_DS.connect
        
    def create_scalar_attribute(self, argin):
        """ A method that creates a new scalar attribute.
        
        :param argin: New attribute name.
        :type: PyTango.DevString
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In create_scalar_attribute()")
        #----- PROTECTED REGION ID(ROACH_DS.create_scalar_attribute) ENABLED START -----#
        super(ROACH_DS, self).create_scalar_attribute(argin)
        #----- PROTECTED REGION END -----#	//	ROACH_DS.create_scalar_attribute
        
    def create_vector_attribute(self, argin):
        """ A method that creates a new vector attribute.
        
        :param argin: New attribute name.
        :type: PyTango.DevString
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In create_vector_attribute()")
        #----- PROTECTED REGION ID(ROACH_DS.create_vector_attribute) ENABLED START -----#
        super(ROACH_DS, self).create_vector_attribute(argin)
        #----- PROTECTED REGION END -----#	//	ROACH_DS.create_vector_attribute
        
    def disconnect(self):
        """ Disconnect this device.
        
        :param : 
        :type: PyTango.DevVoid
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In disconnect()")
        #----- PROTECTED REGION ID(ROACH_DS.disconnect) ENABLED START -----#
        super(ROACH_DS, self).disconnect()
        #----- PROTECTED REGION END -----#	//	ROACH_DS.disconnect
        
    def flush_attributes(self):
        """ A method that removes all attributes for the current firmware.
        
        :param : 
        :type: PyTango.DevVoid
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In flush_attributes()")
        #----- PROTECTED REGION ID(ROACH_DS.flush_attributes) ENABLED START -----#
        super(ROACH_DS, self).flush_attributes()
        #----- PROTECTED REGION END -----#	//	ROACH_DS.flush_attributes
        
    def generate_attributes(self):
        """ A method that generates dynamic attributes based on the current firmware.
        
        :param : 
        :type: PyTango.DevVoid
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In generate_attributes()")
        #----- PROTECTED REGION ID(ROACH_DS.generate_attributes) ENABLED START -----#
        super(ROACH_DS, self).generate_attributes()
        #----- PROTECTED REGION END -----#	//	ROACH_DS.generate_attributes
        
    def get_device_list(self):
        """ Returns a list of devices, as a serialized python dictionary, stored as a string.
        
        :param : 
        :type: PyTango.DevVoid
        :return: Dictionary of devices.
        :rtype: PyTango.DevString """
        self.debug_stream("In get_device_list()")
        argout = ''
        #----- PROTECTED REGION ID(ROACH_DS.get_device_list) ENABLED START -----#
        argout = super(ROACH_DS, self).get_device_list()
        #----- PROTECTED REGION END -----#	//	ROACH_DS.get_device_list
        return argout
        
    def get_firmware_list(self, argin):
        """ Returns a list of firmwares, as a serialized python dictionary, stored as a string.
        
        :param argin: Device on board to get list of firmware, as a string.
        :type: PyTango.DevString
        :return: Dictionary of firmwares on the board.
        :rtype: PyTango.DevString """
        self.debug_stream("In get_firmware_list()")
        argout = ''
        #----- PROTECTED REGION ID(ROACH_DS.get_firmware_list) ENABLED START -----#
        state_ok = self.check_state_flow(inspect.stack()[0][3])
        if state_ok:
            try:
                arguments = pickle.loads(argin)
                device = arguments['device']
                if device is None:
                    firmware_list = self.fpga_instance.get_firmware_list()
                else:
                    firmware_list = self.fpga_instance.get_firmware_list(Device(device))

                argout = pickle.dumps(firmware_list)
            except DevFailed as df:
                self.debug_stream("Failed to get firmware list: %s" % df)
                argout = ''
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	ROACH_DS.get_firmware_list
        return argout
        
    def get_register_info(self, argin):
        """ Gets a dictionary of information associated with a specified register.
        
        :param argin: The register name for which information will be retrieved.
        :type: PyTango.DevString
        :return: Returns a string-encoded dictionary of information.
        :rtype: PyTango.DevString """
        self.debug_stream("In get_register_info()")
        argout = ''
        #----- PROTECTED REGION ID(ROACH_DS.get_register_info) ENABLED START -----#
        argout = super(ROACH_DS, self).get_register_info(argin)
        #----- PROTECTED REGION END -----#	//	ROACH_DS.get_register_info
        return argout
        
    def get_register_list(self):
        """ Returns a list of registers and values, as a serialized python dictionary, stored as a string.
        
        :param : 
        :type: PyTango.DevVoid
        :return: List of register names.
        :rtype: PyTango.DevVarStringArray """
        self.debug_stream("In get_register_list()")
        argout = ['']
        #----- PROTECTED REGION ID(ROACH_DS.get_register_list) ENABLED START -----#
        state_ok = self.check_state_flow(inspect.stack()[0][3])
        if state_ok:
            try:
                register_dict = self.fpga_instance.get_register_list()
                argout = register_dict.keys()
            except DevFailed as df:
                self.debug_stream("Failed to get register list: %s" % df)
                argout = ''
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	ROACH_DS.get_register_list
        return argout
        
    def load_firmware(self, argin):
        """ Call to load firmware.
        
        :param argin: File path.
        :type: PyTango.DevString
        :return: Return true if successful.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In load_firmware()")
        argout = False
        #----- PROTECTED REGION ID(ROACH_DS.load_firmware) ENABLED START -----#
        state_ok = self.check_state_flow(inspect.stack()[0][3])
        if state_ok:
            arguments = pickle.loads(argin)
            filepath = arguments['path']
            self.flush_attributes()
            try:
                self.fpga_instance.load_firmware(filepath)
                self.generate_attributes()
                self.attr_is_programmed_read = True
                self.info_stream("Firmware loaded.")
                argout = True
            except DevFailed as df:
                self.debug_stream("Failed to load firmware: %s" % df)
                self.attr_is_programmed_read = False
                self.flush_attributes()
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	ROACH_DS.load_firmware
        return argout
        
    def load_plugin(self, argin):
        """ Loads a plugin in device server.
        
        :param argin: Name of plugin. Case sensitive.
        :type: PyTango.DevString
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In load_plugin()")
        #----- PROTECTED REGION ID(ROACH_DS.load_plugin) ENABLED START -----#
        super(ROACH_DS, self).load_plugin(argin)
        #----- PROTECTED REGION END -----#	//	ROACH_DS.load_plugin
        
    def read_address(self, argin):
        """ Reads values from a register location. Instead of a register name, the actual physical address has to be provided.
        
        :param argin: Associated register information.
        :type: PyTango.DevString
        :return: Register values.
        :rtype: PyTango.DevVarULongArray """
        self.debug_stream("In read_address()")
        argout = [0]
        #----- PROTECTED REGION ID(ROACH_DS.read_address) ENABLED START -----#
        state_ok = self.check_state_flow(inspect.stack()[0][3])
        if state_ok:
            arguments = pickle.loads(argin)
            address = arguments['address']
            words = arguments['words']
            try:
                argout = self.fpga_instance.read_address(address, words)
            except DevFailed as df:
                self.debug_stream("Failed to read address: %s" % df)
                argout = ''
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	ROACH_DS.read_address
        return argout
        
    def read_device(self, argin):
        """ Get device value.
        
        :param argin: 
            String containing:
            1) SPI Device to read from
            2) Address on device to read from
        :type: PyTango.DevString
        :return: Value of device.
        :rtype: PyTango.DevULong """
        self.debug_stream("In read_device()")
        argout = 0
        #----- PROTECTED REGION ID(ROACH_DS.read_device) ENABLED START -----#
        state_ok = self.check_state_flow(inspect.stack()[0][3])
        if state_ok:
            arguments = pickle.loads(argin)
            device = arguments['device']
            address = arguments['address']
            try:
                argout = self.fpga_instance.read_device(device, address)
            except DevFailed as df:
                self.debug_stream("Failed to read device: %s" % df)
                argout = 0
        else:
           self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	ROACH_DS.read_device
        return argout
        
    def read_register(self, argin):
        """ Reads values from a register location.
        
        :param argin: Associated register information.
        :type: PyTango.DevString
        :return: Register values.
        :rtype: PyTango.DevVarULongArray """
        self.debug_stream("In read_register()")
        argout = [0]
        #----- PROTECTED REGION ID(ROACH_DS.read_register) ENABLED START -----#
        state_ok = self.check_state_flow(inspect.stack()[0][3])
        if state_ok:
            arguments = pickle.loads(argin)
            register = arguments['register']
            words = arguments['words']
            offset = arguments['offset']

            reg_info = pickle.loads(self.get_register_info(register))
            self.info_stream("Reg info: %s" % reg_info)
            length_register = reg_info['size']
            if words+offset <= length_register:
                try:
                    self.debug_stream("Register: %s" % register)
                    self.debug_stream("Words: %s" % words)
                    self.debug_stream("Offset: %s" % offset)
                    if words or offset is None:
                        argout = self.fpga_instance.read_register(register)
                    else:
                        argout = self.fpga_instance.read_register(register, words, offset)
                except DevFailed as df:
                    self.debug_stream("Failed to read register: %s" % df)
                    argout = [0]
            else:
                self.info_stream("Register size limit exceeded, no values read.")
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	ROACH_DS.read_register
        return argout
        
    def remove_command(self, argin):
        """ A generic command that removes a command entry from the Tango device driver.
        
        :param argin: Command name.
        :type: PyTango.DevString
        :return: True if command removal was successful, false otherwise.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In remove_command()")
        argout = False
        #----- PROTECTED REGION ID(ROACH_DS.remove_command) ENABLED START -----#
        argout = super(ROACH_DS, self).remove_command(argin)
        #----- PROTECTED REGION END -----#	//	ROACH_DS.remove_command
        return argout
        
    def run_plugin_command(self, argin):
        """ Proxy to run a particular plugin command.
        
        :param argin: Dictionary with name of command to run, and arguments.
        :type: PyTango.DevString
        :return: Any output from the command.
        :rtype: PyTango.DevString """
        self.debug_stream("In run_plugin_command()")
        argout = ''
        #----- PROTECTED REGION ID(ROACH_DS.run_plugin_command) ENABLED START -----#
        argout = super(ROACH_DS, self).run_plugin_command(argin)
        #----- PROTECTED REGION END -----#	//	ROACH_DS.run_plugin_command
        return argout
        
    def set_attribute_levels(self, argin):
        """ Set alarm levels for a particular attribute.
        1) min_value : (str) minimum allowed value
        2 )max_value : (str) maximum allowed value
        3) min_alarm : (str) low alarm level
        4) max_alarm : (str) high alarm level
        
        :param argin: A pickled string storing a dictionary with the required alarm levels, and name of attribute.
        :type: PyTango.DevString
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In set_attribute_levels()")
        #----- PROTECTED REGION ID(ROACH_DS.set_attribute_levels) ENABLED START -----#
        super(ROACH_DS, self).set_attribute_levels(argin)
        #----- PROTECTED REGION END -----#	//	ROACH_DS.set_attribute_levels
        
    def set_board_state(self, argin):
        """ Sets the board status by passing in a value.
                UNKNOWN	=  0
                INIT		=  1
                ON		=  2
                RUNNING	=  3
                FAULT		=  4
                OFF		=  5
                STANDBY	=  6
                SHUTTING_DOWN	=  7
                MAINTENANCE	=  8
                LOW_POWER	=  9
                SAFE_STATE	=  10
        
        :param argin: Board status value.
        :type: PyTango.DevLong
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In set_board_state()")
        #----- PROTECTED REGION ID(ROACH_DS.set_board_state) ENABLED START -----#
        super(ROACH_DS, self).set_board_state(argin)
        #----- PROTECTED REGION END -----#	//	ROACH_DS.set_board_state
        
    def write_address(self, argin):
        """ Writes values to a register location. The actual physical address has to be provided.
        
        :param argin: Associated register information.
        :type: PyTango.DevString
        :return: True if successful, false if not.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In write_address()")
        argout = False
        #----- PROTECTED REGION ID(ROACH_DS.write_address) ENABLED START -----#
        state_ok = self.check_state_flow(inspect.stack()[0][3])
        if state_ok:
            arguments = pickle.loads(argin)
            address = arguments['address']
            values = arguments['values']
            try:
                argout = self.fpga_instance.write_address(address, values)
            except DevFailed as df:
                self.debug_stream("Failed to write address: %s" % df)
                argout = False
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	ROACH_DS.write_address
        return argout
        
    def write_device(self, argin):
        """ Set device value.
        
        :param argin: 
            A string containing the following:
            1) SPI device to write to
            2) Address on device to write to
            3) Value to write
        :type: PyTango.DevString
        :return: True if successful, false if not.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In write_device()")
        argout = False
        #----- PROTECTED REGION ID(ROACH_DS.write_device) ENABLED START -----#
        state_ok = self.check_state_flow(inspect.stack()[0][3])
        if state_ok:
            arguments = pickle.loads(argin)
            device = arguments['device']
            address = arguments['address']
            value = arguments['value']
            try:
                argout = self.fpga_instance.write_device(device, address, value)
            except DevFailed as df:
                self.debug_stream("Failed to write device: %s" % df)
                argout = False
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	ROACH_DS.write_device
        return argout
        
    def write_register(self, argin):
        """ Writes values from a register location.
        
        :param argin: Associated register information.
        :type: PyTango.DevString
        :return: True if successful, false if not.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In write_register()")
        argout = False
        #----- PROTECTED REGION ID(ROACH_DS.write_register) ENABLED START -----#
        state_ok = self.check_state_flow(inspect.stack()[0][3])
        if state_ok:
            arguments = pickle.loads(argin)
            register = arguments['register']
            values = arguments['values']
            offset = arguments['offset']

            reg_info = pickle.loads(self.get_register_info(register))
            length_register = reg_info['size']
            length_values = len(values)
            if length_values+offset <= length_register:
                try:
                    if values or offset is None:
                        argout = self.fpga_instance.write_register(register)
                    else:
                        argout = self.fpga_instance.write_register(register, values, offset)
                    argout = True
                except DevFailed as df:
                    self.debug_stream("Failed to write register: %s" % df)
                    argout = False
            else:
                self.info_stream("Register size limit exceeded, no changes committed.")
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	ROACH_DS.write_register
        return argout
        
    def sink_alarm_state(self):
        """ This method is designed to turn off the device alarm state. It however, the cause that triggers an alarm is still present, alarm will turn back on.
        
        :param : 
        :type: PyTango.DevVoid
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In sink_alarm_state()")
        #----- PROTECTED REGION ID(ROACH_DS.sink_alarm_state) ENABLED START -----#
        super(ROACH_DS, self).sink_alarm_state()
        #----- PROTECTED REGION END -----#	//	ROACH_DS.sink_alarm_state
        

    #----- PROTECTED REGION ID(ROACH_DS.programmer_methods) ENABLED START -----#
    
    #----- PROTECTED REGION END -----#	//	ROACH_DS.programmer_methods

class ROACH_DSClass(FPGA_DSClass):
    #--------- Add you global class variables here --------------------------
    #----- PROTECTED REGION ID(ROACH_DS.global_class_variables) ENABLED START -----#
    
    #----- PROTECTED REGION END -----#	//	ROACH_DS.global_class_variables

    def dyn_attr(self, dev_list):
        """Invoked to create dynamic attributes for the given devices.
        Default implementation calls
        :meth:`ROACH_DS.initialize_dynamic_attributes` for each device
    
        :param dev_list: list of devices
        :type dev_list: :class:`PyTango.DeviceImpl`"""
    
        for dev in dev_list:
            try:
                dev.initialize_dynamic_attributes()
            except:
                import traceback
                dev.warn_stream("Failed to initialize dynamic attributes")
                dev.debug_stream("Details: " + traceback.format_exc())
        #----- PROTECTED REGION ID(ROACH_DS.dyn_attr) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	ROACH_DS.dyn_attr

    #    Class Properties
    class_property_list = {
        }
    class_property_list.update(FPGA_DSClass.class_property_list)


    #    Device Properties
    device_property_list = {
        }
    device_property_list.update(FPGA_DSClass.device_property_list)


    #    Command definitions
    cmd_list = {
        'add_command':
            [[PyTango.DevString, "A string containing a dictionary for fields required for command creation."],
            [PyTango.DevBoolean, "True if command creation was successful, false if not."]],
        'connect':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevVoid, "none"]],
        'create_scalar_attribute':
            [[PyTango.DevString, "New attribute name."],
            [PyTango.DevVoid, "none"]],
        'create_vector_attribute':
            [[PyTango.DevString, "New attribute name."],
            [PyTango.DevVoid, "none"]],
        'disconnect':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevVoid, "none"]],
        'flush_attributes':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevVoid, "none"]],
        'generate_attributes':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevVoid, "none"]],
        'get_device_list':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevString, "Dictionary of devices."]],
        'get_firmware_list':
            [[PyTango.DevString, "Device on board to get list of firmware, as a string."],
            [PyTango.DevString, "Dictionary of firmwares on the board."]],
        'get_register_info':
            [[PyTango.DevString, "The register name for which information will be retrieved."],
            [PyTango.DevString, "Returns a string-encoded dictionary of information."]],
        'get_register_list':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevVarStringArray, "List of register names."]],
        'load_firmware':
            [[PyTango.DevString, "File path."],
            [PyTango.DevBoolean, "Return true if successful."]],
        'load_plugin':
            [[PyTango.DevString, "Name of plugin. Case sensitive."],
            [PyTango.DevVoid, "none"]],
        'read_address':
            [[PyTango.DevString, "Associated register information."],
            [PyTango.DevVarULongArray, "Register values."]],
        'read_device':
            [[PyTango.DevString, "String containing:\n1) SPI Device to read from\n2) Address on device to read from"],
            [PyTango.DevULong, "Value of device."]],
        'read_register':
            [[PyTango.DevString, "Associated register information."],
            [PyTango.DevVarULongArray, "Register values."]],
        'remove_command':
            [[PyTango.DevString, "Command name."],
            [PyTango.DevBoolean, "True if command removal was successful, false otherwise."]],
        'run_plugin_command':
            [[PyTango.DevString, "Dictionary with name of command to run, and arguments."],
            [PyTango.DevString, "Any output from the command."]],
        'set_attribute_levels':
            [[PyTango.DevString, "A pickled string storing a dictionary with the required alarm levels, and name of attribute."],
            [PyTango.DevVoid, "none"]],
        'set_board_state':
            [[PyTango.DevLong, "Board status value."],
            [PyTango.DevVoid, "none"]],
        'write_address':
            [[PyTango.DevString, "Associated register information."],
            [PyTango.DevBoolean, "True if successful, false if not."]],
        'write_device':
            [[PyTango.DevString, "A string containing the following:\n1) SPI device to write to\n2) Address on device to write to\n3) Value to write"],
            [PyTango.DevBoolean, "True if successful, false if not."]],
        'write_register':
            [[PyTango.DevString, "Associated register information."],
            [PyTango.DevBoolean, "True if successful, false if not."]],
        'sink_alarm_state':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevVoid, "none"]],
        }
    cmd_list.update(FPGA_DSClass.cmd_list)


    #    Attribute definitions
    attr_list = {
        'board_state':
            [[PyTango.DevLong,
            PyTango.SCALAR,
            PyTango.READ]],
        'is_programmed':
            [[PyTango.DevBoolean,
            PyTango.SCALAR,
            PyTango.READ]],
        'ip_address':
            [[PyTango.DevString,
            PyTango.SCALAR,
            PyTango.READ_WRITE]],
        'port':
            [[PyTango.DevULong,
            PyTango.SCALAR,
            PyTango.READ_WRITE]],
        }
    attr_list.update(FPGA_DSClass.attr_list)


def main():
    try:
        py = PyTango.Util(sys.argv)
        py.add_class(ROACH_DSClass,ROACH_DS,'ROACH_DS')
        #----- PROTECTED REGION ID(ROACH_DS.add_classes) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	ROACH_DS.add_classes

        U = PyTango.Util.instance()
        U.server_init()
        U.server_run()

    except PyTango.DevFailed,e:
        print '-------> Received a DevFailed exception:',e
    except Exception,e:
        print '-------> An unforeseen exception occured....',e

if __name__ == '__main__':
    main()

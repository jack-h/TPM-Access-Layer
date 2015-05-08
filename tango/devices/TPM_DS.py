#!/usr/bin/env python
# -*- coding:utf-8 -*- 


##############################################################################
## license :
##============================================================================
##
## File :        TPM_DS.py
## 
## Project :     AAVS Tango TPM Driver
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

"""A Tango device server for the TPM board."""

__all__ = ["TPM_DS", "TPM_DSClass", "main"]

__docformat__ = 'restructuredtext'

import PyTango
import sys
# Add additional import
#----- PROTECTED REGION ID(TPM_DS.additionnal_import) ENABLED START -----#
from PyTango import Util, Attr, SpectrumAttr
from PyTango._PyTango import DevFailed
from accesslayer import *
from definitions import *
from types import *
import pickle
#----- PROTECTED REGION END -----#	//	TPM_DS.additionnal_import

## Device States Description
## No states for this device

class TPM_DS (PyTango.Device_4Impl):

    #--------- Add you global variables here --------------------------
    #----- PROTECTED REGION ID(TPM_DS.global_variables) ENABLED START -----#
    #### global tpm_instance
    #### tpm_instance = None

    all_states_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    plugin_cmd_list = {}

    # State flow definitions - allowed states for each command
    state_list = {
        'loadFirmwareBlocking': all_states_list,
        'getRegisterList': all_states_list,
        'getDeviceList': all_states_list,
        'Connect': all_states_list,
        'Disconnect': all_states_list,
        'getFirmwareList': all_states_list,
        'getRegisterInfo': all_states_list,
        'createScalarAttribute': all_states_list,
        'createVectorAttribute': all_states_list,
        'readRegister': all_states_list,
        'writeRegister': all_states_list,
        'generateAttributes': all_states_list,
        'flushAttributes': all_states_list,
        'readAddress': all_states_list,
        'writeAddress': all_states_list,
        'readDevice': all_states_list,
        'writeDevice': all_states_list,
        'setBoardState': all_states_list,
        'addCommand': all_states_list,
        'removeCommand': all_states_list
    }

    def callPluginCommand(self, argin = None):
        """ This method is responsible for calling a command from attached plugins.
        The input to this command has to include a set of arguments required by the command to be called.

        :param argin: A pickled dictionary with required arguments.
        :type: PyTango.DevString
        :return:
            Any output of the called command.
            An empty dictionary is returned for commands with no returned values.
        :rtype: PyTango.DevString """
        self.debug_stream("In callPluginCommand()")
        argout = None

        arguments = pickle.loads(argin)
        command_name = arguments['fnName']
        arginput = arguments['fnInput']

        #self.info_stream("Inspecting stack...")
        #self.info_stream(inspect.stack()[2][3])
        #command_name = inspect.stack()[2][3]
        if command_name in self.plugin_cmd_list:
            self.info_stream("Called existent command: %s" % command_name)
            state_ok = self.checkStateFlow(command_name)
            if state_ok:
                try:
                    argin_dict = pickle.loads(arginput)
                    #self.info_stream("Input to command: %s" % argin_dict)
                    if argin_dict:
                        #self.info_stream("Call with parameters")
                        argout = getattr(self.tpm_instance, command_name)(arginput)
                    else:
                        #self.info_stream("Call without parameters")
                        argout = getattr(self.tpm_instance, command_name)()
                except DevFailed as df:
                    self.info_stream("Failed to run plugin command: %s" % df)
                    argout = ''
            else:
                self.debug_stream("Invalid state")
        else:
            self.debug_stream("Called non-existent command")
        return argout

    def checkStateFlow(self, fnName):
        """ Checks if the current state the device is in one of the states in a given list of allowed states for a paticular function.
        :param : Name of command to be executed
        :type: String
        :return: True if allowed, false if not.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In checkStateFlow()")
        # get allowed states for this command
        fnAllowedStates = self.state_list[fnName]
        allowed = self.attr_boardState_read in fnAllowedStates
        self.info_stream("Current state allowed: %s" % allowed)
        return allowed

    def getDevice(self, name):
        """ Extract device name from provided register name, if present """
        try:
            device = name.split('.')[0].upper()
            if device == "BOARD":
                return Device.Board
            elif device == "FPGA1":
                return Device.FPGA_1
            elif device == "FPGA2":
                return Device.FPGA_2
            else:
                return None
        except:
            return None

    def read_GeneralScalar(self, attr):
        """ A method that reads from a scalar attribute.

        :param attr: The attribute to read from.
        :type: PyTango.DevAttr
        :return: The read data.
        :rtype: PyTango.DevULong """
        self.info_stream("Reading attribute %s", attr.get_name())
        arguments = {}
        dev = self.getDevice(attr.get_name())
        arguments['device'] = dev.value
        arguments['register'] = attr.get_name()
        arguments['words'] = 1
        arguments['offset'] = 0
        args = str(arguments)
        values_array = self.readRegister(args)  #get actual value by reading from register
        attr.set_value(values_array[0]) # readRegister returns an array, so a scalar requires a read from 0'th location

    def write_GeneralScalar(self, attr):
        """ A method that writes to a scalar attribute.

        :param attr: The attribute to write to.
        :type: PyTango.DevAttr
        :return: Success or failure.
        :rtype: PyTango.DevBoolean """
        self.info_stream("Writing attribute %s", attr.get_name())
        data = attr.get_write_value()
        arguments = {}
        dev = self.getDevice(attr.get_name())
        arguments['device'] = dev.value
        arguments['register'] = attr.get_name()
        arguments['offset'] = 0
        arguments['values'] = data
        args = str(arguments)
        self.writeRegister(args)

    def read_GeneralVector(self, attr):
        """ A method that reads from a scalar attribute.

        :param attr: The attribute to read from.
        :type: PyTango.DevAttr
        :return: The read data.
        :rtype: PyTango.DevVarULongArray """
        self.info_stream("Reading attribute %s", attr.get_name())
        arguments = {}
        dev = self.getDevice(attr.get_name())
        arguments['device'] = dev.value
        arguments['register'] = attr.get_name()
        arguments['words'] = 1
        arguments['offset'] = 0
        args = str(arguments)
        values_array = self.readRegister(args)  #get actual values by reading from register
        attr.set_value(values_array) # readRegister returns an array

    def write_GeneralVector(self, attr):
        """ A method that writes to a vector attribute.

        :param attr: The attribute to write to.
        :type: PyTango.DevAttr
        :return: Success or failure.
        :rtype: PyTango.DevBoolean """
        self.info_stream("Writting attribute %s", attr.get_name())
        data = attr.get_write_value()
        arguments = {}
        dev = self.getDevice(attr.get_name())
        arguments['device'] = dev.value
        arguments['register'] = attr.get_name()
        arguments['offset'] = 0
        arguments['values'] = data
        args = str(arguments)
        self.writeRegister(args)

    #----- PROTECTED REGION END -----#	//	TPM_DS.global_variables

    def __init__(self,cl, name):
        PyTango.Device_4Impl.__init__(self,cl,name)
        self.debug_stream("In __init__()")
        TPM_DS.init_device(self)
        #----- PROTECTED REGION ID(TPM_DS.__init__) ENABLED START -----#
        #self.tpm_instance = None
        #----- PROTECTED REGION END -----#	//	TPM_DS.__init__
        
    def delete_device(self):
        self.debug_stream("In delete_device()")
        #----- PROTECTED REGION ID(TPM_DS.delete_device) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	TPM_DS.delete_device

    def init_device(self):
        self.debug_stream("In init_device()")
        self.get_device_properties(self.get_device_class())
        self.attr_boardState_read = 0
        self.attr_isProgrammed_read = False
        #----- PROTECTED REGION ID(TPM_DS.init_device) ENABLED START -----#
        self.info_stream("Starting device initialization...")
        self.setBoardState(BoardState.Init.value)
        self.tpm_instance = TPM()
        connect_args = pickle.dumps({'ip': "127.0.0.1", 'port': 10000})
        self.Connect(connect_args)
        #self.tpm_instance = TPM(ip="127.0.0.1", port=10000)

        print self.tpm_instance.getAvailablePlugins()
        self.tpm_instance.loadPlugin('FirmwareTest')
        plugins_dict = self.tpm_instance.getLoadedPlugins()

        #iterate on plugins
        for plugin in plugins_dict:
            for command in plugins_dict[plugin]:
                arguments = {}
                arguments['commandName'] = command
                arguments['inDesc'] = ''
                arguments['outDesc'] = ''
                arguments['states'] = self.all_states_list
                args = pickle.dumps(arguments)
                result = self.addCommand(args)
                if result == True:
                    self.info_stream("Command [%s].[%s] created successfully in device server." % (plugin, command))
                    self.__dict__[command] = lambda input: self.callPluginCommand(input)
                else:
                    self.info_stream("Command [%s].[%s] not created" % command)

        self.info_stream("Device has been initialized.")
        #----- PROTECTED REGION END -----#	//	TPM_DS.init_device

    def always_executed_hook(self):
        self.debug_stream("In always_excuted_hook()")
        #----- PROTECTED REGION ID(TPM_DS.always_executed_hook) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	TPM_DS.always_executed_hook

    #-----------------------------------------------------------------------------
    #    TPM_DS read/write attribute methods
    #-----------------------------------------------------------------------------
    
    def read_boardState(self, attr):
        self.debug_stream("In read_boardState()")
        #----- PROTECTED REGION ID(TPM_DS.boardState_read) ENABLED START -----#
        attr.set_value(self.attr_boardStatus_read)
        #----- PROTECTED REGION END -----#	//	TPM_DS.boardState_read
        
    def read_isProgrammed(self, attr):
        self.debug_stream("In read_isProgrammed()")
        #----- PROTECTED REGION ID(TPM_DS.isProgrammed_read) ENABLED START -----#
        attr.set_value(self.attr_isProgrammed_read)
        
        #----- PROTECTED REGION END -----#	//	TPM_DS.isProgrammed_read
        
    
    
        #----- PROTECTED REGION ID(TPM_DS.initialize_dynamic_attributes) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	TPM_DS.initialize_dynamic_attributes
            
    def read_attr_hardware(self, data):
        self.debug_stream("In read_attr_hardware()")
        #----- PROTECTED REGION ID(TPM_DS.read_attr_hardware) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	TPM_DS.read_attr_hardware


    #-----------------------------------------------------------------------------
    #    TPM_DS command methods
    #-----------------------------------------------------------------------------
    
    def Connect(self, argin):
        """ Opens the connection to the device.
        
        :param argin: Device IP address and port number.
        :type: PyTango.DevString
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In Connect()")
        #----- PROTECTED REGION ID(TPM_DS.Connect) ENABLED START -----#
        #state_ok = self.checkStateFlow("Connect")
        state_ok = self.checkStateFlow(self.Connect.__name__)
        if state_ok:
            arguments = pickle.loads(argin)
            #arguments = eval(argin)
            ip_str = arguments['ip']
            port = arguments['port']
            self.tpm_instance.connect(ip_str, port)
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	TPM_DS.Connect
        
    def Disconnect(self):
        """ Disconnect this device.
        
        :param : 
        :type: PyTango.DevVoid
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In Disconnect()")
        #----- PROTECTED REGION ID(TPM_DS.Disconnect) ENABLED START -----#
        state_ok = self.checkStateFlow(self.Connect.__name__)
        if state_ok:
            self.tpm_instance.disconnect()
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	TPM_DS.Disconnect
        
    def addCommand(self, argin):
        """ A generic command that adds a new command entry to the Tango device driver.
        
        :param argin: A string containing a dictionary for fields required for command creation.
        :type: PyTango.DevString
        :return: True if command creation was successful, false if not.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In addCommand()")
        argout = False
        #----- PROTECTED REGION ID(TPM_DS.addCommand) ENABLED START -----#
        state_ok = self.checkStateFlow(self.addCommand.__name__)
        if state_ok:
            #  Protect the script from exceptions raised by Tango
            try:
                # Try create a new command entry
                arguments = pickle.loads(argin)
                commandName = arguments['commandName']
                inDesc = arguments['inDesc']
                outDesc = arguments['outDesc']
                allowedStates = arguments['states']

                self.state_list[commandName] = allowedStates
                self.plugin_cmd_list[commandName] = [[PyTango.DevString, inDesc], [PyTango.DevString, outDesc]]
                #self.cmd_list[commandName] = [[PyTango.DevString, inDesc], [PyTango.DevString, outDesc]]
                argout = True
            except DevFailed as df:
                self.debug_stream("Failed to create new command entry in device server: \n%s" % df)
                argout = False
            finally:
                return argout
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	TPM_DS.addCommand
        return argout
        
    def createScalarAttribute(self, argin):
        """ A method that creates a new scalar attribute.
        
        :param argin: New attribute name.
        :type: PyTango.DevString
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In createScalarAttribute()")
        #----- PROTECTED REGION ID(TPM_DS.createScalarAttribute) ENABLED START -----#
        state_ok = self.checkStateFlow(self.createScalarAttribute.__name__)
        if state_ok:
            attr = Attr(argin, PyTango.DevULong)
            self.add_attribute(attr, self.read_GeneralScalar, self.write_GeneralScalar)
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	TPM_DS.createScalarAttribute
        
    def createVectorAttribute(self, argin):
        """ A method that creates a new vector attribute.
        
        :param argin: Name and size of vector attribute.
        :type: PyTango.DevString
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In createVectorAttribute()")
        #----- PROTECTED REGION ID(TPM_DS.createVectorAttribute) ENABLED START -----#
        arguments = pickle.loads(argin)
        name = arguments['name']
        length = arguments['length']
        state_ok = self.checkStateFlow(self.createVectorAttribute.__name__)
        if state_ok:
            attr = SpectrumAttr(name, PyTango.DevULong, PyTango.READ_WRITE, length)
            self.add_attribute(attr, self.read_GeneralVector, self.write_GeneralVector)
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	TPM_DS.createVectorAttribute
        
    def flushAttributes(self):
        """ A method that removes all attributes for the current firmware.
        
        :param : 
        :type: PyTango.DevVoid
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In flushAttributes()")
        #----- PROTECTED REGION ID(TPM_DS.flushAttributes) ENABLED START -----#
        state_ok = self.checkStateFlow(self.flushAttributes.__name__)
        if state_ok:
            if self.attr_isProgrammed_read:
                register_dict = self.tpm_instance.getRegisterList()
                if not register_dict: #if dict is empty
                    for reg_name, entries in register_dict.iteritems():
                        self.remove_attribute(reg_name)
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	TPM_DS.flushAttributes
        
    def generateAttributes(self):
        """ A method that generates dynamic attributes based on the current firmware.
        
        :param : 
        :type: PyTango.DevVoid
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In generateAttributes()")
        #----- PROTECTED REGION ID(TPM_DS.generateAttributes) ENABLED START -----#
        state_ok = self.checkStateFlow(self.generateAttributes.__name__)
        if state_ok:
            register_dict = self.tpm_instance.getRegisterList()
            for reg_name, entries in register_dict.iteritems():
                size = entries.get('size')
                #print reg_name, size
                if size > 1:
                    args = {'name': reg_name, 'length': size}
                    self.createVectorAttribute(pickle.dumps(args))
                else:
                    self.createScalarAttribute(reg_name)
            else:
                self.debug_stream("Invalid state")

    def getDeviceList(self):
        """ Returns a list of devices, as a serialized python dictionary, stored as a string.
        
        :param : 
        :type: PyTango.DevVoid
        :return: Dictionary of devices.
        :rtype: PyTango.DevString """
        self.debug_stream("In getDeviceList()")
        argout = ''
        #----- PROTECTED REGION ID(TPM_DS.getDeviceList) ENABLED START -----#
        state_ok = self.checkStateFlow(self.getDeviceList.__name__)
        if state_ok:
            devlist = self.tpm_instance.getDeviceList()
            argout = pickle.dumps(devlist)
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	TPM_DS.getDeviceList
        
    def getDeviceList(self):
        """ Returns a list of devices, as a serialized python dictionary, stored as a string.
        
        :param : 
        :type: PyTango.DevVoid
        :return: Dictionary of devices.
        :rtype: PyTango.DevString """
        self.debug_stream("In getDeviceList()")
        argout = ''
        #----- PROTECTED REGION ID(TPM_DS.getDeviceList) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	TPM_DS.getDeviceList
        return argout
        
    def getFirmwareList(self, argin):
        """ Returns a list of firmwares, as a serialized python dictionary, stored as a string.
        
        :param argin: Device on board to get list of firmware, as a string.
        :type: PyTango.DevString
        :return: Dictionary of firmwares on the board.
        :rtype: PyTango.DevString """
        self.debug_stream("In getFirmwareList()")
        argout = ''
        #----- PROTECTED REGION ID(TPM_DS.getFirmwareList) ENABLED START -----#
        state_ok = self.checkStateFlow(self.getFirmwareList.__name__)
        if state_ok:
            arguments = pickle.loads(argin)
            device = arguments['device']
            firmware_list = self.tpm_instance.getFirmwareList(Device(device))
            argout = pickle.dumps(firmware_list)
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	TPM_DS.getFirmwareList
        return argout
        
    def getRegisterInfo(self, argin):
        """ Gets a dictionary of information associated with a specified register.
        
        :param argin: The register name for which information will be retrieved.
        :type: PyTango.DevString
        :return: Returns a string-encoded dictionary of information.
        :rtype: PyTango.DevString """
        self.debug_stream("In getRegisterInfo()")
        argout = ''
        #----- PROTECTED REGION ID(TPM_DS.getRegisterInfo) ENABLED START -----#
        state_ok = self.checkStateFlow(self.getRegisterInfo.__name__)
        if state_ok:
            reglist = self.tpm_instance.getRegisterList()
            value = reglist.get(argin)
            argout = pickle.dumps(value)
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	TPM_DS.getRegisterInfo
        return argout
        
    def getRegisterList(self):
        """ Returns a list of registers and values, as a serialized python dictionary, stored as a string.
        
        :param : 
        :type: PyTango.DevVoid
        :return: List of register names.
        :rtype: PyTango.DevVarStringArray """
        self.debug_stream("In getRegisterList()")
        argout = ['']
        #----- PROTECTED REGION ID(TPM_DS.getRegisterList) ENABLED START -----#
        state_ok = self.checkStateFlow(self.getRegisterList.__name__)
        if state_ok:
            register_dict = self.tpm_instance.getRegisterList()
            argout = register_dict.keys()
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	TPM_DS.getRegisterList
        return argout
        
    def loadFirmwareBlocking(self, argin):
        """ Blocking call to load firmware.
        
        :param argin: File path.
        :type: PyTango.DevString
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In loadFirmwareBlocking()")
        #----- PROTECTED REGION ID(TPM_DS.loadFirmwareBlocking) ENABLED START -----#
        state_ok = self.checkStateFlow(self.loadFirmwareBlocking.__name__)
        if state_ok:
            arguments = pickle.loads(argin)
            device = arguments['device']
            filepath = arguments['path']
            self.flushAttributes()
            self.tpm_instance.loadFirmwareBlocking(Device(device), filepath)
            self.generateAttributes()
            self.attr_isProgrammed_read = True
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	TPM_DS.loadFirmwareBlocking
        
    def readAddress(self, argin):
        """ Reads values from a register location. Instead of a register name, the actual physical address has to be provided.
        
        :param argin: Associated register information.
        :type: PyTango.DevString
        :return: Register values.
        :rtype: PyTango.DevVarULongArray """
        self.debug_stream("In readAddress()")
        argout = [0]
        #----- PROTECTED REGION ID(TPM_DS.readAddress) ENABLED START -----#
        state_ok = self.checkStateFlow(self.readAddress.__name__)
        if state_ok:
            arguments = pickle.loads(argin)
            address = arguments['address']
            words = arguments['words']
            argout = self.tpm_instance.readAddress(address, words)
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	TPM_DS.readAddress
        return argout
        
    def readDevice(self, argin):
        """ Get device value.
        
        :param argin: 
            String containing:
            1) SPI Device to read from
            2) Address on device to read from
        :type: PyTango.DevString
        :return: Value of device.
        :rtype: PyTango.DevULong """
        self.debug_stream("In readDevice()")
        argout = 0
        #----- PROTECTED REGION ID(TPM_DS.readDevice) ENABLED START -----#
        state_ok = self.checkStateFlow(self.readDevice.__name__)
        if state_ok:
            arguments = pickle.loads(argin)
            device = arguments['device']
            address = arguments['address']
            argout = self.tpm_instance.readDevice(device, address)
        else:
           self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	TPM_DS.readDevice
        return argout
        
    def readRegister(self, argin):
        """ Reads values from a register location.
        
        :param argin: Associated register information.
        :type: PyTango.DevString
        :return: Register values.
        :rtype: PyTango.DevVarULongArray """
        self.debug_stream("In readRegister()")
        argout = [0]
        #----- PROTECTED REGION ID(TPM_DS.readRegister) ENABLED START -----#
        state_ok = self.checkStateFlow(self.readRegister.__name__)
        if state_ok:
            arguments = pickle.loads(argin)
            device = arguments['device']
            register = arguments['register']
            words = arguments['words']
            offset = arguments['offset']
            argout = self.tpm_instance.readRegister(Device(device), register, words, offset)
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	TPM_DS.readRegister
        return argout
        
    def removeCommand(self, argin):
        """ A generic command that removes a command entry from the Tango device driver.
        
        :param argin: Command name.
        :type: PyTango.DevString
        :return: True if command removal was successful, false otherwise.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In removeCommand()")
        argout = False
        #----- PROTECTED REGION ID(TPM_DS.removeCommand) ENABLED START -----#
        state_ok = self.checkStateFlow(self.removeCommand.__name__)
        if state_ok:
            try:
                del self.plugin_cmd_list[argin]
                del self.state_list[argin]
                argout = True
            except DevFailed as df:
                print("Failed to remove command entry in device server: \n%s" % df)
                argout = False
            finally:
                return argout
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	TPM_DS.removeCommand
        return argout
        
    def setBoardState(self, argin):
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
        self.debug_stream("In setBoardState()")
        #----- PROTECTED REGION ID(TPM_DS.setBoardState) ENABLED START -----#
        self.attr_boardState_read = argin

    def writeAddress(self, argin):
        """ Writes values to a register location. The actual physical address has to be provided.
        
        :param argin: Associated register information.
        :type: PyTango.DevString
        :return: True if successful, false if not.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In writeAddress()")
        argout = False
        #----- PROTECTED REGION ID(TPM_DS.writeAddress) ENABLED START -----#
        state_ok = self.checkStateFlow(self.writeAddress.__name__)
        if state_ok:
            arguments = pickle.loads(argin)
            address = arguments['address']
            values = arguments['values']
            argout = self.tpm_instance.writeAddress(address, values)
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	TPM_DS.writeAddress
        
    def writeAddress(self, argin):
        """ Writes values to a register location. The actual physical address has to be provided.
        
        :param argin: Associated register information.
        :type: PyTango.DevString
        :return: True if successful, false if not.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In writeAddress()")
        argout = False
        #----- PROTECTED REGION ID(TPM_DS.writeAddress) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	TPM_DS.writeAddress
        return argout
        
    def writeDevice(self, argin):
        """ Set device value.
        
        :param argin: 
            A string containing the following:
            1) SPI device to write to
            2) Address on device to write to
            3) Value to write
        :type: PyTango.DevString
        :return: True if successful, false if not.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In writeDevice()")
        argout = False
        #----- PROTECTED REGION ID(TPM_DS.writeDevice) ENABLED START -----#
        state_ok = self.checkStateFlow(self.writeDevice.__name__)
        if state_ok:
            arguments = pickle.loads(argin)
            device = arguments['device']
            address = arguments['address']
            value = arguments['value']
            argout = self.tpm_instance.writeDevice(device, address, value)
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	TPM_DS.writeDevice
        return argout
        
    def writeRegister(self, argin):
        """ Writes values from a register location.
        
        :param argin: Associated register information.
        :type: PyTango.DevString
        :return: True if successful, false if not.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In writeRegister()")
        argout = False
        #----- PROTECTED REGION ID(TPM_DS.writeRegister) ENABLED START -----#
        state_ok = self.checkStateFlow(self.writeRegister.__name__)
        if state_ok:
            arguments = pickle.loads(argin)
            device = arguments['device']
            register = arguments['register']
            values = arguments['values']
            offset = arguments['offset']
            argout = self.tpm_instance.writeRegister(Device(device), register, values, offset)
        else:
            self.debug_stream("Invalid state")
        #----- PROTECTED REGION END -----#	//	TPM_DS.writeRegister
        return argout
        
    def runPluginCommand(self, argin):
        """ Proxy to run a particular plugin command.
        
        :param argin: Dictionary with name of command to run, and arguments.
        :type: PyTango.DevString
        :return: Any output from the command.
        :rtype: PyTango.DevString """
        self.debug_stream("In runPluginCommand()")
        argout = ''
        #----- PROTECTED REGION ID(TPM_DS.runPluginCommand) ENABLED START -----#
        arguments = pickle.loads(argin)
        fnName = arguments['fnName']
        self.info_stream("Running: %s" % fnName)
        fnInput = arguments['fnInput']
        self.info_stream("Input: %s" % fnInput)
        #self.info_stream("Cmd_list: %s" % self.plugin_cmd_list)
        if fnName in self.plugin_cmd_list:
            self.info_stream("Plugin command found!")
            methodCalled = getattr(self, fnName)
            self.info_stream("%s" % methodCalled)
            argout = methodCalled(argin)
            if not isinstance(argout, str):
                argout = pickle.dumps(argout)
            #argout = getattr(self, fnName)(fnInput)
        #----- PROTECTED REGION END -----#	//	TPM_DS.runPluginCommand
        return argout
        

class TPM_DSClass(PyTango.DeviceClass):
    #--------- Add you global class variables here --------------------------
    #----- PROTECTED REGION ID(TPM_DS.global_class_variables) ENABLED START -----#
    
    #----- PROTECTED REGION END -----#	//	TPM_DS.global_class_variables

    def dyn_attr(self, dev_list):
        """Invoked to create dynamic attributes for the given devices.
        Default implementation calls
        :meth:`TPM_DS.initialize_dynamic_attributes` for each device
    
        :param dev_list: list of devices
        :type dev_list: :class:`PyTango.DeviceImpl`"""
    
        for dev in dev_list:
            try:
                dev.initialize_dynamic_attributes()
            except:
                import traceback
                dev.warn_stream("Failed to initialize dynamic attributes")
                dev.debug_stream("Details: " + traceback.format_exc())
        #----- PROTECTED REGION ID(TPM_DS.dyn_attr) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	TPM_DS.dyn_attr

    #    Class Properties
    class_property_list = {
        }


    #    Device Properties
    device_property_list = {
        }


    #    Command definitions
    cmd_list = {
        'Connect':
            [[PyTango.DevString, "Device IP address and port number."],
            [PyTango.DevVoid, "none"]],
        'Disconnect':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevVoid, "none"]],
        'addCommand':
            [[PyTango.DevString, "A string containing a dictionary for fields required for command creation."],
            [PyTango.DevBoolean, "True if command creation was successful, false if not."]],
        'createScalarAttribute':
            [[PyTango.DevString, "New attribute name."],
            [PyTango.DevVoid, "none"]],
        'createVectorAttribute':
            [[PyTango.DevString, "New attribute name."],
            [PyTango.DevVoid, "none"]],
        'flushAttributes':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevVoid, "none"]],
        'generateAttributes':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevVoid, "none"]],
        'getDeviceList':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevString, "Dictionary of devices."]],
        'getFirmwareList':
            [[PyTango.DevString, "Device on board to get list of firmware, as a string."],
            [PyTango.DevString, "Dictionary of firmwares on the board."]],
        'getRegisterInfo':
            [[PyTango.DevString, "The register name for which information will be retrieved."],
            [PyTango.DevString, "Returns a string-encoded dictionary of information."]],
        'getRegisterList':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevVarStringArray, "List of register names."]],
        'loadFirmwareBlocking':
            [[PyTango.DevString, "File path."],
            [PyTango.DevVoid, "none"]],
        'readAddress':
            [[PyTango.DevString, "Associated register information."],
            [PyTango.DevVarULongArray, "Register values."]],
        'readDevice':
            [[PyTango.DevString, "String containing:\n1) SPI Device to read from\n2) Address on device to read from"],
            [PyTango.DevULong, "Value of device."]],
        'readRegister':
            [[PyTango.DevString, "Associated register information."],
            [PyTango.DevVarULongArray, "Register values."]],
        'removeCommand':
            [[PyTango.DevString, "Command name."],
            [PyTango.DevBoolean, "True if command removal was successful, false otherwise."]],
        'setBoardState':
            [[PyTango.DevLong, "Board status value."],
            [PyTango.DevVoid, "none"]],
        'writeAddress':
            [[PyTango.DevString, "Associated register information."],
            [PyTango.DevBoolean, "True if successful, false if not."]],
        'writeDevice':
            [[PyTango.DevString, "A string containing the following:\n1) SPI device to write to\n2) Address on device to write to\n3) Value to write"],
            [PyTango.DevBoolean, "True if successful, false if not."]],
        'writeRegister':
            [[PyTango.DevString, "Associated register information."],
            [PyTango.DevBoolean, "True if successful, false if not."]],
        'runPluginCommand':
            [[PyTango.DevString, "Dictionary with name of command to run, and arguments."],
            [PyTango.DevString, "Any output from the command."]],
        }


    #    Attribute definitions
    attr_list = {
        'boardState':
            [[PyTango.DevLong,
            PyTango.SCALAR,
            PyTango.READ]],
        'isProgrammed':
            [[PyTango.DevBoolean,
            PyTango.SCALAR,
            PyTango.READ]],
        }


def main():
    try:
        py = PyTango.Util(sys.argv)
        py.add_class(TPM_DSClass,TPM_DS,'TPM_DS')

        U = PyTango.Util.instance()
        U.server_init()
        U.server_run()

    except PyTango.DevFailed,e:
        print '-------> Received a DevFailed exception:',e
    except Exception,e:
        print '-------> An unforeseen exception occured....',e

if __name__ == '__main__':
    main()

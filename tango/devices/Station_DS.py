#!/usr/bin/env python
# -*- coding:utf-8 -*- 


##############################################################################
## license :
##============================================================================
##
## File :        Station_DS.py
## 
## Project :     AAVS Tango Station Driver
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

"""A Tango device that manages an entire station of TPMs."""

__all__ = ["Station_DS", "Station_DSClass", "main"]

__docformat__ = 'restructuredtext'

import PyTango
import sys
# Add additional import
# ----- PROTECTED REGION ID(Station_DS.additionnal_import) ENABLED START -----#
from PyTango import DevState, Util, Attr, SpectrumAttr, Attribute, MultiAttribute, Group
from PyTango._PyTango import DevFailed
from pyfabil import Device, BoardState, BoardMake
from types import *
import pickle
import inspect
import time
# ----- PROTECTED REGION END -----#	//	Station_DS.additionnal_import

## Device States Description
## ON : Station is ON.
## ALARM : Station is in ALARM.

class Station_DS (PyTango.Device_4Impl):

    #--------- Add you global variables here --------------------------
    # ----- PROTECTED REGION ID(Station_DS.global_variables) ENABLED START -----#
    all_states_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    tpm_dict = {}

    station_devices = PyTango.Group('station')

    def check_state_flow(self, fnName):
        """ Checks if the current state the device is in one of the states in a given list of allowed states for a paticular function.
        :param : Name of command to be executed
        :type: String
        :return: True if allowed, false if not.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In check_state_flow()")
        argout = False
        # get allowed states for this command
        try:
            fnAllowedStates = self.state_list[fnName]
            allowed = self.attr_station_state_read in fnAllowedStates
            if not allowed:
                self.info_stream("Current state allowed: %s" % allowed)
            argout = allowed
        except DevFailed as df:
            self.info_stream("Failed to check state flow: %s" % df)
            argout = False
        finally:
            return argout

    # State flow definitions - allowed states for each command
    state_list = {
        'add_tpm': all_states_list,
        'remove_tpm': all_states_list,
        'connect_tpm': all_states_list,
        'run_station_command': all_states_list,
        'get_station_state': all_states_list
    }
    # ----- PROTECTED REGION END -----#	//	Station_DS.global_variables

    def __init__(self,cl, name):
        PyTango.Device_4Impl.__init__(self,cl,name)
        self.debug_stream("In __init__()")
        Station_DS.init_device(self)
        # ----- PROTECTED REGION ID(Station_DS.__init__) ENABLED START -----#

        # ----- PROTECTED REGION END -----#	//	Station_DS.__init__
        
    def delete_device(self):
        self.debug_stream("In delete_device()")
        # ----- PROTECTED REGION ID(Station_DS.delete_device) ENABLED START -----#

        # ----- PROTECTED REGION END -----#	//	Station_DS.delete_device

    def init_device(self):
        self.debug_stream("In init_device()")
        self.get_device_properties(self.get_device_class())
        self.attr_station_state_read = 0
        # ----- PROTECTED REGION ID(Station_DS.init_device) ENABLED START -----#
        self.set_state(DevState.ON)
        self.set_station_state(BoardState.Init.value)
        # ----- PROTECTED REGION END -----#	//	Station_DS.init_device

    def always_executed_hook(self):
        self.debug_stream("In always_excuted_hook()")
        # ----- PROTECTED REGION ID(Station_DS.always_executed_hook) ENABLED START -----#

        # ----- PROTECTED REGION END -----#	//	Station_DS.always_executed_hook

    #-----------------------------------------------------------------------------
    #    Station_DS read/write attribute methods
    #-----------------------------------------------------------------------------
    
    def read_station_state(self, attr):
        self.debug_stream("In read_station_state()")
        # ----- PROTECTED REGION ID(Station_DS.station_state_read) ENABLED START -----#
        attr.set_value(self.attr_station_state_read)
        self.info_stream(BoardState(self.attr_station_state_read))
        # ----- PROTECTED REGION END -----#	//	Station_DS.station_state_read
        
    
    
        # ----- PROTECTED REGION ID(Station_DS.initialize_dynamic_attributes) ENABLED START -----#

        # ----- PROTECTED REGION END -----#	//	Station_DS.initialize_dynamic_attributes
            
    def read_attr_hardware(self, data):
        self.debug_stream("In read_attr_hardware()")
        # ----- PROTECTED REGION ID(Station_DS.read_attr_hardware) ENABLED START -----#

        # ----- PROTECTED REGION END -----#	//	Station_DS.read_attr_hardware


    #-----------------------------------------------------------------------------
    #    Station_DS command methods
    #-----------------------------------------------------------------------------
    
    def add_tpm(self, argin):
        """ Adds the Tango device proxy name to the list of TPMs managed 
        by this station.
        
        :param argin: 
            The device proxy name, board type, IP address and port number
             for communication are supplied as a serialized python dictionary, stored as a string.
        :type: PyTango.DevString
        :return: Returns true if operation is successful, false otherwise.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In add_tpm()")
        argout = False
        # ----- PROTECTED REGION ID(Station_DS.add_tpm) ENABLED START -----#
        state_ok = self.check_state_flow(inspect.stack()[0][3])
        if state_ok:
            try:
                arguments = pickle.loads(argin)
                device_proxy_name = arguments['name']
                device_type = arguments['type']
                device_ip = arguments['ip']
                device_port = arguments['port']
                sub_dict = {'type': device_type, 'ip': device_ip, 'port': device_port}
                self.tpm_dict[device_proxy_name] = sub_dict
                self.station_devices.add(device_proxy_name)
                argout = True
            except DevFailed as df:
                self.debug_stream("Failed to add tpm to station: %s" % df)
        else:
            self.debug_stream("Invalid state")
        # ----- PROTECTED REGION END -----#	//	Station_DS.add_tpm
        return argout
        
    def remove_tpm(self, argin):
        """ Removes the Tango device proxy name from the list of TPMs managed by this station.
        
        :param argin: The Tango device proxy name of the TPM to remove from the station.
        :type: PyTango.DevString
        :return: Returns true if operation is successful, false otherwise.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In remove_tpm()")
        argout = False
        # ----- PROTECTED REGION ID(Station_DS.remove_tpm) ENABLED START -----#
        state_ok = self.check_state_flow(inspect.stack()[0][3])
        if state_ok:
            try:
                device_proxy_name = argin
                del self.tpm_dict[device_proxy_name]
                self.station_devices.remove(device_proxy_name)
                argout = True
            except DevFailed as df:
                self.debug_stream("Failed to remove tpm from station: %s" % df)
        else:
            self.debug_stream("Invalid state")
            # ----- PROTECTED REGION END -----#	//	Station_DS.remove_tpm
        return argout
        
    def connect_tpm(self, argin):
        """ Instructs a particular TPM to connect.
        
        :param argin: Tango device proxy name of TPM.
        :type: PyTango.DevString
        :return: Returns true if operation is successful, false otherwise.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In connect_tpm()")
        argout = False
        # ----- PROTECTED REGION ID(Station_DS.connect_tpm) ENABLED START -----#
        state_ok = self.check_state_flow(inspect.stack()[0][3])
        if state_ok:
            try:
                device_name = argin
                sub_dict = self.tpm_dict[device_name]

                # setup device
                tpm_instance = PyTango.DeviceProxy(device_name)
                tpm_instance.ip_address = sub_dict['ip']
                tpm_instance.port = sub_dict['port']

                # Connect to device
                tpm_instance.command_inout("connect")
                self.info_stream("Connected: %s" % device_name)
                argout = True
            except DevFailed as df:
                self.debug_stream("Failed to connect to all station devices: %s" % df)
                argout = ''
        else:
            self.debug_stream("Invalid state")
        # ----- PROTECTED REGION END -----#	//	Station_DS.connect_tpm
        return argout
        
    def set_station_state(self, argin):
        """ Sets the station status by passing in a value.
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
        
        :param argin: Station state.
        :type: PyTango.DevLong
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In set_station_state()")
        # ----- PROTECTED REGION ID(Station_DS.set_station_state) ENABLED START -----#

        # ----- PROTECTED REGION END -----#	//	Station_DS.set_station_state
        
    def run_station_command(self, argin):
        """ This command takes the name of a command and executes it station-wide.
        
        The command must exist on all connected devices.
        
        :param argin: 
            A pickled string containing:
            1) Name of command
            2) Arguments for command
            
            Arguments for a command have to be supplied as list of dictionaries.
            If only one item is in the list, the same input is applied to all station commands.
            
            If more than one item is in the list, then each item is sent to an individual device (in order of station devices).
            Therefore the size of the list should be equivalent to the number of devices controlled by the station.
        :type: PyTango.DevString
        :return: Returns a set of replies per device in the station, pickled as a string.
        :rtype: PyTango.DevString """
        self.debug_stream("In run_station_command()")
        argout = ''
        # ----- PROTECTED REGION ID(Station_DS.run_station_command) ENABLED START -----#
        state_ok = self.check_state_flow(inspect.stack()[0][3])
        if state_ok:
            try:
                arguments = pickle.loads(argin)
                fnName = arguments['fnName']
                fnInput = arguments['fnInput']
                self.info_stream("Calling TPM function: %s" % fnName)

                if fnInput is not None:
                    if len(fnInput) > 1 and len(fnInput) != len(self.tpm_dict):
                        raise Exception(
                            'Number of inputs to station commands not equivalent to number of devices under station control.')

                # loop over tpms in station
                command_indexes = []
                cnt = 0
                for device in self.tpm_dict:
                    tpm_proxy = self.station_devices.get_device(device)
                    print tpm_proxy
                    if fnInput is None:
                        self.info_stream("No input detected...")
                        command_indexes.append(tpm_proxy.command_inout_asynch(fnName))
                    elif len(fnInput) > 1:
                        self.info_stream("Multiple inputs detected...spreading to boards")
                        pickled_fnInput = pickle.dumps(fnInput[cnt])
                        command_indexes.append(tpm_proxy.command_inout_asynch(fnName, pickled_fnInput))
                    else:
                        self.info_stream("Single input detected...unifying calls")
                        pickled_fnInput = pickle.dumps(fnInput[0])
                        command_indexes.append(tpm_proxy.command_inout_asynch(fnName, pickled_fnInput))
                    cnt += 1

                replies = [None] * len(command_indexes)
                replies_gathered = 0
                while replies_gathered < len(command_indexes):
                    time.sleep(0.1)
                    cnt = 0
                    for device in self.tpm_dict:
                        self.debug_stream("Waiting for asynchronous reply...")
                        tpm_proxy = self.station_devices.get_device(device)
                        try:
                            #replies[cnt] = tpm_proxy.command_inout_reply(command_indexes[cnt])
                            replies[cnt] = tpm_proxy.command_inout_reply(command_indexes[cnt])
                            replies_gathered += 1
                            self.debug_stream('Received: %s' % replies[cnt])
                            cnt += 1
                        except DevFailed as e:
                            #self.debug_stream('Received DevFailed: %s' % e)
                            #if e.args[0]['reason'] != 'API_AsynReplyNotArrived':
                                self.info_stream('Wait for reply again')
                                continue
                                #raise Exception, 'Weird exception received!: %s' % e

                argout = pickle.dumps(replies)
            except DevFailed as df:
                self.debug_stream("Failed to run station-wide command: %s" % df)
        else:
            self.debug_stream("Invalid state")
        # ----- PROTECTED REGION END -----#	//	Station_DS.run_station_command
        return argout
        
    def get_station_state(self):
        """ This commands returns a summary of the state of each TPM in the station.
        
        :param : 
        :type: PyTango.DevVoid
        :return: A pickled string storing the state of each TPM in the station.
        :rtype: PyTango.DevString """
        self.debug_stream("In get_station_state()")
        argout = ''
        # ----- PROTECTED REGION ID(Station_DS.get_station_state) ENABLED START -----#
        state_ok = self.check_state_flow(inspect.stack()[0][3])
        if state_ok:
            try:
                states = {}
                for device_proxy_name in self.tpm_dict:
                    self.info_stream("Retrieving state from: %s" % device_proxy_name)
                    tpm_instance = PyTango.DeviceProxy(device_proxy_name)
                    tpm_state = tpm_instance.read_attribute("board_state")
                    self.debug_stream("State: %s" % tpm_state.value)
                    states[device_proxy_name] = tpm_state.value
                argout = pickle.dumps(states)
            except DevFailed as df:
                self.debug_stream("Failed to report station board states: %s" % df)
                argout = ''
        else:
            self.debug_stream("Invalid state")
        # ----- PROTECTED REGION END -----#	//	Station_DS.get_station_state
        return argout
        

    # ----- PROTECTED REGION ID(Station_DS.programmer_methods) ENABLED START -----#

        # ----- PROTECTED REGION END -----#	//	Station_DS.programmer_methods

class Station_DSClass(PyTango.DeviceClass):
    #--------- Add you global class variables here --------------------------
    # ----- PROTECTED REGION ID(Station_DS.global_class_variables) ENABLED START -----#

    # ----- PROTECTED REGION END -----#	//	Station_DS.global_class_variables

    def dyn_attr(self, dev_list):
        """Invoked to create dynamic attributes for the given devices.
        Default implementation calls
        :meth:`Station_DS.initialize_dynamic_attributes` for each device
    
        :param dev_list: list of devices
        :type dev_list: :class:`PyTango.DeviceImpl`"""
    
        for dev in dev_list:
            try:
                dev.initialize_dynamic_attributes()
            except:
                import traceback
                dev.warn_stream("Failed to initialize dynamic attributes")
                dev.debug_stream("Details: " + traceback.format_exc())
        # ----- PROTECTED REGION ID(Station_DS.dyn_attr) ENABLED START -----#

                # ----- PROTECTED REGION END -----#	//	Station_DS.dyn_attr

    #    Class Properties
    class_property_list = {
        }


    #    Device Properties
    device_property_list = {
        }


    #    Command definitions
    cmd_list = {
        'add_tpm':
            [[PyTango.DevString, "The device proxy name, board type, IP address and port number\n for communication are supplied as a serialized python dictionary, stored as a string."],
            [PyTango.DevBoolean, "Returns true if operation is successful, false otherwise."]],
        'remove_tpm':
            [[PyTango.DevString, "The Tango device proxy name of the TPM to remove from the station."],
            [PyTango.DevBoolean, "Returns true if operation is successful, false otherwise."]],
        'connect_tpm':
            [[PyTango.DevString, "Tango device proxy name of TPM."],
            [PyTango.DevBoolean, "Returns true if operation is successful, false otherwise."]],
        'set_station_state':
            [[PyTango.DevLong, "Station state."],
            [PyTango.DevVoid, "none"]],
        'run_station_command':
            [[PyTango.DevString, "A pickled string containing:\n1) Name of command\n2) Arguments for command\n\nArguments for a command have to be supplied as list of dictionaries.\nIf only one item is in the list, the same input is applied to all station commands.\n\nIf more than one item is in the list, then each item is sent to an individual device (in order of station devices).\nTherefore the size of the list should be equivalent to the number of devices controlled by the station."],
            [PyTango.DevString, "Returns a set of replies per device in the station, pickled as a string."]],
        'get_station_state':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevString, "A pickled string storing the state of each TPM in the station."]],
        }


    #    Attribute definitions
    attr_list = {
        'station_state':
            [[PyTango.DevLong,
            PyTango.SCALAR,
            PyTango.READ]],
        }


def main():
    try:
        py = PyTango.Util(sys.argv)
        py.add_class(Station_DSClass,Station_DS,'Station_DS')
        # ----- PROTECTED REGION ID(Station_DS.add_classes) ENABLED START -----#

        # ----- PROTECTED REGION END -----#	//	Station_DS.add_classes

        U = PyTango.Util.instance()
        U.server_init()
        U.server_run()

    except PyTango.DevFailed,e:
        print '-------> Received a DevFailed exception:',e
    except Exception,e:
        print '-------> An unforeseen exception occured....',e

if __name__ == '__main__':
    main()

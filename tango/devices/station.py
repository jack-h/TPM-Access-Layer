import PyTango
from pyfabil import Device, BoardMake
import pickle
import sys


class Station(object):

    # Class constructor
    def __init__(self, station_name = None):
        if station_name is not None:
            self._station_instance = PyTango.DeviceProxy(station_name)

    def add_tpm(self, device_name, device_type, ip_address, port):
        try:
            arguments = {}
            arguments['name'] = device_name
            arguments['type'] = device_type
            arguments['ip'] = ip_address
            arguments['port'] = port
            args = pickle.dumps(arguments)
            return self._station_instance.command_inout("add_tpm", args)
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def remove_tpm(self, device_name):
        try:
            arguments = {}
            arguments['name'] = device_name
            args = pickle.dumps(arguments)
            return self._station_instance.command_inout("remove_tpm", args)
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def get_station_state(self):
        try:
            return pickle.loads(self._station_instance.command_inout("get_station_state"))
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def connect_tpm(self, device_name):
        try:
            args = device_name
            return self._station_instance.command_inout("connect_tpm", args)
        except:
            print "Error:", sys.exc_info()[0]
            raise

    def run_station_command(self, command_name, command_input):
        try:
            arguments = {}
            arguments['fnName'] = command_name
            arguments['fnInput'] = command_input
            args = pickle.dumps(arguments)
            return pickle.loads(self._station_instance.command_inout("run_station_command", args))
        except:
            print "Error:", sys.exc_info()[0]
            raise

if __name__ == "__main__":
    station = Station(station_name = "test/station/1")
    print station.add_tpm(device_name = "test/tpm_board/1", device_type = BoardMake.TpmBoard, ip_address = "127.0.0.1", port = 10000)

    fnName = "sink_alarm_state"
    fnInput = None
    print station.run_station_command(fnName, fnInput)
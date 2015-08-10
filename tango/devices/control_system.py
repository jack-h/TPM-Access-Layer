import PyTango
from pyfabil import Device, BoardMake
import pickle
import sys

# ------------------ Station Related Commands --------------------------------- #
def station_add_tile(station_id, tile_name, device_type, ip_address, port):
    try:
        station_instance = PyTango.DeviceProxy(station_id)
        arguments = {}
        arguments['name'] = tile_name
        arguments['type'] = device_type
        arguments['ip'] = ip_address
        arguments['port'] = port
        args = pickle.dumps(arguments)
        return station_instance.command_inout("add_tpm", args)
    except:
        print "Error:", sys.exc_info()[0]
        raise


def station_remove_tile(station_id, tile_name):
    try:
        station_instance = PyTango.DeviceProxy(station_id)
        arguments = {}
        arguments['name'] = tile_name
        args = pickle.dumps(arguments)
        return station_instance.command_inout("remove_tpm", args)
    except:
        print "Error:", sys.exc_info()[0]
        raise


def station_get_state(station_id):
    try:
        station_instance = PyTango.DeviceProxy(station_id)
        return pickle.loads(station_instance.command_inout("get_station_state"))
    except:
        print "Error:", sys.exc_info()[0]
        raise


def station_connect_tile(station_id, tile_name):
    try:
        station_instance = PyTango.DeviceProxy(station_id)
        args = tile_name
        return station_instance.command_inout("connect_tpm", args)
    except:
        print "Error:", sys.exc_info()[0]
        raise


def station_run_command(station_id, command_name, command_input):
    try:
        station_instance = PyTango.DeviceProxy(station_id)
        arguments = {}
        arguments['fnName'] = command_name
        arguments['fnInput'] = command_input
        args = pickle.dumps(arguments)
        return pickle.loads(station_instance.command_inout("run_station_command", args))
    except:
        print "Error:", sys.exc_info()[0]
        raise


# ------------------ Board Related Commands --------------------------------- #

def tile_connect(tile_id, ip_address="127.0.0.1", port=10000):
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        tile_instance.ip_address = ip_address
        tile_instance.port = port
        return tile_instance.command_inout("connect")
    except:
        print "Error:", sys.exc_info()[0]
        raise


def tile_disconnect(tile_id):
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        tile_instance.command_inout("disconnect")
    except:
        print "Error:", sys.exc_info()[0]
        raise


def tile_reset(tile_id, device):
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        arguments = {}
        arguments['device'] = device.value
        args = pickle.dumps(arguments)
        tile_instance.command_inout("reset_board", args)
    except:
        print "Error:", sys.exc_info()[0]
        raise


def tile_sink_alarm_state(tile_id):
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        tile_instance.command_inout("sink_alarm_state")
    except:
        print "Error:", sys.exc_info()[0]
        raise


def tile_get_device_list(tile_id):
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        return tile_instance.command_inout("get_device_list")
    except:
        print "Error:", sys.exc_info()[0]
        raise


def tile_get_firmware_list(tile_id, device=Device.Board):
    # TPM device = Device.Board
    # Roach device = Device.FPGA_1
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        arguments = {}
        arguments['device'] = device.value
        args = pickle.dumps(arguments)
        return tile_instance.command_inout("get_firmware_list", args)
    except:
        print "Error:", sys.exc_info()[0]
        raise


def tile_get_register_info(tile_id, reset=False, load_values=False):
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        arguments = {}
        arguments['reset'] = reset
        arguments['load_values'] = load_values
        args = pickle.dumps(arguments)
        return tile_instance.command_inout("get_register_info", args)
    except:
        print "Error:", sys.exc_info()[0]
        raise


def tile_get_register_list(tile_id, reset=False, load_values=False):
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        arguments = {}
        arguments['reset'] = reset
        arguments['load_values'] = load_values
        args = pickle.dumps(arguments)
        return tile_instance.command_inout("get_register_list", args)
    except:
        print "Error:", sys.exc_info()[0]
        raise


def tile_load_firmware(tile_id, device, filepath=None, load_values=False):
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        arguments = {}
        arguments['device'] = device.value
        arguments['path'] = filepath
        arguments['load_values'] = load_values
        args = pickle.dumps(arguments)
        return tile_instance.command_inout("load_firmware", args)
    except:
        print "Error:", sys.exc_info()[0]
        raise


def tile_load_plugin(tile_id, plugin, **kwargs):
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        arguments = {}
        arguments['plugin_name_load'] = plugin
        arguments['kw_args'] = kwargs
        args = pickle.dumps(arguments)
        return tile_instance.command_inout("load_plugin", args)
    except:
        print "Error:", sys.exc_info()[0]
        raise


def tile_unload_all_plugins(tile_id):
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        return tile_instance.command_inout("unload_all_plugins")
    except:
        print "Error:", sys.exc_info()[0]
        raise


def tile_unload_plugin(tile_id, plugin, instance=None):
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        arguments = {}
        arguments['plugin'] = plugin
        arguments['instance'] = instance
        args = pickle.dumps(arguments)
        return tile_instance.command_inout("unload_plugin", args)
    except:
        print "Error:", sys.exc_info()[0]
        raise


def tile_run_plugin_command(tile_id, name, input):
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        arguments = {}
        arguments['fnName'] = name
        arguments['fnInput'] = input
        args = pickle.dumps(arguments)
        return tile_instance.command_inout("run_plugin_command", args)
    except:
        print "Error:", sys.exc_info()[0]
        raise


def tile_read_address(tile_id, address, n=1):
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        arguments = {}
        arguments['address'] = address
        arguments['words'] = n
        args = pickle.dumps(arguments)
        return tile_instance.command_inout("read_address", args)
    except:
        print "Error:", sys.exc_info()[0]
        raise


def tile_write_address(tile_id, address, values):
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        arguments = {}
        arguments['address'] = address
        arguments['values'] = values
        args = pickle.dumps(arguments)
        return tile_instance.command_inout("write_address", args)
    except:
        print "Error:", sys.exc_info()[0]
        raise


def tile_read_device(tile_id, address, device):
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        arguments = {}
        arguments['address'] = address
        arguments['device'] = device.value
        args = pickle.dumps(arguments)
        return tile_instance.command_inout("read_device", args)
    except:
        print "Error:", sys.exc_info()[0]
        raise


def tile_write_device(tile_id, device, address, values):
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        arguments = {}
        arguments['address'] = address
        arguments['device'] = device.value
        arguments['value'] = values
        args = pickle.dumps(arguments)
        return tile_instance.command_inout("write_device", args)
    except:
        print "Error:", sys.exc_info()[0]
        raise


def tile_read_register(tile_id, register, n=1, offset=0, device=None):
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        arguments = {}
        arguments['register'] = register
        arguments['device'] = device.value
        arguments['words'] = n
        arguments['offset'] = offset
        args = pickle.dumps(arguments)
        return tile_instance.command_inout("read_register", args)
    except:
        print "Error:", sys.exc_info()[0]
        raise


def tile_write_register(tile_id, register, values, offset=0, device=None):
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        arguments = {}
        arguments['register'] = register
        arguments['device'] = device.value
        arguments['values'] = values
        arguments['offset'] = offset
        args = pickle.dumps(arguments)
        return tile_instance.command_inout("write_register", args)
    except:
        print "Error:", sys.exc_info()[0]
        raise


def tile_set_attribute_levels(tile_id, name, min_value, max_value, min_alarm, max_alarm):
    try:
        tile_instance = PyTango.DeviceProxy(tile_id)
        arguments = {}
        arguments['name'] = name
        arguments['min_value'] = min_value
        arguments['max_value'] = max_value
        arguments['min_alarm'] = min_alarm
        arguments['max_alarm'] = max_alarm
        args = pickle.dumps(arguments)
        return tile_instance.command_inout("set_attribute_levels", args)
    except:
        print "Error:", sys.exc_info()[0]
        raise

# ------------------ Test Commands --------------------------------- #
if __name__ == "__main__":
    station_id = "test/station/1"
    tile_name = "test/tpm_board/1"
    device_type = BoardMake.TpmBoard

    station_add_tile(station_id, tile_name, device_type, ip_address="127.0.0.1", port=10000)

    fnName = "sink_alarm_state"
    fnInput = None
    print station_run_command(station_id, fnName, fnInput)

    tile_name = "test/roach_board/1"
    device_type = BoardMake.RoachBoard
    print tile_connect(tile_name, ip_address="192.168.100.2", port=7147)
    print tile_load_firmware('tut4.bof')

from time import sleep
import unittest
import os

from pyfabil import UniBoard, Device, LibraryError, Status, Error
from pyfabil.tests.uniboard_simulator import UniBoardSimulator


__author__ = 'Alessio Magro'

class TestUniBoard(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestUniBoard, self).__init__(*args, **kwargs)
        self._simulator    = None
        self._uniboard_sim = None
        self._ip           = "127.0.0.1"
        self._port         = 50000

        # Register map for testing
        self._config_file  = os.path.join(os.getcwd(), "tests/files/unb_test_map.xml")
        if not os.path.exists(self._config_file):
            self._config_file = os.path.join(os.getcwd(), "files/unb_test_map.xml")

        # Device mapping
        self._devices = {0 : Device.FPGA_1, 1 : Device.FPGA_2, 2: Device.FPGA_3,
                         3 : Device.FPGA_4, 4 : Device.FPGA_5, 5: Device.FPGA_6,
                         6 : Device.FPGA_7, 7 : Device.FPGA_8}

        # Node list
        self._nodelist = [(0, 'F'), (1, 'F'), (2, 'F'), (3, 'F'),
                          (4, 'B'), (5, 'B'), (6, 'B'), (7, 'B')]

    def setUp(self):
        """ Start the mock uniboard script """
        # Launch simluator thread
        self._simulator = UniBoardSimulator()
        self._simulator.start()
        sleep(1)

    def tearDown(self):
        """ Ready from unittest, clean up uniboard simulator """
        # Send stop signal to simulator
        if self._simulator is not None:
            self._simulator.stop()

        # Wait for simulator to finish
        self._simulator.join()
        self._simulator = None

    def test__convert_node_to_device(self):
        """ Check conversion from node to device """

        unb = UniBoard(nodelist = self._nodelist)

        # Check that node string combinations return the correct devices
        for (node_num, node_type) in self._nodelist:
            self.assertEqual(unb._nodes[node_num]['device'], self._devices[node_num])
            self.assertEqual(unb._nodes[node_num]['type'], node_type)
            self.assertEqual(unb._convert_node_to_device(str(node_num)), self._devices[node_num])
            self.assertEqual(unb._convert_node_to_device("fpga%d" % (node_num + 1)), self._devices[node_num])
            self.assertEqual(unb._convert_node_to_device("node%d" % node_num), self._devices[node_num])

        # Check that node combinations are returned correctly
        self.assertEqual(unb._convert_node_to_device('all'), self._devices.values())
        self.assertEqual(unb._convert_node_to_device('front'), [Device.FPGA_1, Device.FPGA_2, Device.FPGA_3, Device.FPGA_4])
        self.assertEqual(unb._convert_node_to_device('back'), [Device.FPGA_5, Device.FPGA_6, Device.FPGA_7, Device.FPGA_8])

        # Chech that invalid nodes raises exception
        with self.assertRaises(LibraryError):
            unb._convert_node_to_device('random')

    def test__get_nodes(self):
        """ Check name combinations for getting group of nodes """
        unb = UniBoard(nodelist = self._nodelist)

        # Check that node string combinations return the correct devices
        for (node_num, node_type) in self._nodelist:
            # String commands
            self.assertEqual(unb._get_nodes(str(node_num)), self._devices[node_num])
            self.assertEqual(unb._get_nodes("fpga%d" % (node_num + 1)), self._devices[node_num])
            self.assertEqual(unb._get_nodes("node%d" % node_num), self._devices[node_num])

            # Int commands
            self.assertEqual(unb._get_nodes(node_num), self._devices[node_num])

            # Device command
            self.assertEqual(unb._get_nodes(Device.FPGA_1), Device.FPGA_1)

        # Check invalid number and string
        with self.assertRaises(LibraryError):
            unb._get_nodes('random')
            unb._get_nodes(11)
            unb._get_nodes(-1)
            unb._get_nodes({})

        # Test list and tuple features
        self.assertEqual(unb._get_nodes(range(8)), self._devices.values())
        self.assertEqual(unb._get_nodes(tuple(range(8))), self._devices.values())
        self.assertEqual(unb._get_nodes([str(x) for x in range(8)]), self._devices.values())
        self.assertEqual(unb._get_nodes(self._devices.values()), self._devices.values())

    def test_connect(self):
        """ Test UniBoard connection """
        unb = UniBoard(ip = self._ip, port = self._port, nodelist = self._nodelist)
        self.assertEqual(unb.get_status(), Status.OK)

    def test_load_firmware_blocking(self):
        """ Test loading of firmware """
        unb = UniBoard(ip = self._ip, port = self._port, nodelist = self._nodelist)
        self.assertEqual(unb.get_status(), Status.OK)

        # Call load firmware on all nodes
        unb.load_firmware_blocking(self._devices.values(), self._config_file)
        self.assertTrue(unb._programmed)
        self.assertEqual(unb.get_status(), Status.OK)

    def test_write_read_register(self):
        """ Test writing to registers, all combinations """
        unb = UniBoard(ip = self._ip, port = self._port, nodelist = self._nodelist)
        self.assertEqual(unb.get_status(), Status.OK)

        # Call load firmware on all nodes
        unb.load_firmware_blocking(self._devices.values(), self._config_file)
        self.assertTrue(unb._programmed)
        self.assertEqual(unb.get_status(), Status.OK)

        value = 1
        register = "%s.regfile.register1"
        # Perform tests in pairs, each time writing to and reading from a register
        for node in self._nodelist:
            dev = str(node[0])
            unb.write_register(register % dev, value)
            result = unb.read_register(register % dev)
            self.assertEqual(len(result), 1)
            self.assertEqual(len(result[0]), 3)
            self.assertEqual(result[0][1], Error.Success.value)
            self.assertEqual(result[0][2], [value])
            value += 1

            dev = "fpga%d" % (node[0] + 1)
            unb.write_register(register % dev, value)
            result = unb.read_register(register % dev)
            self.assertEqual(len(result), 1)
            self.assertEqual(len(result[0]), 3)
            self.assertEqual(result[0][1], Error.Success.value)
            self.assertEqual(result[0][2], [value])
            value += 1

            dev = "node%d" % node[0]
            unb.write_register(register % dev, value)
            result = unb.read_register(register % dev)
            self.assertEqual(len(result), 1)
            self.assertEqual(len(result[0]), 3)
            self.assertEqual(result[0][1], Error.Success.value)
            self.assertEqual(result[0][2], [value])
            value += 1

        register = "regfile.register1"
        for node in self._nodelist:
            unb.write_register(register, value, device = self._devices[node[0]])
            result = unb.read_register(register, device = self._devices[node[0]])
            self.assertEqual(len(result), 1)
            self.assertEqual(len(result[0]), 3)
            self.assertEqual(result[0][1], Error.Success.value)
            self.assertEqual(result[0][2], [value])
            value += 1

        # Test with node combination specified in register name
        # All nodes
        register = "all.regfile.register1"
        unb.write_register(register, value)
        result = unb.read_register(register)
        self.assertEqual(len(result), len(self._nodelist))
        for i, node in enumerate(self._nodelist):
            self.assertEqual(len(result[i]), 3)
            self.assertEqual(result[i][0], node[0])
            self.assertEqual(result[i][1], Error.Success.value)
            self.assertEqual(result[i][2], [value])
        value += 1

        # Front nodes
        register = "front.regfile.register1"
        unb.write_register(register, value)
        result = unb.read_register(register)
        nodes = [n for n, t in self._nodelist if t == 'F']
        self.assertEqual(len(result), len(nodes))
        for i, node in enumerate(nodes):
            self.assertEqual(len(result[i]), 3)
            self.assertEqual(result[i][0], node)
            self.assertEqual(result[i][1], Error.Success.value)
            self.assertEqual(result[i][2], [value])
        value += 1

        # Back nodes
        register = "back.regfile.register1"
        unb.write_register(register, value)
        result = unb.read_register(register)
        nodes = [n for n, t in self._nodelist if t == 'B']
        self.assertEqual(len(result), len(nodes))
        for i, node in enumerate(nodes):
            self.assertEqual(len(result[i]), 3)
            self.assertEqual(result[i][0], node)
            self.assertEqual(result[i][1], Error.Success.value)
            self.assertEqual(result[i][2], [value])
        value += 1

        # All devices, specified explicitly
        register = "regfile.register1"
        unb.write_register(register, value, device = self._devices.values())
        result = unb.read_register(register, device = self._devices.values())
        self.assertEqual(len(result), len(self._devices.values()))
        for i, node in enumerate([a for a,b in self._nodelist]):
            self.assertEqual(len(result[i]), 3)
            self.assertEqual(result[i][0], node)
            self.assertEqual(result[i][1], Error.Success.value)
            self.assertEqual(result[i][2], [value])
        value += 1

        # All devices, multiple data items to write
        unb.write_register(register, [value] * 256, device = self._devices.values())
        result = unb.read_register(register, 256, device = self._devices.values())
        self.assertEqual(len(result), len(self._devices.values()))
        for i, node in enumerate([a for a, b in self._nodelist]):
            self.assertEqual(len(result[i]), 3)
            self.assertEqual(result[i][0], node)
            self.assertEqual(result[i][1], Error.Success.value)
            self.assertEqual(len(result[i][2]), 256)
            self.assertEqual(result[i][2], [value] * 256)

    def test_write_read_address(self):
        """ Test read write fifo """
        unb = UniBoard(ip = self._ip, port = self._port, nodelist = self._nodelist)
        self.assertEqual(unb.get_status(), Status.OK)

        # Call load firmware on all nodes
        unb.load_firmware_blocking(self._devices.values(), self._config_file)
        self.assertTrue(unb._programmed)
        self.assertEqual(unb.get_status(), Status.OK)

        value = 1
        address = 0x1000
        unb.write_address(address, value, device = self._devices.values())
        result = unb.read_address(address, device = self._devices.values())
        self.assertEqual(len(result), len(self._nodelist))
        for i, node in enumerate(self._nodelist):
            self.assertEqual(len(result[i]), 3)
            self.assertEqual(result[i][0], node[0])
            self.assertEqual(result[i][1], Error.Success.value)
            self.assertEqual(result[i][2], [value])

    # def test_write_read_fifo(self):
    #     """ Test read write fifo """
    #     unb = UniBoard(ip = self._ip, port = self._port, nodelist = self._nodelist)
    #     self.assertEqual(unb.get_status(), Status.OK)
    #
    #     # Call load firmware on all nodes
    #     unb.load_firmware_blocking(self._devices.values(), self._config_file)
    #     self.assertTrue(unb._programmed)
    #     self.assertEqual(unb.get_status(), Status.OK)
    #
    #     register = "all.regfile.fifo_register"
    #     unb.write_register(register, value)
    #     result = unb.read_register(register)
    #     self.assertEqual(len(result), len(self._nodelist))
    #     for i, node in enumerate(self._nodelist):
    #         self.assertEqual(len(result[i]), 3)
    #         self.assertEqual(result[i][0], node[0])
    #         self.assertEqual(result[i][1], Error.Success.value)
    #         self.assertEqual(result[i][2], [value])

if __name__ == "__main__":
    unittest.TestLoader.sortTestMethodsUsing = None
    unittest.main()
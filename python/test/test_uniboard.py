from pyfabil import UniBoard, Device, LibraryError, Status
from unittest import TestCase, main
from time import sleep
import subprocess
import sys
import os

__author__ = 'Alessio Magro'

class TestUniBoard(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestUniBoard, self).__init__(*args, **kwargs)
        self._mock_script = 'mock_uniboard.py'
        self._uniboard_sim = None

        # Device mapping
        self._devices = {0 : Device.FPGA_1, 1 : Device.FPGA_2, 2: Device.FPGA_3,
                         3 : Device.FPGA_4, 4 : Device.FPGA_5, 5: Device.FPGA_6,
                         6 : Device.FPGA_7, 7 : Device.FPGA_8}

    def setUp(self):
        """ Start the mock uniboard script """
        # Check that file exists
        self.assertTrue(os.path.exists(self._mock_script))
        self._uniboard_sim = subprocess.Popen([sys.executable, self._mock_script],
                                               stdout = subprocess.PIPE,
                                               stderr = subprocess.STDOUT)
        sleep(1)

    def tearDown(self):
        """ Ready from unittest, clean up uniboard simulator """
        # Kill uniboard simulator and clean up data files
        if self._uniboard_sim is not None:
            self._uniboard_sim.kill()
            self._uniboard_sim = None
        pass

    def test__convert_node_to_device(self):
        """ Check conversion from node to device """
        nodelist = [(0, 'F'), (1, 'F'), (2, 'F'), (3, 'F'),
                    (4, 'B'), (5, 'B'), (6, 'B'), (7, 'B')]
        unb = UniBoard(nodelist = nodelist)

        # Check that node string combinations return the correct devices
        for (node_num, node_type) in nodelist:
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
        nodelist = [(0, 'F'), (1, 'F'), (2, 'F'), (3, 'F'),
                    (4, 'B'), (5, 'B'), (6, 'B'), (7, 'B')]
        unb = UniBoard(nodelist = nodelist)

        # Check that node string combinations return the correct devices
        for (node_num, node_type) in nodelist:
            # String commands
            self.assertEqual(unb._get_nodes(str(node_num)), self._devices[node_num])
            self.assertEqual(unb._get_nodes("fpga%d" % (node_num + 1)), self._devices[node_num])
            self.assertEqual(unb._get_nodes("node%d" % node_num), self._devices[node_num])

            # Int commands
            self.assertEqual(unb._get_nodes(node_num), self._devices[node_num])

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

    def test_connect(self):
        """ Test UniBoard connection """
        nodelist = [(0, 'F'), (1, 'F'), (2, 'F'), (3, 'F'),
                    (4, 'B'), (5, 'B'), (6, 'B'), (7, 'B')]
        unb = UniBoard(ip="127.0.0.1", port = 50000, nodelist = nodelist)
        self.assertEqual(unb.get_status(), Status.OK)

    def test_write_register(self):
        pass


if __name__ == "__main__":
    main()
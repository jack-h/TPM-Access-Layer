from pyfabil.boards.fpgaboard import FPGABoard, DeviceNames
from pyfabil.base.interface import *
from concurrent import futures
from math import log


class UniBoard(FPGABoard):
    """ FPGABoard subclass for communicating with a UniBoard """

    def __init__(self, **kwargs):
        """ Class constructor """

        # Process nodelist, if passed
        if 'nodelist' not in kwargs.keys():
            raise LibraryError("UniBoard. constructor requires a nodelist")

        # A mapping between node number and FPGABoard device type numbering
        # is required. It is assumed that the nodelist will be in node
        # number ascending order
        self._nodes = { }

        # A UniBoard is composed of a number of nodes, split into front
        # nodes and back nodes. Each type of node generally load the same
        # firmware, so some operations can be performed on all nodes of
        # the same type.
        for i, (node_number, node_type) in enumerate(kwargs['nodelist']):
            if node_type not in ['F', 'B']:
                raise LibraryError("UniBoard. Unrecognised node type %s" % node_type)
            else:
                self._nodes[node_number] = { 'type'   : node_type,
                                             'device' : Device(2**i),
                                             'names'  : [str(node_number), 'FPGA' + str(node_number + 1), 'NODE' + str(node_number)]}

        # Get all node names (and combination of) for faster processing
        self._names = [v for node in self._nodes.values() for v in node['names']]
        self._names.extend(['ALL', 'FRONT', 'BACK'])

        # Create a map between nodes and devices for fast access
        self._device_node_map = { }
        for k, v in self._nodes.iteritems():
            self._device_node_map[v['device']] = k

        # Call super class initialiser
        kwargs['fpgaBoard'] = BoardMake.UniboardBoard
        super(UniBoard, self).__init__(**kwargs)

    def connect(self, ip, port):
        """ Connect to board
        :param ip: Board IP
        :param port: Port to connect to
        """

        # Check if IP is valid, and if a hostname is provided, check whether it
        # exists and get IP address
        import socket
        try:
            socket.inet_aton(ip)
        except socket.error:
            try:
                ip = socket.gethostbyname(ip)
            except socket.gaierror:
                raise BoardError("Provided IP address (%s) is invalid or does not exist")

        # Connect to board
        board_id = call_connect_board(self._fpga_board.value, ip, port)
        if board_id == 0:
            self.status = Status.NetworkError
            raise BoardError("Could not connect to board with ip %s" % ip)
        else:
            self._logger.info(self.log("Connected to board %s, received ID %d" % (ip, board_id)))
            self.id = board_id
            self.status = Status.OK

    def load_firmware_blocking(self, device, filepath):
        """ Override load firmware blocking to be able to specify nodes as well as devices
        :param device: devices or nodes
        :param filepath: Firmware to load
        """

        # Extract nodes
        nodes = self._get_nodes(device)
        nodes = nodes if type(nodes) is list else [nodes]

        # Call load firmware blocking for all specified nodes
        self.status = Status.LoadingFirmware

        self._logger.debug(self.log("Calling load_firmware_blocking"))

        if len(nodes) == 1:
            result = [call_load_firmware(self.id, nodes[0], filepath)]
        else:
            result = []
            # Use thread pool to parallelise calls over nodes
            with futures.ThreadPoolExecutor(max_workers = len(nodes)) as executor:
                for res in executor.map(lambda p: call_load_firmware_blocking(*p), [(self.id, node, filepath) for node in nodes]):
                    result.append(res)

        # If calld succeeded, get register and device list
        if all([r for r in result if result == Error.Success]):
            self._programmed = True
            self.status = Status.OK
            self.get_register_list()
            self.get_device_list()
            self._logger.info(self.log("Successfuly loaded firmware %s on board" % filepath))
        else:
            self._programmed = False
            self.status = Status.LoadingFirmwareError
            raise BoardError("load_firmware_blocking failed on board")

    def write_register(self, register, values, offset = 0, device = None):
        """ Override superclass write register to support multiple nodes on a uniboard
        :param register: The register name. The first component of the register name
                         typically represents the device. In this case, it can also be
                         'all',, 'front' or 'back'
        :param values:   The value to write to the register
        :param offset:   Register offset
        :param device:   List of nodes can be explicitly specified
        :return:
        """

        # Perform basic checks
        if not self._checks():
            return

        # If list of devices is specified, check whether they are valid and get associated nodes
        nodes = None
        if device is not None:
            nodes = self._get_nodes(device)
        else:
            # List of devices not provided, extract device from register name
            try:
                device = register.split('.')[0].upper()
                nodes = self._convert_node_to_device(device)
            except KeyError:
                pass

        # Change nodes to list if it is not already a list
        nodes = nodes if type(nodes) is list else [nodes]

        # Extract device name from register if present
        if register.find('.') > 0:
            if register.split('.')[0].upper() in self._names:
                register = '.'.join(register.split('.')[1:])

        # We need at least one node to check the whether the register is fifo or not
        reg_str = 'fpga%d.%s' % (int(log(nodes[0].value, 2) + 1), register)

        result = []
        if self._registerList[reg_str]['type'] == RegisterType.FifoRegister:
            # Write to be performed on a FIFO register
            if len(nodes) == 1:
                result.append([call_write_fifo_register(self.id, nodes[0], register, values)])
            else:
                # Use thread pool to parallelise calls over nodes
                with futures.ThreadPoolExecutor(max_workers=len(nodes)) as executor:
                    for res in executor.map(lambda p: call_write_fifo_register(*p),
                                            [(self.id, node, register, values) for node in nodes]):
                        result.append(res)
        else:
            # Write to be performed on a normal register or memory block
            if len(nodes) == 1:
                result.append([call_write_register(self.id, nodes[0], register, values)])
            else:
                # Use thread pool to parallelise calls over nodes
                with futures.ThreadPoolExecutor(max_workers=len(nodes)) as executor:
                    for res in executor.map(lambda p: call_write_register(*p),
                                            [(self.id, node, register, values) for node in nodes]):
                        result.append(res)

        self._logger.debug(self.log("Called write_register"))
        if any([True for res in result if res == Error.Failure]):
            raise BoardError("Failed to write_register %s on nodes %s" % (register, ','.join([str(node) for node in nodes])))

    def read_register(self, register, n = 1, offset = 0, device = None):
        """" Get register value
         :param register: The register name. The first component of the register name
                          typically represents the device. In this case, it can also be
                         'all',, 'front' or 'back'
         :param n: Number of words to read
         :param offset: Memory address offset to read from
         :param device: List of nodes can be explicitly specified
         :return: Values
         """

        # Perform basic checks
        if not self._checks():
            return

        # If list of devices is specified, check whether they are valid and get associated nodes
        nodes = None
        if device is not None:
            nodes = self._get_nodes(device)
        else:
            # List of devices not provided, extract device from register name
            try:
                device = register.split('.')[0].upper()
                nodes = self._convert_node_to_device(device)
            except KeyError:
                pass

        # Change nodes to list if it is not already a list
        nodes = nodes if type(nodes) is list else [nodes]

        # Extract device name from register if present
        if register.find('.') > 0:
            if register.split('.')[0].upper() in self._names:
                register = '.'.join(register.split('.')[1:])

        # Get the register type (whether firo or normal)
        register_type = self._registerList['fpga%d.%s' % (int(log(nodes[0].value, 2) + 1), register)]['type']

        result = []
        if register_type == RegisterType.FifoRegister:
            # Write to be performed on a FIFO register
            if len(nodes) == 1:
                values = call_read_fifo_register(self.id, nodes[0], register, n)
                result.append((nodes[0], values.error, values.values))
            else:
                # Use thread pool to parallelise calls over nodes
                with futures.ThreadPoolExecutor(max_workers=len(nodes)) as executor:
                    for node in nodes:
                        result.append((node, executor.submit(lambda p: call_read_fifo_register(*p),
                                                             [self.id, node, register, n])))
        else:
            # Write to be performed on a normal register or memory block
            if len(nodes) == 1:
                values = call_read_register(self.id, nodes[0], register, n)
                result.append((nodes[0], values.error, values.values))
            else:
                # Use thread pool to parallelise calls over nodes
                with futures.ThreadPoolExecutor(max_workers=len(nodes)) as executor:
                    for node in nodes:
                        result.append((node, executor.submit(lambda p: call_read_register(*p),
                                                             [self.id, node, register, n])))


        # Finished reading, process return values
        return_values = []
        if len(nodes) == 1:
            for node, error, values in result:
                if error == Error.Failure:
                    raise BoardError("Failed to read_register %s from node %s" % ('1', '2'))
                else:
                    return_values.append((self._device_node_map[node], error, [values[i] for i in range(n)]))
        else:
            for node, future in result:
                result = future.result()
                if result.error == Error.Failure:
                    raise BoardError("Failed to read_register %s from node %s" % ('1', '2'))
                else:
                    return_values.append((self._device_node_map[node], result.error,
                                          [result.values[i] for i in range(n)]))

        return return_values

    def _convert_node_to_device(self, node):
        """ Convert a node from a nodelist to a device
        :param node: Node
        :return: Device
        """
        node = node.upper()
        if node == 'ALL':     # All nodes
            return [ self._nodes[n]['device'] for n in self._nodes.iterkeys() ]
        elif node == 'FRONT': # Front nodes
            return [ self._nodes[n]['device'] for n in self._nodes.iterkeys()
                     if self._nodes[n]['type'] == 'F']
        elif node == 'BACK':  # Back nodes
            return [ self._nodes[n]['device'] for n in self._nodes.iterkeys()
                     if self._nodes[n]['type'] == 'B']
        else:                  # Specific node
            for i, k in enumerate(self._nodes):
                if node in self._nodes[k]['names']:
                    return self._nodes[k]['device']
        raise LibraryError("Node '%s' contains invalid nodes" % node)

    def _get_nodes(self, nodes):
        """ Check nodes type and whether they are valid
        :param nodes: Nodes to check
        :return: Convert list of devices
        """

        # nodes could be a list of integres or strings
        if type(nodes) in [list, tuple]:
            devs = []
            if type(nodes[0]) is str:
                for entry in nodes:
                    entry = entry.upper()
                    for i, k in enumerate(self._nodes):
                        if entry in self._nodes[k]['names']:
                            devs.append(self._nodes[k]['device'])
            elif type(nodes[0]) is int:
                for node in nodes:
                    devs.append(self._nodes[node]['device'])
            elif type(nodes[0]) is Device:
                return nodes
            else:
                raise LibraryError("Nodes should be int, str, list of int or list of str")
            return devs

        # String representation of a single node
        elif type(nodes) is str:
            return self._convert_node_to_device(nodes)

        # Node number
        elif type(nodes) is int:
            if 0 <= nodes <= 7:
                return self._nodes[nodes]['device']
            else:
                raise LibraryError("Node number should be between 0 and 7, inclusive")

        # Device
        elif type(nodes) is Device:
            return nodes

        # Invalid type
        else:
            raise LibraryError("Nodes should be int, str, list of int or list of str")

    def __getitem__(self, key):
        """ Override __getitem__, return value from board """

        # Run check
        if not self._checks():
            return

        # Check if the specified key is a string
        if type(key) is str:
            return self.read_register(key)
        else:
            raise LibraryError("Unrecognised key type, must be register name")

    def __setitem__(self, key, value):
        """ Override __setitem__, set value on board """

        # Run checks
        if not self._checks():
            return

        # Check if the specified key is a string
        if type(key) is str:
            self.write_register(key, value)
        else:
            raise LibraryError("Unrecognised key type, must be register name")

    def __str__(self):
        """ Override __str__ to print register information in a human readable format """

        if not self._programmed:
            return ""

        # Run checks
        if not self._checks():
            return

        # Split register list into devices
        registers = { }
        for k, v in self._registerList.iteritems():
            if v['device'] not in registers.keys():
                registers[v['device']] = []
            registers[v['device']].append(v)

        # Loop over all devices
        string  = "Device%sRegister%sAddress%sBitmask\n" % (' ' * 2, ' ' * 37, ' ' * 8)
        string += "------%s--------%s-------%s-------\n" % (' ' * 2, ' ' * 37, ' ' * 8)

        for k, v in registers.iteritems():
            for reg in sorted(v, key = lambda arg : arg['name']):
                regspace = ' ' * (45 - len(reg['name']))
                adspace  = ' ' * (15 - len(hex(reg['address'])))
                string += '%s\t%s%s%s%s0x%08X\n' % (DeviceNames[k], reg['name'], regspace, hex(reg['address']), adspace, reg['bitmask'])

        # Return string representation
        return string

if __name__ == "__main__":
    # Simple tests, make sure mock_uniboard.py is running
    nodelist = [(0,'F'), (1,'F'),(2,'F'), (3,'F'), (4,'B'), (5,'B'),(6,'B'), (7,'B')]
    unb = UniBoard(ip = "127.0.0.1", port = 50000, nodelist = nodelist)

    devices = [Device.FPGA_1, Device.FPGA_2, Device.FPGA_3, Device.FPGA_4,
               Device.FPGA_5, Device.FPGA_6, Device.FPGA_7, Device.FPGA_8]
    unb.load_firmware_blocking(devices, "/home/lessju/Code/TPM-Access-Layer/doc/XML/uniboard_map.xml")

    unb.write_register('1.regfile.date_code', 45)
    print unb.read_register('1.regfile.date_code')
    unb['fpga1.regfile.date_code'] = 24
    print unb['fpga1.regfile.date_code']
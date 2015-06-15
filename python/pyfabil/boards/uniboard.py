from pyfabil.boards.fpgaboard import FPGABoard
from pyfabil.base.interface import *


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

    def write_register(self, register, values, offset = 0, device = None):
        """ Override superclass write register to support multiple nodes
            one a uniboard
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

        # Call appropriate function for all devices
        for node in nodes:

            # Call function and return
            if self._registerList[register]['type'] == RegisterType.FifoRegister:
                err = call_write_fifo_register(self.id, node, self._remove_device(register), values)
            else:
                err = call_write_register(self.id, node, self._remove_device(register), values, offset)

            self._logger.debug(self.log("Called write_register for node %s" % str(node)))
            if err == Error.Failure:
                raise BoardError("Failed to write_register %s on node %s" % (register, str(node)))


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
        raise LibraryError("%s contains invalid nodes" % node)

    def _get_nodes(self, nodes):
        """ Check nodes type and whether they are valid
        :param nodes: Nodes to check
        :return: Convert list of devices
        """

        # nodes could be a list of integres or strings
        if type(nodes) in [list, tuple]:
            devices = []
            if type(nodes[0]) is str:
                for entry in nodes:
                    entry = entry.upper()
                    for i, k in enumerate(self._nodes):
                        if entry in self._nodes[k]['names']:
                            devices.append(self._nodes[k]['device'])
            elif type(nodes[0]) is int:
                for node in nodes:
                    devices.append(self._nodes[node]['device'])
            else:
                raise LibraryError("Nodes should be int, str, list of int or list of str")
            return devices

        # String representation of a single node
        elif type(nodes) is str:
            return self._convert_node_to_device(nodes)

        # Node number
        elif type(nodes) is int:
            if 0 <= nodes <= 7:
                return self._nodes[nodes]['device']
            else:
                raise LibraryError("Node number should be between 0 and 7, inclusive")

        # Invalid type
        else:
            raise LibraryError("Nodes should be int, str, list of int or list of str")

if __name__ == "__main__":
    # Simple tests, make sure mock_uniboard.py is running
    nodelist = [(0,'F'), (1,'F'),(2,'F'), (3,'F'), (4,'B'), (5,'B'),(6,'B'), (7,'B')]
    unb = UniBoard(ip = "127.0.0.1", port = 5000, nodelist = nodelist)
    unb.load_firmware_blocking(Device.FPGA_1, "/home/lessju/Code/TPM-Access-Layer/doc/XML/uniboard_map.xml")
    print unb._registerList
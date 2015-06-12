import xml.etree.ElementTree as ET

from pyfabil.boards.fpgaboard import *
from pyfabil.base.definitions import *


# ----------------------- Config Handler --------------------
class ConfigHandler(object):
    """ Helper class for XML configuration files """

    def __init__(self, config):
        """ Initialise class by loading XML file
        :param config: Configuration flile path
        """

        # Check if file exists and is an XML file
        try:
            tree = ET.parse(config)
        except ET.ParseError:
            raise InstrumentError("XML configuration file is malformed")
        except IOError:
            raise InstrumentError("XML configuration file does not exists or is not accessible")

        # Get element root
        root = tree.getroot()

        # Get list of board types implemented in the access layer
        available_boards = [cls.__name__ for cls in sys.modules['accesslayer'].FPGABoard.__subclasses__()]

        # Set class attributes to be populated
        self.instrument = { }
        self.boards = { }

        # Nodes within root can vary, for now we skip unneedeg nodes and
        # only process the <boards> tag
        for child in root:
            if child.tag.lower() == "boards":
                # Process boards tag, which should contain a list of boards
                # the tag name should represent a board type implemented in the access layer
                for board in child:
                    # Check if board is supported
                    if board.tag not in available_boards:
                        raise InstrumentError("Board %s is not supported" % board)

                    # Add board to instance dictionary
                    current_board = { 'board_class' : board.tag }

                    # Update board dict with attributes
                    current_board.update(board.attrib)

                    # Go through board tags
                    for node in board:
                        # If node is a plugin, then create plugins list in dict
                        if node.tag.lower() == "plugins":
                            current_board['plugins'] = { }
                            for plugin in node:
                                current_board['plugins'][plugin.tag] = self.parse_config_node(plugin)
                        else:
                            current_board[node.tag] = self.parse_config_node(node)

                    # Check if board has an id, and is so add to list of boards
                    if 'id' in current_board.keys():
                        self.boards[current_board['id']] = current_board
                    else:
                        raise InstrumentError("Each board must have an associated id tag")
            else:
                self.instrument[child.tag] = self.parse_config_node(child)

    @staticmethod
    def parse_config_node(node):
        """ Parse an XML configuration node
        :param node: The XML node
        :return: Dictionary representing the configuration
        """
        # Add top node attributes to dictionary
        config  = node.attrib

        # Loop over all children
        for n in node:
            # Check if node has children
            if len(n) > 0:
                # Check if tag is already in config
                c = ConfigHandler.parse_config_node(n)
                if n.tag in config.keys():
                    # If tag is already a list, append to it
                    if type(config[n.tag]) is list:
                        config[n.tag].append(c)
                    # Otherwise, convert dict to list
                    else:
                        config[n.tag] = [c, config[n.tag]]
                else:
                    config[n.tag] = c
            else:
                # Check if node contains attributes. If so, then the nodes content
                # will be added as content
                if len(n.attrib) > 0:
                    v = n.attrib
                    v['text'] = n.text
                else:
                    v = n.text

                # Check if tag is already in config
                if n.tag in config.keys():
                    if type(config[n.tag]) is list:
                        config[n.tag].append(v)
                    else:
                        config[n.tag] = [v, config[n.tag]]
                else:
                    config[n.tag] = v

        # All done, return configuration
        return config


# --------------------------- Instrument -----------------------

class Instrument(object):
    """ Instrument class """

    def __init__(self, config_file):
        """ Initialise instrument
        :param config_file: Configuration file
        """

        # Set instrument status
        self.status = Status.LoadingFirmware

        # Parse configuration
        self._config = ConfigHandler(config_file)

        # Check if logging is required, and if so configure
        if 'logging' in self._config.instrument.keys() and eval(self._config.instrument['logging']['enabled']):
                level = logging.WARN if  'level' not in self._config.instrument['logging'] \
                                     else getattr(logging, self._config.instrument['logging']['level'].upper())
                filename =  None if 'filename' not in self._config.instrument['logging'] \
                                 else self._config.instrument['logging']['filename']
                self.configure_logging(log_level= level, log_filename= filename)
        else:
            self._logger = logging.getLogger('dummy')

        # Create board and initialise instances
        self.boards = { }
        for k, v in self._config.boards.iteritems():
            self.boards[k] = eval(v['board_class'])()
            self.boards[k].initialise(v)
            self._logger.info("Initialised board %s, has internal id %d" % (k, self.boards[k].id))

        # Check status
        self.status_check()

        self._logger.info("Initialised intrument")

    def status_check(self):
        """ Check instrument status
        :return: Status
        """

        # Check status of all boards
        status = { }
        for k, v in self.boards.iteritems():
            status[k] = self.boards[k].status_check()

        # Set instrument status
        stat = set([v for k, v in status.iteritems()]) - set([Status.OK])
        if len(stat) == 0:
            self.status = Status.OK
        else:
            self.status = stat.pop()

        return status

    def configure_logging(self, log_filename = None, log_level = logging.DEBUG):
        """ Basic logging configuration
        :param log_filename: Log filename
        :param log_level: Logging level
        """

        # If filename is not specified, create one
        if log_filename is None:
            from datetime import datetime
            log_filename = "instrument_%s.log" % datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

        # Create logger
        self._logger = logging.getLogger()
        self._logger.setLevel(log_level)

        # Create file handler which logs all messages
        fh = logging.FileHandler(log_filename, mode='w')
        fh.setLevel(log_level)

        # Create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)

        # Create formatter and add it to the handlers
        formatter = logging.Formatter('%(levelname)s\t%(asctime)s\t %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)

        # Add the handlers to logger
        self._logger.addHandler(ch)
        self._logger.addHandler(fh)
        self._logger.info("Starting logging")

if __name__ == "__main__":

    # Create instrument
    instrument = Instrument("/home/lessju/Code/TPM-Access-Layer/doc/XML/Instrument.xml")

    # Check instrument status
    print instrument.status_check()


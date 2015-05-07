from accesslayer import *
from definitions import *
import xml.etree.ElementTree as ET

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
        availableBoards = [cls.__name__ for cls in sys.modules['accesslayer'].FPGABoard.__subclasses__()]

        # Set class attributes to be populated
        self.instrument = { }
        self.boards = { }

        # Root element can have any tag, depending on the instrument.
        # This will be ignored for now...
        # Nodes within root can vary, for now we skip unneedeg nodes and
        # only process the <boards> tag
        for child in root:
            if child.tag.lower() == "boards":
                # Process boards tag, which should contain a list of boards
                # the tag name should represent a board type implemented in the access layer
                for board in child:
                    # Check if board is supported
                    if board.tag not in availableBoards:
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
                                current_board['plugins'][plugin.tag] = plugin.attrib
                        else:
                            current_board[node.tag] = node.attrib

                    # Check if board has an id, and is so add to list of boards
                    if 'id' in current_board.keys():
                        self.boards[current_board['id']] = current_board
                    else:
                        raise InstrumentError("Each board must have an associated id tag")
            else:
                self.instrument[child.tag ] = child.attrib

# --------------------------- Logger -----------------------
def configureLogging(log_filename = None, log_level = logging.INFO):
    """ Basic logging configuration
    :param log_filename: Log filename
    :param log_level: Logging level
    """

    # If filename is not specified, create it
    if log_filename is None:
        from datetime import datetime
        log_filename = "instrument_%s.log" % datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

    # Create logger
    logging.basicConfig(format='%(levelname)s\t%(asctime)s\t%(message)s', filename = log_filename, level = log_level)
    logging.info("Starting logging")

# ------------------------------------------------------------

if __name__ == "__main__":

    # Parse configuration
    c = ConfigHandler("/home/lessju/Code/TPM-Access-Layer/doc/XML/Instrument.xml")

    # Check if logging is required, and if so configure
    if 'logging' in c.instrument.keys() and eval(c.instrument['logging']['enabled']):
            level = logging.WARN if  'level' not in c.instrument['logging'] else getattr(logging, c.instrument['logging']['level'].upper())
            filename =  None if 'filename' not in c.instrument['logging'] else c.instrument['logging']['filename']
            configureLogging(log_level= level, log_filename= filename)

    # Create board instances
    board_instances = { }
    for k, v in c.boards.iteritems():
        board_instances = { k : eval(v['board_class'])() }
        board_instances[k].initialise(v)






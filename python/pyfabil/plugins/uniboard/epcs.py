__author__ = 'lessju'

from pyfabil.plugins.firmwareblock import FirmwareBlock
from pyfabil.base.definitions import *
from pyfabil.base.utils import *
import filecmp
import logging

"""Peripheral epcs

  RO  read only  (no VHDL present to access HW in write mode)
  WO  write only (no VHDL present to access HW in read mode)
  WE  write event (=WO)
  WR  write control, read control
  RW  read status, write control
  RC  read, clear on read
  FR  FIFO read
  FW  FIFO write

  wi  Bits    R/W Name              Default  Description             |REG_EPCS|
  =============================================================================
  0   [23..0] WO  addr              0x0      Address to write to/read from
  1   [0]     WO  rden              0x0      Read enable
  2   [0]     WE  read              0x0      Read
  3   [0]     WE  write             0x0      Write
  4   [0]     WO  sector_erase      0x0      Sector erase
  5   [0]     RO  busy              0x0      Busy
  =============================================================================

  Refer to the user guide of Altera's ALTASMI_PARALLEL megafunction for more
  information.
"""

class UniBoardEpcs(FirmwareBlock):
    """ FirmwareBlock tests class """

    @compatibleboards(BoardMake.UniboardBoard)
    @friendlyname('uniboard_epcs')
    @maxinstances(0)
    def __init__(self, board, **kwargs):
        """ UniBoardEpcs initialiser
        :param board: Pointer to board instance
        """
        super(UniBoardEpcs, self).__init__(board)

        self._reg_address = 'REG_EPCS'

        # Get list of nodes
        if 'nodes' not in kwargs.keys():
            raise PluginError("UniBoardDpmm: List of nodes not specified")

        # Check if list of nodes are valid, and are all back-nodes
        self._nodes = self.board._get_nodes(kwargs['nodes'])
        self._nodes = self._nodes if type(self._nodes) is list else [self._nodes]

        # Check if registers are available on all nodes
        for node in self._nodes:
            fpga_number = self.board.device_to_fpga(node)
            register_str = "fpga%d.%s" % (fpga_number, self._reg_address)
            if register_str not in self.board.register_list.keys():
                raise PluginError("UniBoardEpcs: Node %d does not have register %s" % (fpga_number, self._reg_address))

        # Load required modules
        self._dpmm = self.board.load_plugin("UniBoardDpmm", nodes = self._nodes)
        self._mmdp = self.board.load_plugin("UniBoardMmdp", nodes = self._nodes)

         # Register map
        self._reg_addr          = 0
        self._reg_rden          = 1
        self._reg_read          = 2
        self._reg_write         = 3
        self._reg_sector_erase  = 4
        self._reg_busy          = 5
        self._rbf_dir           = '' # TODO: Make this sensible
        self._page_size_bytes   = 256
        self._page_size_words   = self._page_size_bytes/4

        # EPCS flash M25P128 has 64 sectors of 1024 pages of 256 bytes
        self._pages_per_sector  = 1024
        self._factory_sector_start = 0
        self._factory_sector_end   = 23

        # sector 24 is reserved for factory image data
        # sector 25 is reserved for user    image data
        self._user_sector_start    = 26
        self._user_sector_end      = 63
        self._factory_sector_span  = self._factory_sector_end - self._factory_sector_start + 1
        self._user_sector_span     = self._user_sector_end - self._user_sector_start + 1
        self._factory_page_start   = self._factory_sector_start * self._pages_per_sector
        self._user_page_start      = self._user_sector_start * self._pages_per_sector

    #######################################################################################
    def write_rden(self, data = 1):
         self.board.write_register(self._reg_address, data, offset = self._reg_rden, device = self._nodes)

    def write_read(self, data = 1):
        self.board.write_register(self._reg_address, data, offset = self._reg_read, device = self._nodes)

    def write_write(self, data = 1):
         self.board.write_register(self._reg_address, data, offset = self._reg_write, device = self._nodes)

    def write_addr(self, addr = None, page = None):
        if page is not None:
            addr = page * self._page_size_bytes
        self.board.write_register(self._reg_address, addr, offset = self._reg_addr, device = self._nodes)

    def write_sector_erase(self, data=1):
        self.board.write_register(self._reg_address, data, offset = self._reg_sector_erase, device = self._nodes)

    def write_erase_sector(self, sector):
        # We need to write any address in the target sector's address range to select that sector for erase.
        # We'll use the base (lowest) address of the sectors for this: sector 0 starts at 0x0, sector 1 starts
        # at 0x40000 etc.
        self.write_addr(sector * 0x40000)
        self.write_sector_erase()

    def read_busy(self):
        data = self.board.read_register(self._reg_address, offset = self._reg_busy, n = 1, device = self._nodes)
        return [node_data for (node, status, node_data) in data]

    def read_page(self, page = 0):
        addr = page * self._page_size_bytes
        self.write_addr(addr)
        self.write_rden()
        self.write_read()
        do_until_eq(self.read_busy, 0)
        self._dpmm.read_usedw()
        self.read_page_to_file(self._rbf_dir + "/page.bin")
        self.write_rden(0)


    def write_raw_binary_file(self, fact_or_usr, rbf_file):
        rbf = open(rbf_file, "rb")
        if fact_or_usr == "user":
            sector_start = self._user_sector_start
            page_start   = self._user_page_start
            reserved_sector_span = self._user_sector_span
        else:
            sector_start = self._factory_sector_start
            page_start   = self._factory_page_start
            reserved_sector_span = self._factory_sector_span

        # Calculate the required number of pages (RBF file size is rarely a multiple of 256 bytes)
        rbf_size_bytes = os.path.getsize(rbf_file)
        print '(%s) Raw Binary File: %s'  % (fact_or_usr, rbf_file)
        print '    Size: %d bytes' % rbf_size_bytes
        rbf_page_span = ceil_div(rbf_size_bytes, self._page_size_bytes)
        print '    Span: %d pages'%rbf_page_span

        # Convert page span to sector span, call write_erase_sector for this span
        rbf_sector_span =  ceil_div(rbf_page_span, self._pages_per_sector)
        print '    Span: %d sectors'%rbf_sector_span

        if rbf_sector_span>reserved_sector_span:
            print 'ERROR: RBF span (%d sectors) exceeds reserved %s image span (%d sectors) !' % \
                  (rbf_sector_span, fact_or_usr, reserved_sector_span)

        # Erase the sectors we're going to write with the RBF
        print 'Erasing %d sectors...'% rbf_sector_span
        for sector in range(sector_start, sector_start+rbf_sector_span):
            print '    %d of [%d..%d]' % (sector, sector_start, sector_start + rbf_sector_span - 1)
            self.write_erase_sector(sector)
            do_until_eq(self.read_busy, 0)

        # Now write all pages
        print 'Writing %d pages [%d..%d]...' % (rbf_page_span, page_start, page_start + rbf_page_span - 1)
        for page in range(0, rbf_page_span):

            do_until_eq( self.read_busy, 0)
            self.write_addr(page=page_start+page)

            reversed_words = []
            # Write one page to the MM->DP FIFO at a time
            for word in range(0, self._page_size_words):
                # Read a word from the file
                word_read = rbf.read(4)

                # EPCS allows us to write less than the page size, too. So simply break the loop when we've
                # written the entire file, no need to pad the remaining bytes in this page.fact_or_usr
                if not word_read:
                    print '    End of Raw Binary File found after writing word %d in page %d.' % (word - 1, page)
                    print '(%s) Raw Binary File: %s successfully written to flash.'  % (fact_or_usr, rbf_file)
                    break

                if len(word_read) < 4:
                    nof_pad_bytes = 4 - len(word_read)
                    # The last word read might be less than 4 bytes. Pad with null chars.
                    rbf_word = struct.unpack('I', word_read + nof_pad_bytes*'\0' )[0]
                else:
                    rbf_word = struct.unpack('I',  word_read)[0]

                # (bit) reverse and append to our word list
                reversed_words.append(reverse_word(rbf_word))

            # Now write the reversed word list to the MM->DP FIFO
            self._mmdp.write_data(reversed_words)

            # ...and assert 'write'.
            self.write_write()

        rbf.close()

    def read_page_to_file(self, filename):

        data_file = open(filename, "wb")

        print 'Saving one page (256 bytes) from read FIFO to file.'

        # Reverse the bits in the read word. On unix, use 'od -t x4 -w128 [file]' to compare.
        data = self._dpmm.read_data(self._page_size_words)[0]

        for word64 in data:
            reversed_word64 = reverse_word(word64)
            word32 = struct.pack("I", reversed_word64)
            data_file.write(word32)

        data_file.close()


    def read_and_verify_raw_binary_file(self, fact_or_usr, base_rbf_file):

        if fact_or_usr=="user":
            page_start   = self._user_page_start
        else:
            page_start   = self._factory_page_start

        # Open the original RBF that's supposed to be stored in flash
        base_rbf = open(base_rbf_file, "rb")

        # Calculate the required number of pages (RBF file size is rarely a multiple of 256 bytes)
        rbf_size_bytes = os.path.getsize(base_rbf_file)
        print '(%s) Raw Binary File: %s: starting verification' %(fact_or_usr,base_rbf_file)
        print '    Size: %d bytes' % rbf_size_bytes

        rbf_page_span = ceil_div(rbf_size_bytes, self._page_size_bytes)
        print '    Span: %d pages'%rbf_page_span

        print 'Reading %s RBF from flash, saving to file(s) "rbf/.read_ver_[node].rbf".' %fact_or_usr
        print '    Reading %d pages [%d..%d] from %d nodes...' % (rbf_page_span, page_start, page_start + rbf_page_span - 1,
                                                                  len(self._nodes))

        words_to_write = ceil_div(rbf_size_bytes, 4)
        # We write to the file on 32-bit bounaries. If our file size is not an exact multiple of 32-bits,
        # we need to compensate (remove) excess bytes from the last word written to the file.
        excess_bytes = (words_to_write * 4) - rbf_size_bytes

        filenames=[]
        files=[]
        words_written = []

        for node in self._nodes:
            # now create a new binary file that we'll write our flash data to
            filename = self._rbf_dir + "/.read_ver_" + str(node) + ".rbf"
            filenames.append(filename)
            files.append(open(filename, "wb"))
            words_written.append(0)

        for page in range(page_start, page_start+rbf_page_span):

            do_until_eq( self.read_busy, 0)

            # Write address
            self.write_addr(page=page)
            time.sleep(0.0001) # Note: sleeps added because on faster PCs readback failed
            # Read one page size at a time, append to file.
            self.write_rden()
            time.sleep(0.0001)
            self.write_read()
            time.sleep(0.0001)
            self.write_rden(0)
            time.sleep(0.0001)

            # collect this page from all targeted nodes
            data = self._dpmm.read_data(self._page_size_words)

            # write this page to the corresponding file
            for i in range(0, len(self._nodes)):
                for word64 in data[i]:
                    reversed_word64 = reverse_word(word64)
                    word32 = struct.pack("I", reversed_word64)
                    # Stop writing if file size matches base file size
                    if words_written[i] < words_to_write:
                        if words_written[i] == words_to_write-1: # last word; remove any excess bytes
                            files[i].write(word32[0:4-excess_bytes])
                        else:
                            files[i].write(word32)
                        words_written[i] += 1

        base_rbf.close()

        for i in range(0, len(self._nodes)):
            files[i].close()
            print 'Comparing %s to %s.' % (filenames[i], base_rbf_file)

            if filecmp.cmp(filenames[i], base_rbf_file):
                print '    (%s) Raw Binary file %s verified, OK.'%(fact_or_usr, filenames[i])
            else:
                print '    (%s) Raw Binary File %s mismatch!'%(fact_or_usr, filenames[i])

    def write_ver_raw_binary_file(self, fact_or_usr, rbf_file):
        self.write_raw_binary_file(fact_or_usr, rbf_file)
        self.read_and_verify_raw_binary_file(fact_or_usr, rbf_file)

    def read_and_save_raw_binary_file(self, fact_or_usr):

        if fact_or_usr == "user":
            rbf_page_span = self._user_sector_span*self._pages_per_sector
            page_start   = self._user_page_start
        else:
            rbf_page_span = self._factory_sector_span*self._pages_per_sector
            page_start   = self._factory_page_start

        print '(%s) Raw Binary File: read' % fact_or_usr
        print '    Span: %d pages'%rbf_page_span

        print 'Reading %s RBF from flash, saving to file(s) "rbf/.read_sav_[node].rbf".'  % fact_or_usr
        print '    Reading %d pages [%d..%d] from %d nodes...' % (rbf_page_span, page_start, page_start + rbf_page_span - 1,
                                                                  len(self._nodes))

        filenames=[]
        files=[]

        for node in self._nodes:
            # now create a new binary file that we'll write our flash data to
            filename=self._rbf_dir+"/.read_sav_"+str(node)+".rbf"
            filenames.append(filename)
            files.append(open(filename, "wb"))


        for page in range(page_start, page_start+rbf_page_span):

            do_until_eq( self.read_busy, 0)

            # Write address
            self.write_addr(page=page)

            # Read one page size at a time, append to file.
            self.write_rden()
            self.write_read()
            self.write_rden(0)

            # collect this page from all targeted nodes
            data = self._dpmm.read_data(self._page_size_words)

            # write this page to the corresponding file
            for i in range(0, len(self._nodes)):
                for word64 in data[i]:
                    reversed_word64 = reverse_word(word64)
                    word32 = struct.pack("I", reversed_word64)
                    files[i].write(word32)

        print '    Done.'

    ##################### Superclass method implementations #################################

    def initialise(self):
        """ Initialise UniBoardEpcs """

        logging.info("UniBoardEpcs has been initialised")
        return True

    def status_check(self):
        """ Perform status check
        :return: Status
        """
        logging.info("UniBoardEpcs : Checking status")
        return Status.OK

    def clean_up(self):
        """ Perform cleanup
        :return: Success
        """
        logging.info("UniBoardEpcs : Cleaning up")
        return True
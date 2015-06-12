###############################################################################
#
# Copyright (C) 2012
# ASTRON (Netherlands Institute for Radio Astronomy) <http://www.astron.nl/>
# P.O.Box 2, 7990 AA Dwingeloo, The Netherlands
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

"""
This stub will emulate 1 uniboard node.
acces to register, flash and fifo

based on uniboard udp protocol V1.1
"""

import udp
import struct
import array


def unpackPayload(data):
    fmt = "L"*(len(data)/4)
    dd = struct.unpack(fmt,data)
    return dd

def packPayload(data):
    fmt = "L"*(len(data))
    packed_data = struct.pack(fmt,*data)
    return packed_data

def main():
    print "UNI-BOARD node stub"
    eth = udp.Server(5000)
    stub = Node()
    stub.register.save()
    stub.flash.save()
    stub.fifo0.save()
    stub.fifo1.save()

    try:
        print "waiting for data"

        while True:
            data = eth.recv()
            response = packPayload(stub.process(data))
            eth.send(response)
    finally:
        eth.close()


"""
UNIBOARD node communication emulation
author: Pieter Donker (ASTRON)
date: december 2011

node class emulates communication with one uniboard node
read/write to registers, flash and fifo memory is possible
after each write the information is also writen to a file
register --> register.dat
flash    --> flash.dat
fifo0    --> fifo0.dat
fifo1    --> fifo1.dat

based on uniboard udp protocol V1.1

== classes ==
'node' is a class that will emulate communication with a uniboard node
'memory' is the base class for register, fifo and flash
"""

# memory base class
class Memory():
    def __init__(self, memory_size, value_type, preset_value=0):
        self.memory_size = memory_size
        self.preset_value = preset_value
        self.value_type = value_type
        print "mem_size=%d  preset_value=%d  value_type=%c" %(\
                self.memory_size,\
                self.preset_value,\
                self.value_type)
        self.memory = array.array(self.value_type)
        self.resize(memory_size)

    def resize(self, memory_size):
        self.memory_size = len(self.memory)
        if memory_size < self.memory_size:
            while self.memory_size > memory_size:
                self.memory.pop()
                self.memory_size -= 1
        elif memory_size > self.memory_size:
            while memory_size > self.memory_size:
                self.memory.append(self.preset_value)
                self.memory_size += 1

    def preset(self, value=None):
        if value != None:
            self.preset_value = value
        print "mem_size=", self.memory_size
        i = 0
        while i < self.memory_size:
            self.memory[i] = self.presetValue
            i += 1

    def setFileName(self, filename):
        self.file_name= filename

    def save(self):
        fmt = self.value_type * len(self.memory)
        file_data = struct.pack(fmt, *self.memory)
        f = open(self.file_name,"w")
        f.write(file_data)
        f.close()


    def write(self, addr, value):
        if addr < self.memory_size:
            self.memory[addr] = value
            return 0 # ok
        return 1 # error

    def read(self, addr):
        if addr < self.memory_size:
            return self.memory[addr] # ok
        return 1 # error

    def writeBlock(self, addr, values):
        #print values
        for value in values:
            self.write(addr, value)
            addr += 1

    def readBlock(self, addr, nvalues):
        response = []
        for i in range(addr, addr+nvalues, 1):
            response.append(self.read(i))
        #print "readBlock() response=", response
        return response


# memory-fifo
class Fifo(Memory):
    def __init__(self, mem_size, name):
        print "initialize fifo registers"
        Memory.__init__(self, mem_size, 'L', 0x0)
        filename = name+".dat"
        self.setFileName(filename)

    def write(self, values):
        for value in values:
            self.memory[1:] = self.memory[:self.memory_size-1]
            self.memory[0] = value
        return 0 # ok

    def read(self, nvalues):
        values = []
        for i in range(nvalues):
            values.append(self.memory[0])
            self.memory[:self.memory_size-1] = self.memory[1:self.memory_size]
            self.memory[self.memory_size-1] = 0
        return values

# memory-register
class Register(Memory):
    def __init__(self, mem_size):
        print "initialize registers"
        Memory.__init__(self, mem_size, 'L', 0x0)
        self.setFileName("register.dat")


# flash program memory
class Flash(Memory):
    def __init__(self, sections=64, pages_in_section=1024, page_size=256):
        print "initialize flash memory"
        mem_size = sections * pages_in_section * page_size
        Memory.__init__(self, mem_size, 'B', 0xff)
        self.sections = sections
        self.pages_in_section = pages_in_section
        self.page_size = page_size
        self.flash_size = mem_size
        self.setFileName("flash.dat")

    def eraseSection(self, address):
        section = int(address / (self.pages_in_section * self.page_size))
        addr = section * self.pages_in_section * self.page_size
        for i in range(self.pages_in_section * self.page_size):
            self.write(addr, 0xff)
            addr += 1

    def readPage(self, address):
        # look for first addr in page
        addr = int(address / self.page_size) * self.page_size
        return self.readBlock(addr, self.page_size)

    def writePage(self, adress, data):
        if len(data) != self.page_size:
            print "wrong page size"
            return

        # look for first addr in page
        addr = int(address / self.page_size) * self.page_size
        self.writeBlock(addr, data)




class Node():
    # opcodes
    WAIT_PPS     = 0xFFFFFFFF
    MEMORY_READ  = 0x1
    MEMORY_WRITE = 0x2
    MODIFY_AND   = 0x3
    MODIFY_OR    = 0x4
    MODIFY_XOR   = 0x5
    FLASH_WRITE  = 0x6
    FLASH_READ   = 0x7
    FLASH_ERASE  = 0x8
    FIFO_READ    = 0x9
    FIFO_WRITE   = 0xA

    PPS0 = 0x48808083
    PPS1 = 0x49808083

    def __init__(self):
        self.flash = Flash(64, 1024, 256)
        self.register = Register(262144)
        self.fifo0 = Fifo(1024, "fifo0")
        self.fifo1 = Fifo(1024, "fifo1")
        print "Node initialized"
        #self.register.preset(65)

    def setPayload(self, payload):
        self.payload = payload
        self.payload_no = 0

    def getNextByte(self):
        byte = self.payload[self.payload_no]
        self.payload_no += 1
        return byte

    def getNextWord(self):
        data = self.payload[self.payload_no : self.payload_no+4]
        word = struct.unpack("L",data)[0]
        self.payload_no += 4
        return word

    def getRemainsWord(self):
        data = []
        while self.payload_no < len(self.payload):
            data.append(self.getNextWord())
        return data

    def getRemainsByte(self):
        data = []
        while self.payload_no < len(self.payload):
            data.append(self.getNextByte())
        return data

    def process(self, data):
        self.setPayload(data)
        response = []
        psn = self.getNextWord()
        opcode = self.getNextWord()
        print 'opcode=', opcode,

        response.append(psn)

        if opcode == self.WAIT_PPS: # return PPS info
            print "Return PPS info"
            response.append(PPS1)

        elif opcode == self.MEMORY_READ:
            print " (MEMORY_READ)"
            nwords = self.getNextWord()
            address = self.getNextWord()
            print "read %d words starting at address %d" %(nwords, address)
            response.append(address)
            response += self.register.readBlock(address, nwords)

        elif opcode == self.MEMORY_WRITE:
            print " (MEMORY_WRITE)"
            nwords = self.getNextWord()
            address = self.getNextWord()
            print "write %d words starting at address %d" %(nwords, address)
            response.append(address)
            self.register.writeBlock(address, self.getRemainsWord())
            self.register.save()

        elif opcode == self.MODIFY_AND:
            print " (MODIFY_AND)"
            nwords = self.getNextWord()
            address = self.getNextWord()
            print "and %d words starting at address %d" %(nwords, address)
            response.append(address)
            for ri in range(nwords):
                self.register[address] &= self.getNextWord()
                address += 1
            self.register.save()

        elif opcode == self.MODIFY_OR:
            print " (MODIFY_OR)"
            nwords = self.getNextWord()
            address = self.getNextWord()
            print "or %d words starting at address %d" %(nwords, address)
            response.append(address)
            for ri in range(nwords):
                self.register[address] |= self.getNextWord()
                address += 1
            self.register.save()

        elif opcode == self.MODIFY_XOR:
            print " (MODIFY_XOR)"
            nwords = self.getNextWord()
            address = self.getNextWord()
            print "xor %d words starting at address %d" %(nwords, address)
            response.append(address)
            for ri in range(nwords):
                self.register[address] ^= self.getNextWord()
                address += 1
            self.register.save()

        elif opcode == self.FLASH_ERASE:
            print " (FLASH_ERASE)"
            address = self.getNextWord()
            response.append(address)
            self.flash.eraseSection(address)
            self.flash.save()

        elif opcode == self.FLASH_WRITE:
            print " (FLASH_WRITE)"
            address = self.getNextWord()
            response.append(address)
            self.flash.writePage(address, self.getRemainsByte())
            self.flash.save()

        elif opcode == self.FLASH_READ:
            print " (FLASH_READ)"
            address = self.getNextWord()
            response.append(address)
            response += self.flash.readPage(address)

        elif opcode == self.FIFO_READ:
            print " (FIFO_READ)"
            nwords = self.getNextWord()
            address = self.getNextWord()
            if address == 39440:
                print "read %d words from fifo-0" %(nwords)
                response.append(address)
                response += self.fifo0.read(nwords)
                self.fifo0.save()
            elif address == 39448:
                print "read %d words from fifo-1" %(nwords)
                response.append(address)
                response += self.fifo1.read(nwords)
                self.fifo1.save()
            else:
                print "address %d NOT a FIFO address" %(address)

        elif opcode == self.FIFO_WRITE:
            print " (FIFO_WRITE)"
            nwords = self.getNextWord()
            address = self.getNextWord()
            if address == 39440:
                print "write %d words to fifo-0" %(nwords)
                response.append(address)
                self.fifo0.write(self.getRemainsWord())
                self.fifo0.save()
            elif address == 39448:
                print "write %d words to fifo-1" %(nwords)
                response.append(address)
                self.fifo1.write(self.getRemainsWord())
                self.fifo1.save()
            else:
                print "address %d NOT a FIFO address" %(address)

        return response



if __name__ == "__main__":
    main()

import struct

def convert_uint_to_string(data):
    """ Convert list of 32-bit unsigned integers to string"""
    temp = [struct.unpack('BBBB', struct.pack('>I', x)) for x in data]
    return ''.join([chr(b) for a in temp for b in a[::-1]])

def high_bits(datum, bits):
    """ Return location of on bits in datum"""
    result = []
    for i in range(bits):
	if (datum >> i) & 0xF == 1:
	    result.append(i)
    return result

#!/usr/bin/env python
# encoding: utf-8
'''
bplistlib -- read binary .plist files. No write support.

Functions:

These two functions are analagous to the readPlist and readPlistFromString
functions available in plistlib:

readBinaryPlist
readBinaryPlistFromString

These two functions can discriminate between an XML plist file and a binary
plist file, and run the appropriate functions to parse that file:

readAnyPlist
readAnyPlistFromString

----------
bplistlib.py was derived largely from the perl program pluil.pl, version 1.6
which is available under the following terms:

Any use is fine with attribution.

Author: Pete M. Wilson
Website: http://scw.us/iPhone/plutil/
Email: scw@gamewood.net
Copyright: 2007-2008 Starlight Computer Wizardry
'''


import cStringIO
from datetime import datetime
import plistlib
import struct
from time import mktime


class BinaryPlistParser(object):
    '''
    A parser object for binary plist files. Initialize, then parse an open
    file object.
    '''
    def __init__(self, file_object):
        '''Parse an open file object. Seeking needs to be supported.'''
        self.file_object = file_object
        
        self.file_object.seek(-32, 2)
        trailer = struct.unpack('>6xBB4xL4xL4xL', self.file_object.read())
        offset_size = trailer[0]
        self.object_reference_size = trailer[1]
        number_of_objects = trailer[2]
        root_object = trailer[3]
        reference_table_offset = trailer[4]
        
        self.reference_table = []
        formats = (None, 'B', '>H', 'BBB', '>L')
        self.file_object.seek(reference_table_offset)
        for i in range(number_of_objects):
            offset = struct.unpack(formats[offset_size],
                                   self.file_object.read(offset_size))
            if offset_size == 3:
                offset = offset[0] * 0x100 + offset[1] * 0x10 + offset[2]
            else:
                offset = offset[0]
            self.reference_table.append(offset)
        
        self.file_object.seek(self.reference_table[root_object])
    
    def parse(self):
        '''Return the parsed root object.'''
        return self.parse_object()
    
    def parse_object(self):
        '''Read out and parse an object within a binary plist.'''
        # it's worth noting that the type numbers of arrays and dictionaries
        # are mnenomic in hex, 0xa and 0xd. Cute.
        type_parser = (
                       self.parse_boolean,
                       self.parse_int,
                       self.parse_float,
                       self.parse_date,
                       self.parse_binary_data,
                       self.parse_string,
                       self.parse_unicode_string,
                       None,
                       None,
                       None,
                       self.parse_array,
                       None,
                       None,
                       self.parse_dictionary,
        )
        value = struct.unpack('B', self.file_object.read(1))[0]
        object_type = value >> 4
        object_length = value & 0xF
        if ((object_type != 0) and (object_length == 15)):
            object_length = self.parse_object()
        return type_parser[object_type](object_length)
    
    def parse_boolean(self, object_length):
        '''Parse an encoded boolean from a binary plist.'''
        if object_length == 0:
            return None
        elif object_length == 8:
            return False
        elif object_length == 9:
            return True
        else:
            raise ValueError("Unknown Boolean")
    
    def parse_int(self, object_length):
        '''Read out and parse an encoded integer from a binary plist.'''
        raw = self.file_object.read(1 << object_length)
        formats = ('b', '>h', '>l', '>q')
        return struct.unpack(formats[object_length], raw)[0]
    
    def parse_float(self, object_length):
        '''Read out and parse an encoded float from a binary plist.'''
        raw = self.file_object.read(1 << object_length)
        formats = (None, None, 'f', 'd')
        return struct.unpack(formats[object_length], raw[::-1])[0]
    
    def parse_date(self, object_length):
        '''Read out and parse an encoded date from a binary plist'''
        # seconds since 1 January 2001, 0:00:00.0
        raw = self.file_object.read(1 << object_length)
        formats = (None, None, 'f', 'd')
        seconds = struct.unpack(formats[object_length], raw[::-1])[0]
        epoch_adjustment = 978307200.0
        seconds += epoch_adjustment
        return datetime.fromtimestamp(seconds)
    
    def parse_binary_data(self, object_length):
        '''
        Read out binary data from a binary plist. No parsing is performed.
        '''
        return plistlib.Data(self.file_object.read(object_length))
    
    def parse_string(self, object_length):
        '''
        Read out a encoded string from a binary plist. No parsing is performed,
        it should be ascii.
        '''
        raw = self.file_object.read(object_length)
        return raw
    
    def parse_unicode_string(self, object_length):
        '''
        Read out and parse an encoded unicode string from a binary plist. The
        data is parsed as big-endian utf-16.
        '''
        raw = self.file_object.read(object_length * 2)
        return raw.decode('utf_16_be')
    
    def parse_array(self, object_length):
        '''
        Read out and parse an encoded array from a binary plist. Objects within
        the array are recursively parsed as well.
        '''
        object_offsets = []
        formats = (None, 'B', '>H')
        format = formats[self.object_reference_size]
        for i in range(object_length):
            raw = self.file_object.read(self.object_reference_size)
            object_number = struct.unpack(format, raw)[0]
            object_offsets.append(self.reference_table[object_number])
        array = []
        for offset in object_offsets:
            self.file_object.seek(offset)
            obj = self.parse_object()
            array.append(obj)
        return array
    
    def parse_dictionary(self, object_length):
        '''
        Read out and parse an encoded dictionary from a binary plist.
        Objects inside the dictionary are recursively parsed as well.
        '''
        key_offsets = []
        formats = (None, 'B', '>H')
        format = formats[self.object_reference_size]
        for i in range(object_length):
            raw = self.file_object.read(self.object_reference_size)
            object_number = struct.unpack(format, raw)[0]
            key_offsets.append(self.reference_table[object_number])
        value_offsets = []
        for i in range(object_length):
            raw = self.file_object.read(self.object_reference_size)
            object_number = struct.unpack(format, raw)[0]
            value_offsets.append(self.reference_table[object_number])
        mydict = {}
        for key_offset, value_offset in zip(key_offsets, value_offsets):
            self.file_object.seek(key_offset)
            key = self.parse_object()
            self.file_object.seek(value_offset)
            value = self.parse_object()
            mydict.update({key: value})
        return mydict
    

class BinaryPlistWriter(object):
    '''
    A writer object for binary plist files. Initialize with an open file
    object, then write the root object to that file.
    '''
    def __init__(self, file_object):
        '''
        Keep track of the file object, plus some lists that will be needed
        later.
        '''
        self.file_object = file_object
        self.all_objects = []
        self.flattened_objects = {}
        self.offsets = []
        self.reference_size = None
        self.offset_size = None
        self.reference_table_offset = None
    
    def write(self, root_object):
        '''Write the root_object to self.file_object.'''
        self.collect_all_objects(root_object)
        self.flatten()
        self.set_reference_size()
        self.file_object.write('bplist00')
        for object_ in self.all_objects:
            self.file_object.write(self.encode(object_))
        self.file_object.write(self.build_reference_table())
        self.file_object.write(self.build_trailer())
    
    def collect_all_objects(self, object_):
        '''
        Build self.all_objects by recursively walking the tree of objects and
        collecting all unique objects found. An object is unique if no other
        object already in self.all_objects matches it in equality and type.
        '''
        found = False
        for comparison_object in self.all_objects:
            if (type(object_) == type(comparison_object) and
                object_ == comparison_object):
                found = True
                break
        if not found:
            self.all_objects.append(object_)
        if type(object_) == list:
            for item in object_:
                self.collect_all_objects(item)
        elif type(object_) == dict:
            for item in object_.keys() + object_.values():
                self.collect_all_objects(item)
    
    def find_in_all_objects(self, object_):
        '''
        Find an object in self.all_objects, matching equality and type, and
        return the index it was found at. If not found, raise ValueError.
        '''
        for index, comparison_object in enumerate(self.all_objects):
            if (type(object_) == type(comparison_object) and
                object_ == comparison_object):
                return index
        return ValueError
    
    def flatten(self):
        '''
        Take all dictionaries and arrays in self.all_objects and replace each
        child object with the index of that child object in self.all_objects.
        '''
        for item_index, item in enumerate(self.all_objects):
            if type(item) == list:
                flattened_list = []
                for list_item in item:
                    flattened_list.append(self.find_in_all_objects(list_item))
                self.flattened_objects.update({item_index: flattened_list})
            elif type(item) == dict:
                flattened_dict = {}
                for key, value in item.items():
                    key_index = self.find_in_all_objects(key)
                    value_index = self.find_in_all_objects(value)
                    flattened_dict.update({key_index: value_index})
                self.flattened_objects.update({item_index: flattened_dict})
        for index, object_ in self.flattened_objects.items():
            self.all_objects[index] = object_
    
    def get_boolean_length(self, boolean):
        '''Return the object length for a boolean.'''
        if boolean is None:
            return 0
        elif boolean is False:
            return 8
        elif boolean is True:
            return 9
        else:
            raise ValueError
    
    def get_integer_length(self, integer):
        '''Return the object length for an integer.'''
        bit_lengths = [8 * 2 ** x for x in range(4)]
        limits = [2 ** (bit_length - 1) for bit_length in bit_lengths]
        for index, limit in enumerate(limits):
            if -limit <= integer < limit:
                return index
        raise ValueError
    
    def get_float_length(self, float_):
        '''Return the object length for a float.'''
        single_max = (2 - 2 ** (-23)) * (2 ** 127)
        single_min = 2 ** -126
        double_max = (2 - 2 ** (-52)) * (2 ** 1023)
        double_min = 2 ** -1022
        if (-single_max < float_ < single_min or
            single_min < float_ < single_max):
            return 2
        elif (-double_max < float_ < double_min or
              double_min < float_ < double_max):
            return 3
        raise ValueError
    
    def get_date_length(self, seconds):
        '''
        Return the object length for a date already converted to seconds since
        the epoch.
        '''
        return self.get_float_length(seconds)
    
    def get_data_length(self, data):
        '''Return the object length for uninterpreted binary data.'''
        return len(data.data)
    
    def get_string_length(self, string):
        '''Return the object length for an ascii string.'''
        return len(string)
    
    def get_unicode_string_length(self, unicode_):
        '''Return the object length for a unicode string.'''
        return len(unicode_)
    
    def get_array_length(self, array):
        '''Return the object length for an array.'''
        return len(array)
    
    def get_dictionary_length(self, dictionary):
        '''Return the object length for a dictionary.'''
        return len(dictionary)
    
    def set_reference_size(self):
        '''
        Set self.reference size by finding the minimum needed to fit all the
        objects in self.all_objects.
        '''
        number_of_objects = len(self.all_objects)
        if 0 <= number_of_objects < 256:
            self.reference_size = 1
        elif 256 <= number_of_objects < 65535:
            self.reference_size = 2
        else:
            raise ValueError
    
    def encode(self, object_):
        '''Return the encoded form of an object.'''
        encode_functions = {
                            bool: self.encode_boolean,
                            type(None): self.encode_boolean,
                            int: self.encode_integer,
                            float: self.encode_float,
                            datetime: self.encode_date,
                            type(plistlib.Data('')): self.encode_data,
                            str: self.encode_string,
                            unicode: self.encode_unicode_string,
                            list: self.encode_array,
                            dict: self.encode_dictionary,
        }
        encode_object = encode_functions[type(object_)]
        self.offsets.append(self.file_object.tell())
        return encode_object(object_)
    
    def encode_type_length(self, type_number, length):
        '''
        Encode the first byte (or bytes if length is greater than 14) of a an
        encoded object. This encodes the type and length of the object.
        '''
        big = False
        if length >= 15:
            real_length = self.encode_integer(length)
            length = 15
            big = True
        value = (type_number << 4) + length
        encoded = struct.pack('B', value)
        if big:
            return ''.join((encoded, real_length))
        return encoded
    
    def encode_boolean(self, boolean):
        '''Return an encoded boolean value.'''
        type_number = 0
        length = self.get_boolean_length(boolean)
        return self.encode_type_length(type_number, length)
    
    def encode_integer(self, integer):
        '''Return an encoded integer.'''
        type_number = 1
        formats = ('b', '>h', '>l', '>q')
        length = self.get_integer_length(integer)
        type_length = self.encode_type_length(type_number, length)
        body = struct.pack(formats[length], integer)
        return ''.join((type_length, body))
    
    def encode_float(self, float_):
        '''Return an encoded float.'''
        type_number = 2
        formats = (None, None, 'f', 'd')
        length = self.get_float_length(float_)
        type_length = self.encode_type_length(type_number, length)
        body = struct.pack(formats[length], float_)
        return ''.join((type_length, body[::-1]))
    
    def encode_date(self, date):
        '''Return an encoded date.'''
        type_number = 3
        formats = (None, None, 'f', 'd')
        epoch_adjustment = 978307200.0
        seconds = mktime(date.timetuple())
        seconds -= epoch_adjustment
        length = self.get_date_length(seconds)
        type_length = self.encode_type_length(type_number, length)
        body = struct.pack(formats[length], seconds)
        return ''.join((type_length, body[::-1]))
    
    def encode_data(self, data):
        '''Return encoded binary data.'''
        type_number = 4
        length = self.get_data_length(data)
        type_length = self.encode_type_length(type_number, length)
        body = data.data
        return ''.join((type_length, body))
    
    def encode_string(self, string):
        '''Return an encoded string.'''
        type_number = 5
        length = self.get_string_length(string)
        type_length = self.encode_type_length(type_number, length)
        body = string.encode('ascii')
        return ''.join((type_length, body))
    
    def encode_unicode_string(self, unicode_):
        '''Return an encoded unicode string.'''
        type_number = 6
        length = self.get_unicode_string_length(unicode_)
        type_length = self.encode_type_length(type_number, length)
        body = unicode_.encode('utf_16_be')
        return ''.join((type_length, body))
    
    def encode_array(self, array):
        '''Return an encoded array.'''
        type_number = 0xa
        length = self.get_array_length(array)
        type_length = self.encode_type_length(type_number, length)
        encoded_array = [type_length]
        encoded_array += self.encode_reference_list(array, )
        return ''.join(encoded_array)
    
    def encode_dictionary(self, dictionary):
        '''Return an encoded dictionary.'''
        type_number = 0xd
        length = self.get_dictionary_length(dictionary)
        type_length = self.encode_type_length(type_number, length)
        encoded_dictionary = [type_length]
        encoded_dictionary += self.encode_reference_list(dictionary.keys())
        encoded_dictionary += self.encode_reference_list(dictionary.values())
        return ''.join(encoded_dictionary)
    
    def encode_reference_list(self, references):
        '''
        Return an encoded list of reference values. Used in encoding arrays and
        dictionaries.
        '''
        formats = (None, 'B', '>H')
        encoded_references = []
        for reference in references:
            encoded_reference = struct.pack(formats[self.reference_size],
                                            reference)
            encoded_references.append(encoded_reference)
        return encoded_references
    
    def set_offset_size(self):
        '''Set the number of bytes used to store an offset value.'''
        if 0 <= self.reference_table_offset < 0x100:
            self.offset_size = 1
        elif 0x100 <= self.reference_table_offset < 0x10000:
            self.offset_size = 2
        elif 0x10000 <= self.reference_table_offset < 0x1000000:
            self.offset_size = 3
        elif 0x1000000 <= self.reference_table_offset < 0x100000000:
            self.offset_size = 4
        else:
            raise ValueError
    
    def build_reference_table(self):
        '''Return the encoded reference table.'''
        self.reference_table_offset = self.file_object.tell()
        self.set_offset_size()
        formats = (None, 'B', '>H', 'BBB', '>L')
        encoded_table = []
        for offset in self.offsets:
            if self.offset_size == 3:
                first = offset // 0x100
                second = (offset % 0x100) // 0x10
                third = (offset % 0x100) % 0x10
                offset = (first, second, third)
            encoded_offset = struct.pack(formats[self.offset_size], offset)
            encoded_table.append(encoded_offset)
        return ''.join(encoded_table)
    
    def build_trailer(self):
        '''Return the encoded final 32 bytes of a binary plist.'''
        number_of_objects = len(self.all_objects)
        root_object = 0
        return struct.pack('6xBB4xL4xL4xL', self.offset_size,
                            self.reference_size, number_of_objects,
                            root_object, self.reference_table_offset)
    

def read_any_plist(path_or_file):
    '''
    Detect if a given path or file object represents a binary plist file or an
    xml plist file. Call the appropriate function to read the type of plist
    found and return the parsed root object.
    '''
    did_open = False
    if isinstance(path_or_file, (str, unicode)):
        path_or_file = open(path_or_file)
        did_open = True
    if path_or_file.read(8) == 'bplist00':
        root_object = read_binary_plist(path_or_file)
    else:
        path_or_file.seek(0)  # I'm not sure if this is necessary
        root_object = plistlib.readPlist(path_or_file)
    if did_open:
        path_or_file.close()
    return root_object


def read_any_plist_from_string(data):
    '''
    Detect if a given string represents a binary plist or an xml plist. Call
    the appropriate function to parse the string and return the result.
    '''
    if data[:8] == 'bplist00':
        return read_binary_plist_from_string(data)
    else:
        return plistlib.readPlistFromString(data)


def read_binary_plist(path_or_file):
    '''
    Parse a binary plist from a path or file object, and return the root
    object.
    '''
    did_open = False
    if isinstance(path_or_file, (str, unicode)):
        path_or_file = open(path_or_file)
        did_open = True
    parser = BinaryPlistParser(path_or_file)
    root_object = parser.parse()
    if did_open:
        path_or_file.close()
    return root_object


def read_binary_plist_from_string(data):
    '''Parse a binary plist from a string and return the root object.'''
    return read_binary_plist(cStringIO.StringIO(data))


def write_binary_plist(path_or_file, root_object):
    '''
    Write a binary plist representation of the root object to the path or
    file object given.
    '''
    did_open = False
    if isinstance(path_or_file, (str, unicode)):
        path_or_file = open(path_or_file, "w")
        did_open = True
    writer = BinaryPlistWriter(path_or_file)
    writer.write(root_object)
    if did_open:
        path_or_file.close()


def write_binary_plist_to_string(root_object):
    '''
    Encode the given root object as a binary plist and return a string of the
    encoding.
    '''
    string_io_object = cStringIO.StringIO()
    write_binary_plist(string_io_object, root_object)
    return string_io_object.getvalue()

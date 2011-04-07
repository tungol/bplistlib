#!/usr/bin/env python
# encoding: utf-8
'''
bplistlib -- read binary .plist files. No write support.

Functions:

These two functions are analagous to the readPlist and readPlistFromString
functions available in plistlib:

readBPlist
readBPlistFromString

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
import datetime
import plistlib
import struct
from time import mktime


class BPlistParser(object):
    
    def __init__(self):
        pass
    
    def parse(self, fileobj):
        self.fileobj = fileobj
        
        self.fileobj.seek(-32, 2)
        trailer = struct.unpack('>6xBB4xL4xL4xL', self.fileobj.read())
        offset_size = trailer[0]
        self.obj_ref_size = trailer[1]
        num_objects = trailer[2]
        top_object = trailer[3]
        table_offset = trailer[4]
        
        self.offset_table = []
        table_fmts = (None, 'B', '>H', 'BBB', '>L')
        self.fileobj.seek(table_offset)
        for i in range(num_objects):
            offset = struct.unpack(table_fmts[offset_size],
                                   self.fileobj.read(offset_size))
            if offset_size == 3:
                offset = offset[0] * 0x100 + offset[1] * 0x10 + offset[2]
            else:
                offset = offset[0]
            self.offset_table.append(offset)
        
        self.fileobj.seek(self.offset_table[top_object])
        return self.parse_object()
    
    def parse_object(self):
        # it's worth noting that the type numbers of arrays and dictionaries
        # are mnenomic in hex, 0xa and 0xd. Cute.
        type_parser = (
                       self.parse_boolean,
                       self.parse_int,
                       self.parse_real,
                       self.parse_date,
                       self.parse_binary_data,
                       self.parse_byte_string,
                       self.parse_unicode_string,
                       None,
                       None,
                       None,
                       self.parse_array,
                       None,
                       None,
                       self.parse_dictionary,
        )
        value = struct.unpack('B', self.fileobj.read(1))[0]
        obj_type = value >> 4
        obj_len = value & 0xF
        if ((obj_type != 0) and (obj_len == 15)):
            obj_len = self.parse_object()
        return type_parser[obj_type](obj_len)
    
    def parse_boolean(self, obj_len):
        if obj_len == 0:
            return None
        elif obj_len == 8:
            return False
        elif obj_len == 9:
            return True
        else:
            raise ValueError("Unknown Boolean")
    
    def parse_int(self, obj_len):
        raw = self.fileobj.read(1 << obj_len)
        packs = ('b', '>h', '>l', '>q')
        return struct.unpack(packs[obj_len], raw)[0]
    
    def parse_real(self, obj_len):
        raw = self.fileobj.read(1 << obj_len)
        packs = (None, None, 'f', 'd')
        return struct.unpack(packs[obj_len], raw[::-1])[0]
    
    def parse_date(self, obj_len):
        # seconds since 1 January 2001, 0:00:00.0
        raw = self.fileobj.read(1 << obj_len)
        packs = (None, None, 'f', 'd')
        seconds = struct.unpack(packs[obj_len], raw[::-1])[0]
        epoch_adjustment = 978307200.0
        seconds += epoch_adjustment
        return datetime.fromtimestamp(seconds)
    
    def parse_binary_data(self, obj_len):
        return plistlib.Data(self.fileobj.read(obj_len))
    
    def parse_byte_string(self, obj_len):
        raw = self.fileobj.read(obj_len)
        return raw.decode('ascii')
    
    def parse_unicode_string(self, obj_len):
        raw = self.fileobj.read(obj_len * 2)
        return raw.decode('utf_16_be')
    
    def parse_array(self, obj_len):
        object_offsets = []
        packs = (None, 'B', '>H')
        for i in range(obj_len):
            obj_num = struct.unpack(packs[self.obj_ref_size],
                                    self.fileobj.read(self.obj_ref_size))[0]
            object_offsets.append(self.offset_table[obj_num])
        array = []
        for offset in object_offsets:
            self.fileobj.seek(offset)
            obj = self.parse_object()
            array.append(obj)
        return array
    
    def parse_dictionary(self, obj_len):
        key_offsets = []
        packs = (None, 'B', '>H')
        for i in range(obj_len):
            obj_num = struct.unpack(packs[self.obj_ref_size],
                                    self.fileobj.read(self.obj_ref_size))[0]
            key_offsets.append(self.offset_table[obj_num])
        value_offsets = []
        for i in range(obj_len):
            obj_num = struct.unpack(packs[self.obj_ref_size],
                                    self.fileobj.read(self.obj_ref_size))[0]
            value_offsets.append(self.offset_table[obj_num])
        mydict = {}
        for key_offset, value_offset in zip(key_offsets, value_offsets):
            self.fileobj.seek(key_offset)
            key = self.parse_object()
            self.fileobj.seek(value_offset)
            value = self.parse_object()
            mydict.update({key: value})
        return mydict
    

class BPlistWriter(object):
    
    def __init__(self, fileobj):
        self.fileobj = fileobj
        self.all_objects = []
        self.flattened_objects = {}
    
    def write(self, root_object):
        self.collect_all_objects(root_object)
        self.flatten()
        self.set_reference_size()
        self.fileobj.write('bplist00')
        for object_ in self.all_objects:
            self.fileobj.write(self.encode(object_))
        self.fileobj.write(self.build_reference_table())
        self.fileobj.write(self.build_trailer())
    
    def collect_all_objects(self, object_):
        if object_ not in self.all_objects:
            self.all_objects.append(object_)
        if type(object_) == list:
            for item in list:
                self.collect_all_objects(item)
        elif type(object_) == dict:
            for item in object_.keys() + object_.values():
                self.collect_all_objects(item)
    
    def flatten(self):
        for item_index, item in enumerate(self.all_objects):
            if type(item) == list:
                flattened_list = []
                for list_item in item:
                    flattened_list.append(self.all_objects.index(list_item))
                self.flattened_objects.update({item_index: flattened_list})
            elif type(item) == dict:
                flattened_dict = {}
                for key, value in item[:].items():
                    key_index = self.all_objects.index(key)
                    value_index = self.all_objects.index(value)
                    flattened_dict.update({key_index: value_index})
                self.flattened_objects.update({item_index: flattened_dict})
        for index, object_ in self.flattened_objects.values():
            self.all_objects[index] = object_
    
    def get_boolean_length(self, boolean):
        if boolean is None:
            return 0
        elif boolean is False:
            return 8
        elif boolean is True:
            return 9
        else:
            raise ValueError
    
    def get_integer_length(self, integer):
        bit_lengths = [8 * (2 ** x - 1) for x in range(4)]
        limits = [2 ** bit_length - 1 for bit_length in bit_lengths]
        for index, limit in limits:
            if -limit <= integer < limit:
                return index
        raise ValueError
    
    def get_float_length(self, float_):
        single_max = (2 - 2 ** (-23)) * (2 ** 127)
        single_min = 2 ** -126
        double_max = (2 - 2 ** (-52)) * (2 ** 1023)
        double_min = 2 ** -1022
        if (-single_max < float_ < single_min and
            single_min < float_ < single_max):
            return 2
        elif (-double_max < float_ < double_min and
              double_min < float_ < double_max):
            return 3
        raise ValueError
    
    def get_date_length(self, seconds):
        return self.get_float_length(seconds)
    
    def get_data_length(self, data):
        return len(data.data)
    
    def get_string_length(self, string):
        return len(string)
    
    def get_unicode_length(self, unicode_):
        return len(unicode_) * 2
    
    def get_array_length(self, array):
        return len(array)
    
    def get_dictionary_length(self, dictionary):
        return len(dictionary) * 2
    
    def set_reference_size(self):
        number_of_objects = len(self.all_objects)
        if 0 <= number_of_objects < 256:
            self.reference_size = 1
        elif 256 <= number_of_objects < 65535:
            self.reference_size = 2
        else:
            raise ValueError
    
    def encode(self, object_):
        encode_functions = {
                            bool: self.encode_boolean,
                            None: self.encode_boolean,
                            int: self.encode_integer,
                            float: self.encode_float,
                            datetime: self.encode_date,
                            plistlib.Data: self.encode_data,
                            str: self.encode_string,
                            unicode: self.encode_unicode,
                            list: self.encode_array,
                            dict: self.encode_dictionary,
        }
        encode_object = encode_functions[type(object_)]
        return encode_object(object_)
    
    def encode_type_length(self, type_number, length):
        value = type_number << 4 + length
        return struct.pack('B', value)
    
    def encode_boolean(self, boolean):
        type_number = 0
        length = self.get_boolean_length(boolean)
        return self.encode_type_length(type_number, length)
    
    def encode_integer(self, integer):
        type_number = 1
        packs = ('b', '>h', '>l', '>q')
        length = self.get_integer_length(integer)
        type_length = self.encode_type_length(type_number, length)
        body = struct.pack(packs[length], integer)
        return ''.join((type_length, body))
    
    def encode_float(self, float_):
        type_number = 2
        packs = (None, None, 'f', 'd')
        length = self.get_float_length(float_)
        type_length = self.encode_type_length(type_number, length)
        body = struct.pack(packs[length], float_)
        return ''.join((type_length, body))
    
    def encode_date(self, date):
        type_number = 3
        packs = (None, None, 'f', 'd')
        epoch_adjustment = 978307200.0
        seconds = mktime(date.timetuple())
        seconds -= epoch_adjustment
        length = self.get_date_length(date)
        type_length = self.encode_type_length(type_number, length)
        body = struct.pack(packs[length], seconds)
        return ''.join((type_length, body))
    
    def encode_data(self, data):
        type_number = 4
        length = self.get_data_length(data)
        type_length = self.encode_type_length(type_number, length)
        body = data.data
        return ''.join((type_length, body))
    
    def encode_string(self, string):
        type_number = 5
        length = self.get_string_length(string)
        type_length = self.encode_type_length(type_number, length)
        body = string.encode('ascii')
        return ''.join((type_length, body))
    
    def encode_unicode(self, unicode_):
        type_number = 6
        length = self.get_unicode_length(unicode_)
        type_length = self.encode_type_length(type_number, length)
        body = unicode_.encode('utf16-be')
        return ''.join((type_length, body))
    
    def encode_array(self, array):
        type_number = 0xa
        length = self.get_array_length(array)
        type_length = self.encode_type_length(type_number, length)
        encoded_array = [type_length]
        encoded_array += self.encode_reference_list(array)
        return ''.join(encoded_array)
    
    def encode_dictionary(self, dictionary):
        type_number = 0xd
        length = self.get_dictionary_length(dictionary)
        type_length = self.encode_type_length(type_number, length)
        encoded_dictionary = [type_length]
        encoded_dictionary += self.encode_reference_list(dictionary.keys())
        encoded_dictionary += self.encode_reference_list(dictionary.values())
        return ''.join(encoded_dictionary)
    
    def encode_reference_list(self, references):
        packs = (None, 'B', '>H')
        encoded_references = []
        for reference in references:
            encoded_reference = struct.pack(packs[self.object_reference_size],
                                            reference)
            encoded_references.append(encoded_reference)
        return encoded_references
    

def readAnyPlist(pathOrFile):
    didOpen = False
    if isinstance(pathOrFile, (str, unicode)):
        pathOrFile = open(pathOrFile)
        didOpen = True
    if pathOrFile.read(8) == 'bplist00':
        rootObject = readBPlist(pathOrFile)
    else:
        pathOrFile.seek(0)  # I'm not sure if this is necessary
        rootObject = plistlib.readPlist(pathOrFile)
    if didOpen:
        pathOrFile.close()
    return rootObject


def readAnyPlistFromString(data):
    if data[:8] == 'bplist00':
        return readBPlistFromString(data)
    else:
        return plistlib.readPlistFromString(data)


def readBPlist(pathOrFile):
    didOpen = False
    if isinstance(pathOrFile, (str, unicode)):
        pathOrFile = open(pathOrFile)
        didOpen = True
    p = BPlistParser()
    rootObject = p.parse(pathOrFile)
    if didOpen:
        pathOrFile.close()
    return rootObject


def readBPlistFromString(data):
    return readBPlist(cStringIO.StringIO(data))


def writeBPlist(pathOrFile, rootObject):
    didOpen = 0
    if isinstance(pathOrFile, (str, unicode)):
        pathOrFile = open(pathOrFile, "w")
        didOpen = 1
    writer = BPlistWriter(pathOrFile)
    writer.write(rootObject)
    if didOpen:
        pathOrFile.close()


def writeBPlistToString(rootObject):
    f = cStringIO.StringIO()
    writeBPlist(rootObject, f)
    return f.getvalue()

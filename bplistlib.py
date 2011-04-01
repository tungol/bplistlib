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

# converted from plutil.pl <http://scw.us/iPhone/plutil/>

__licence__ = '''
Copyright (c) 2011, Stephen Morton
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright holder nor the
      names of other contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

__version__ = '0.1'

__author__ = 'Stephen Morton'

__all__ = ['readAnyPlist', 'readBPlist', 'readAnyPlistFromString',
           'readBPlistFromString', 'writeBPlist', 'writeBPlistToString',
           'Data']

import cStringIO
import datetime
import plistlib
import struct


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
        self.set_lengths()
        self.fileobj.write('bplist00')
        for item in self.all_objects:
            self.fileobj.write(self.encode(item))
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
                self.flattened_objects.update{item_index: flattened_list}
            elif type(item) == dict:
                flattened_dict = {}
                for key, value in a[:].items():
                    key_index = self.all_objects.index(key)
                    value_index = self.all_objects.index(value)
                    flattened_dict.update{key_index: value_index}
                self.flattened_objects.update{item_index: flattened_dict}
        for index, object_ in self.flattened_objects.values():
            self.all_objects[index] = object_
    

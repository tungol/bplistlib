# encoding: utf-8
'''
This file contains classes that know how to handle various different parts of
a binary plist file.
'''

from struct import pack, unpack
from datetime import datetime
from plistlib import Data
from time import mktime
from .functions import find_with_type, get_byte_width


class BaseHandler(object):
    '''A base class for object handlers. Does pretty much nothing itself.'''
    
    def __init__(self):
        '''
        These values should be overwritten by subclasses. They are here to show
        what's needed as a minimum.
        '''
        self.type_number = None
        self.types = None
    
    def get_object_length(self, object_):
        '''Hook for calculating the object length of the object.'''
        return len(object_)
    
    def get_byte_length(self, object_length):
        '''
        Hook for conversion between the object length and the byte length.
        '''
        return object_length
    
    def encode_body(self, object_, object_length):
        '''Hook for encoding the body of the object.'''
        return ''
    
    def decode_body(self, raw, object_length):
        '''Hook for decoding the body of an encoded object.'''
        return raw
    
    def unflatten(self, object_, objects):
        '''Hook for unflattening object_ in the context of objects.'''
        return object_
    

class BooleanHandler(BaseHandler):
    '''Handler for boolean types in a binary plist.'''
    
    def __init__(self):
        '''Nothing to see here.'''
        BaseHandler.__init__(self)
        self.type_number = 0
        self.types = (bool, type(None))
        self.integer_to_boolean = {0: None, 8: False, 9: True}
        self.boolean_to_integer = dict(zip(self.integer_to_boolean.values(),
                                           self.integer_to_boolean.keys()))
    
    def get_object_length(self, boolean):
        '''Return the object length for a boolean.'''
        return self.boolean_to_integer[boolean]
    
    def get_byte_length(self, object_length):
        '''The byte length for a boolean is always zero.'''
        return 0
    
    def decode_body(self, raw, object_length):
        '''Return the decoded boolean value.'''
        return self.integer_to_boolean[object_length]
    

class NumberHandler(BaseHandler):
    '''Base class for the different numerical types.'''
    
    def __init__(self):
        '''Nothing to see here.'''
        BaseHandler.__init__(self)
        # Subclasses should overwrite this:
        self.formats = None
    
    def encode_body(self, value, object_length):
        '''Pack the given number appropriately for the object length.'''
        value = self.preprocess(value)
        body = pack(self.formats[object_length], value)
        body = self.process_bytes(body)
        return body
    
    def decode_body(self, raw, object_length):
        '''Unpack the encoded number appropriately for the object length.'''
        raw = self.process_bytes(raw)
        body = unpack(self.formats[object_length], raw)[0]
        body = self.postprocess(body)
        return body
    
    def process_bytes(self, bytes_):
        '''Hook for floats to reverse the byte order.'''
        return bytes_
    
    def get_byte_length(self, object_length):
        '''Calculate the byte length from the object length for a number.'''
        return 1 << object_length
    
    def postprocess(self, body):
        '''Hook to convert from floats to date objects.'''
        return body
    
    def preprocess(self, value):
        '''Hook to convert from date objects to floats.'''
        return value
    

class IntegerHandler(NumberHandler):
    '''Handler class for integers. Subclass of the number handler.'''
    
    def __init__(self):
        '''Nothing to see here.'''
        NumberHandler.__init__(self)
        self.type_number = 1
        self.formats = ('b', '>h', '>l', '>q')
        self.types = int
    
    def get_object_length(self, integer):
        '''Return the object length for an integer.'''
        bit_lengths = [8 * 2 ** x for x in range(4)]
        limits = [2 ** (bit_length - 1) for bit_length in bit_lengths]
        for index, limit in enumerate(limits):
            if -limit <= integer < limit:
                return index
        raise ValueError
    

class FloatHandler(NumberHandler):
    '''Handler class for floats. Subclass of the number handler.'''
    
    def __init__(self):
        '''Nothing to see here.'''
        NumberHandler.__init__(self)
        self.type_number = 2
        self.formats = (None, None, 'f', 'd')
        self.types = float
    
    def get_object_length(self, float_):
        '''Return the object length for a float.'''
        float_ = self.preprocess(float_)
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
    
    def process_bytes(self, bytes_):
        '''Reverse the byte order.'''
        return bytes_[::-1]
    

class DateHandler(FloatHandler):
    '''
    Handler class for dates. Subclass of the float handler because dates are
    stored internally as the floating point number of seconds since the epoch.
    '''
    
    def __init__(self):
        '''Nothing to see here.'''
        FloatHandler.__init__(self)
        self.type_number = 3
        # seconds between 1 Jan 1970 and 1 Jan 2001
        self.epoch_adjustment = 978307200.0
        self.types = datetime
    
    def preprocess(self, date):
        '''Convert a datetime object to seconds since 1 Jan 2001.'''
        seconds = mktime(date.timetuple())
        return seconds - self.epoch_adjustment
    
    def postprocess(self, seconds):
        '''Convert seconds since 1 Jan 2001 to a datetime object.'''
        seconds += self.epoch_adjustment
        return datetime.fromtimestamp(seconds)
    

class DataHander(BaseHandler):
    '''Handler class for arbitrary binary data. Uses plistlib.Data.'''
    
    def __init__(self):
        '''Nothing to see here.'''
        BaseHandler.__init__(self)
        self.type_number = 4
        # this is ugly but maintains interop with plistlib.
        self.types = type(Data(''))
    
    def get_object_length(self, data):
        '''Get the length of the data stored inside the Data object.'''
        return len(data.data)
    
    def encode_body(self, data, object_length):
        '''Get the binary data from the Data object.'''
        return data.data
    
    def decode_body(self, raw, object_length):
        '''Store the binary data in a Data object.'''
        return Data(raw)
    

class StringHandler(BaseHandler):
    '''Handler class for strings.'''
    
    def __init__(self):
        '''Nothing to see here.'''
        BaseHandler.__init__(self)
        self.type_number = 5
        self.encoding = 'ascii'
        self.types = str
    
    def encode_body(self, string, object_length):
        '''Return the encoded version of string, according to self.encoding.'''
        return string.encode(self.encoding)
    

class UnicodeStringHandler(StringHandler):
    '''Handler class for unicode strings. Subclass of the string handler.'''
    
    def __init__(self):
        '''Nothing to see here.'''
        StringHandler.__init__(self)
        self.type_number = 6
        self.encoding = 'utf_16_be'
        self.types = unicode
    
    def get_byte_length(self, object_length):
        '''Return twice the object length.'''
        return object_length * 2
    
    def decode_body(self, raw, object_length):
        '''Decode the raw string according to self.encoding.'''
        return raw.decode(self.encoding)
    

class ReferencesHandler(object):
    '''A handler class for lists of references.'''
    
    def __init__(self):
        self.formats = (None, 'B', 'H')
        self.endian = '>'
        self.format = None
        self.reference_size = None
    
    def set_reference_size(self, reference_size):
        '''Save the given reference size, and set self.format appropriately.'''
        self.reference_size = reference_size
        self.format = self.formats[reference_size]
    
    def encode(self, references):
        '''
        Return an encoded list of reference values. Used in encoding arrays and
        dictionaries.
        '''
        format_ = self.endian + self.format * len(references)
        encoded = pack(format_, *references)
        return encoded
    
    def decode(self, raw, object_length):
        '''Decode the given reference list.'''
        format_ = self.format * object_length
        references = unpack(format_, raw)
        return list(references)
    
    def flatten(self, object_list, objects):
        '''Convert a list of objects to a list of references.'''
        reference_list = []
        for object_ in object_list:
            reference = find_with_type(object_, objects)
            reference_list.append(reference)
        return reference_list
    
    def unflatten(self, references, objects, object_handler):
        '''Convert a list of references to a list of objects.'''
        object_list = []
        for reference in references:
            item = objects[reference]
            item = object_handler.unflatten(item, objects)
            object_list.append(item)
        return object_list
    

class ArrayHandler(BaseHandler):
    '''Handler class for arrays.'''
    
    def __init__(self, object_handler):
        '''Nothing to see here.'''
        BaseHandler.__init__(self)
        self.type_number = 0xa
        self.types = list
        self.object_handler = object_handler
        self.references_handler = object_handler.references_handler
    
    def get_byte_length(self, object_length):
        '''Return the object length times the reference size.'''
        return object_length * self.references_handler.reference_size
    
    def encode_body(self, array, object_length):
        '''Encode the flattened array as a single reference list.'''
        return self.references_handler.encode(array)
    
    def decode_body(self, raw, object_length):
        '''Decode the reference list into a flattened array.'''
        return self.references_handler.decode(raw, object_length)
    
    def flatten(self, array, objects):
        '''Flatten the array into a list of references.'''
        return self.references_handler.flatten(array, objects)
    
    def unflatten(self, array, objects):
        '''Unflatten the list of references into a list of objects.'''
        return self.references_handler.unflatten(array, objects,
                                               self.object_handler)
    
    def collect_children(self, array, objects):
        '''Collect all the items in the array.'''
        for item in array:
            self.object_handler.collect_objects(item, objects)
    

class DictionaryHandler(BaseHandler):
    '''Handler class for dictionaries. Subclasses the container handler.'''
    
    def __init__(self, object_handler):
        '''Nothing to see here.'''
        BaseHandler.__init__(self)
        self.type_number = 0xd
        self.types = dict
        self.object_handler = object_handler
        self.references_handler = object_handler.references_handler
    
    def get_byte_length(self, object_length):
        '''Return twice the object length times the reference size.'''
        return object_length * self.references_handler.reference_size * 2
    
    def encode_body(self, dictionary, object_length):
        '''Encode the flattened dictionary as two reference lists.'''
        keys = self.references_handler.encode(dictionary.keys())
        values = self.references_handler.encode(dictionary.values())
        return ''.join((keys, values))
    
    def decode_body(self, raw, object_length):
        '''
        Decode the two reference lists in raw into a flattened dictionary.
        '''
        half = object_length * self.references_handler.reference_size
        keys = self.references_handler.decode(raw[:half], object_length)
        values = self.references_handler.decode(raw[half:], object_length)
        return dict(zip(keys, values))
    
    def flatten(self, dictionary, objects):
        '''Flatten a dictionary into a dictionary of references.'''
        keys = self.references_handler.flatten(dictionary.keys(), objects)
        values = self.references_handler.flatten(dictionary.values(), objects)
        return dict(zip(keys, values))
    
    def unflatten(self, dictionary, objects):
        '''Unflatten a dictionary into a dictionary of objects.'''
        keys = self.references_handler.unflatten(dictionary.keys(), objects,
                                                 self.object_handler)
        values = self.references_handler.unflatten(dictionary.values(),
                                                   objects,
                                                   self.object_handler)
        return dict(zip(keys, values))
    
    def collect_children(self, dictionary, objects):
        '''Collect all the keys and values in dictionary.'''
        for item in dictionary.keys() + dictionary.values():
            self.object_handler.collect_objects(item, objects)
    

class ObjectHandler(object):
    '''A master handler class for all of the object handler classes.'''
    
    def __init__(self):
        '''Intialize one of every (useful) handler class.'''
        self.references_handler = ReferencesHandler()
        handlers = [BooleanHandler(), IntegerHandler(), FloatHandler(),
                    DateHandler(), DataHander(), StringHandler(),
                    UnicodeStringHandler(), ArrayHandler(self),
                    DictionaryHandler(self)]
        self.handlers_by_type_number = {}
        self.handlers_by_type = {}
        for handler in handlers:
            self.handlers_by_type_number.update({handler.type_number: handler})
            if type(handler.types) == type:
                self.handlers_by_type.update({handler.types: handler})
            else:
                for type_ in handler.types:
                    self.handlers_by_type.update({type_: handler})
    
    def set_reference_size(self, reference_size):
        '''Set the reference size on the references handler.'''
        self.references_handler.set_reference_size(reference_size)
    
    def encode(self, object_):
        '''Use the appropriate handler to encode the given object.'''
        handler = self.handlers_by_type[type(object_)]
        object_length = handler.get_object_length(object_)
        first_byte = self.encode_first_byte(handler.type_number, object_length)
        body = handler.encode_body(object_, object_length)
        return ''.join((first_byte, body))
    
    def decode(self, file_object):
        '''Start reading in file_object, and decode the object found.'''
        object_type, object_length = self.decode_first_byte(file_object)
        handler = self.handlers_by_type_number[object_type]
        byte_length = handler.get_byte_length(object_length)
        raw = file_object.read(byte_length)
        return handler.decode_body(raw, object_length)
    
    def flatten_objects(self, objects):
        '''Flatten all objects in objects.'''
        flattened_objects = {}
        for item_index, item in enumerate(objects):
            if type(item) in (list, dict):
                flattened = self.flatten(item, objects)
                flattened_objects.update({item_index: flattened})
        for index, object_ in flattened_objects.items():
            objects[index] = object_
    
    def flatten(self, object_, objects):
        '''Flatten the given object, using the appropriate handler.'''
        handler = self.handlers_by_type[type(object_)]
        return handler.flatten(object_, objects)
    
    def unflatten(self, object_, objects):
        '''Unflatten the give object, using the appropriate handler.'''
        handler = self.handlers_by_type[type(object_)]
        return handler.unflatten(object_, objects)
    
    def encode_first_byte(self, type_number, length):
        '''
        Encode the first byte (or bytes if length is greater than 14) of a an
        encoded object. This encodes the type and length of the object.
        '''
        big = False
        if length >= 15:
            real_length = self.encode(length)
            length = 15
            big = True
        value = (type_number << 4) + length
        encoded = pack('B', value)
        if big:
            return ''.join((encoded, real_length))
        return encoded
    
    def decode_first_byte(self, file_object):
        '''
        Get the type number and object length from the first byte of an object.
        '''
        value = unpack('B', file_object.read(1))[0]
        object_type = value >> 4
        object_length = value & 0xF
        if object_length == 15:
            object_length = self.decode(file_object)
        return object_type, object_length
    
    def collect_objects(self, object_, objects):
        '''
        Collect all the objects in object_ into objects, using the appropriate
        handler.
        '''
        try:
            find_with_type(object_, objects)
        except ValueError:
            objects.append(object_)
            if type(object_) in (dict, list):
                handler = self.handlers_by_type[type(object_)]
                handler.collect_children(object_, objects)
    

class TableHandler(object):
    '''A handler class for the offset table found in binary plists.'''
    
    def __init__(self):
        '''Nothin to see here.'''
        self.formats = (None, 'B', 'H', 'BBB', 'L')
        self.endian = '>'
    
    def decode(self, file_object, offset_size, length, table_offset):
        '''
        Decode the offset table in file_object. Returns a list of offsets.
        '''
        file_object.seek(table_offset)
        offset_format = self.formats[offset_size]
        table_format = self.endian + offset_format * length
        raw = file_object.read(offset_size * length)
        offsets = unpack(table_format, raw)
        if offset_size == 3:
            zip_args = [offsets[x::3] for x in range(3)]
            offsets = zip(*zip_args)
            offsets = [o[0] * 0x10000 + o[1] * 0x100 + o[2] for o in offsets]
        return offsets
    
    def encode(self, offsets):
        '''Return the encoded form of a list of offsets.'''
        offset_size = get_byte_width(max(offsets), 4)
        offset_format = self.formats[offset_size]
        table_format = self.endian + offset_format * len(offsets)
        if offset_size == 3:
            new_offsets = []
            for offset in offsets[:]:
                first = offset // 0x10000
                second = (offset % 0x10000) // 0x100
                third = (offset % 0x10000) % 0x100
                new_offsets += [first, second, third]
            offsets = new_offsets
        encoded = pack(table_format, *offsets)
        return encoded
    

class TrailerHandler(object):
    '''A handler class for the 'trailer' found in binary plists.'''
    
    def __init__(self):
        '''Nothing to see here.'''
        self.format = '>6xBB4xL4xL4xL'
    
    def decode(self, file_object):
        '''Decode the final 32 bytes of file_object.'''
        file_object.seek(-32, 2)
        trailer = unpack(self.format, file_object.read())
        return trailer
    
    def encode(self, offsets, table_offset):
        '''
        Encode the trailer for a binary plist file with given offsets and
        table_offet.
        '''
        offset_size = get_byte_width(max(offsets), 4)
        number_of_objects = len(offsets)
        reference_size = get_byte_width(number_of_objects, 2)
        root_object = 0
        return pack(self.format, offset_size, reference_size,
                    number_of_objects, root_object, table_offset)
    

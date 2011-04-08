from struct import pack, unpack
from datetime import datetime
from plistlib import Data
from time import mktime


class BinaryPlistBaseHandler(object):
    def encode(self, object_):
        object_ = self.encode_preprocess(object_)
        object_length = self.get_object_length(object_)
        first_byte = self.encode_first_byte(self.type_number, object_length)
        body = self.encode_body(object_, object_length)
        body = self.encode_postprocess(body)
        return ''.join((first_byte, body))
    
    def encode_preprocess(self, object_):
        return object_
    
    def get_object_length(self, object_):
        return len(object_)
    
    def encode_first_byte(self, type_number, length):
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
        encoded = pack('B', value)
        if big:
            return ''.join((encoded, real_length))
        return encoded
    
    def encode_body(self, object_, object_length):
        return ''
    
    def encode_postprocess(self, body):
        return body
    
    def decode(self, file_object, object_length):
        byte_length = self.get_byte_length(object_length)
        raw = file_object.read(byte_length)
        raw = self.decode_preprocess(raw)
        object_ = self.decode_body(raw, object_length)
        object_ = self.decode_postprocess(object_)
        return object_
    
    def get_byte_length(self, object_length):
        return object_length
    
    def decode_preprocess(self, raw):
        return raw
    
    def decode_body(self, raw, object_length):
        return raw
    
    def decode_postprocess(self, object_):
        return object_
    
    def unflatten(self, object_):
        return object_
    
    def collect_objects(self, object_, objects):
        try:
            find_with_type(object_, objects)
        except ValueError:
            objects.append(object_)
            self.collect_children(object_, objects)
    
    def collect_children(self, object, objects):
        pass
    

class BinaryPlistBooleanHandler(BinaryPlistBaseHandler):
    def __init__(self):
        BinaryPlistBaseHandler.__init__(self)
        self.type_number = 0
        self.types = (bool, type(None))
        self.integer_to_boolean = {0: None, 8: False, 9: True}
        self.boolean_to_integer = dict(zip(self.integer_to_boolean.values(),
                                           self.integer_to_boolean.keys()))
    
    def get_object_length(self, boolean):
        '''Return the object length for a boolean.'''
        return self.boolean_to_integer[boolean]
    
    def get_byte_length(self, object_length):
        return 0
    
    def decode_body(self, raw, object_length):
        return self.integer_to_boolean[object_length]
    

class BinaryPlistNumberHandler(BinaryPlistBaseHandler):
    def __init__(self):
        BinaryPlistBaseHandler.__init__(self)
    
    def encode_body(self, integer, object_length):
        return pack(self.formats[object_length], integer)
    
    def decode_body(self, raw, object_length):
        return unpack(self.formats[object_length], raw)[0]
    
    def get_byte_length(self, object_length):
        return 1 << object_length
    

class BinaryPlistIntegerHandler(BinaryPlistNumberHandler):
    def __init__(self):
        BinaryPlistNumberHandler.__init__(self)
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
    

class BinaryPlistFloatHandler(BinaryPlistNumberHandler):
    def __init__(self):
        BinaryPlistNumberHandler.__init__(self)
        self.type_number = 2
        self.formats = (None, None, 'f', 'd')
        self.types = float
    
    def get_object_length(self, float_):
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
    
    def encode_postprocess(self, body):
        return body[::-1]
    
    def decode_preprocess(self, raw):
        return raw[::-1]
    

class BinaryPlistDateHandler(BinaryPlistFloatHandler):
    def __init__(self):
        BinaryPlistFloatHandler.__init__(self)
        self.type_number = 3
        # seconds between 1 Jan 1970 and 1 Jan 2001
        self.epoch_adjustment = 978307200.0
        self.types = datetime
    
    def encode_preprocess(self, date):
        seconds = mktime(date.timetuple())
        return seconds - self.epoch_adjustment
    
    def decode_postprocess(self, seconds):
        seconds += self.epoch_adjustment
        return datetime.fromtimestamp(seconds)
    

class BinaryPlistDataHander(BinaryPlistBaseHandler):
    def __init__(self):
        BinaryPlistBaseHandler.__init__(self)
        self.type_number = 4
        self.types = type(Data(''))  # ugly
    
    def get_object_length(self, data):
        return len(data.data)
    
    def encode_body(self, data, object_length):
        return data.data
    
    def decode_body(self, raw, object_length):
        return Data(raw)
    

class BinaryPlistStringHandler(BinaryPlistBaseHandler):
    def __init__(self):
        BinaryPlistBaseHandler.__init__(self)
        self.type_number = 5
        self.encoding = 'ascii'
        self.types = str
    
    def encode_body(self, string, object_length):
        return string.encode(self.encoding)
    

class BinaryPlistUnicodeStringHandler(BinaryPlistStringHandler):
    def __init__(self):
        BinaryPlistStringHandler.__init__(self)
        self.type_number = 6
        self.encoding = 'utf_16_be'
        self.types = unicode
    
    def get_byte_length(self, object_length):
        return object_length * 2
    
    def decode_body(self, raw, object_length):
        return raw.decode(self.encoding)
    

class BinaryPlistContainerObjectHandler(BinaryPlistBaseHandler):
    def __init__(self):
        BinaryPlistBaseHandler.__init__(self)
        self.formats = (None, 'B', '>H')
        self.format = None
        self.reference_size = None
        self.objects = None
        self.object_handler = None
    
    def set_reference_size(self, reference_size):
        self.reference_size = reference_size
        self.format = self.formats[reference_size]
    
    def set_objects(self, objects):
        self.objects = objects
    
    def set_object_handler(self, object_handler):
        self.object_handler = object_handler
    
    def encode_reference_list(self, references):
        '''
        Return an encoded list of reference values. Used in encoding arrays and
        dictionaries.
        '''
        format_ = self.format * len(references)
        encoded = pack(format_, *references)
        return encoded
    
    def decode_reference_list(self, raw, object_length):
        format_ = self.format * object_length
        references = unpack(format_, raw)
        return list(references)
    
    def flatten_object_list(self, object_list):
        reference_list = []
        for object_ in object_list:
            reference = find_with_type(object_, self.objects)
            reference_list.append(reference)
        return reference_list
    
    def unflatten_reference_list(self, references):
        object_list = []
        for reference in references:
            item = self.objects[reference]
            item = self.object_handler.unflatten(item)
            object_list.append(item)
        return object_list
    

class BinaryPlistArrayHandler(BinaryPlistContainerObjectHandler):
    def __init__(self):
        BinaryPlistContainerObjectHandler.__init__(self)
        self.type_number = 0xa
        self.types = list
    
    def get_byte_length(self, object_length):
        return object_length * self.reference_size
    
    def encode_body(self, array, object_length):
        return self.encode_reference_list(array)
    
    def decode_body(self, raw, object_length):
        return self.decode_reference_list(raw, object_length)
    
    def flatten(self, array):
        return self.flatten_object_list(array)
    
    def unflatten(self, array):
        return self.unflatten_reference_list(array)
    
    def collect_children(self, array, objects):
        for item in array:
            self.object_handler.collect_objects(item, objects)
    

class BinaryPlistDictionaryHandler(BinaryPlistContainerObjectHandler):
    def __init__(self):
        BinaryPlistContainerObjectHandler.__init__(self)
        self.type_number = 0xd
        self.types = dict
    
    def get_byte_length(self, object_length):
        return object_length * self.reference_size * 2
    
    def encode_body(self, dictionary, object_length):
        keys = self.encode_reference_list(dictionary.keys())
        values = self.encode_reference_list(dictionary.values())
        return ''.join((keys, values))
    
    def decode_body(self, raw, object_length):
        half = object_length * self.reference_size
        keys = self.decode_reference_list(raw[:half], object_length)
        values = self.decode_reference_list(raw[half:], object_length)
        return dict(zip(keys, values))
    
    def flatten(self, dictionary):
        keys = self.flatten_object_list(dictionary.keys())
        values = self.flatten_object_list(dictionary.values())
        return dict(zip(keys, values))
    
    def unflatten(self, dictionary):
        keys = self.unflatten_reference_list(dictionary.keys())
        values = self.unflatten_reference_list(dictionary.values())
        return dict(zip(keys, values))
    
    def collect_children(self, dictionary, objects):
        for item in dictionary.keys() + dictionary.values():
            self.object_handler.collect_objects(item, objects)
    

class BinaryPlistObjectHandler(object):
    def __init__(self):
        handlers = [BinaryPlistBooleanHandler(), BinaryPlistIntegerHandler(),
                    BinaryPlistFloatHandler(), BinaryPlistDateHandler(),
                    BinaryPlistDataHander(), BinaryPlistStringHandler(),
                    BinaryPlistUnicodeStringHandler(),
                    BinaryPlistArrayHandler(), BinaryPlistDictionaryHandler()]
        self.handlers_by_type_number = {}
        self.handlers_by_type = {}
        for handler in handlers:
            self.handlers_by_type_number.update({handler.type_number: handler})
            if type(handler.types) == type:
                self.handlers_by_type.update({handler.types: handler})
            else:
                for type_ in handler.types:
                    self.handlers_by_type.update({type_: handler})
        self.set_object_handler()
    
    def set_on_containers(self, setter_function, value):
        array_handler = self.handlers_by_type[list]
        dictionary_handler = self.handlers_by_type[dict]
        setter_function(array_handler, value)
        setter_function(dictionary_handler, value)
    
    def set_reference_size(self, reference_size):
        function = BinaryPlistContainerObjectHandler.set_reference_size
        self.set_on_containers(function, reference_size)
    
    def set_objects(self, objects):
        function = BinaryPlistContainerObjectHandler.set_objects
        self.set_on_containers(function, objects)
    
    def set_object_handler(self):
        function = BinaryPlistContainerObjectHandler.set_object_handler
        self.set_on_containers(function, self)
    
    def encode(self, object_):
        handler = self.handlers_by_type[type(object_)]
        return handler.encode(object_)
    
    def decode(self, file_object):
        object_type, object_length = self.decode_first_byte(file_object)
        handler = self.handlers_by_type_number[object_type]
        return handler.decode(file_object, object_length)
    
    def flatten_objects(self, objects):
        flattened_objects = {}
        for item_index, item in enumerate(objects):
            if type(item) in (list, dict):
                flattened = self.flatten(item)
                flattened_objects.update({item_index: flattened})
        for index, object_ in flattened_objects.items():
            objects[index] = object_
    
    def flatten(self, object_):
        handler = self.handlers_by_type[type(object_)]
        return handler.flatten(object_)
    
    def unflatten(self, object_):
        handler = self.handlers_by_type[type(object_)]
        return handler.unflatten(object_)
    
    def decode_first_byte(self, file_object):
        value = unpack('B', file_object.read(1))[0]
        object_type = value >> 4
        object_length = value & 0xF
        if object_length == 15:
            object_length = self.decode(file_object)
        return object_type, object_length
    
    def collect_objects(self, object_, objects):
        handler = self.handlers_by_type[type(object_)]
        handler.collect_objects(object_, objects)
    

class BinaryPlistTableHandler(object):
    def __init__(self):
        self.formats = (None, 'B', '>H', 'BBB', '>L')
    
    def decode(self, file_object, offset_size, length, table_offset):
        file_object.seek(table_offset)
        offset_format = self.formats[offset_size]
        table_format = offset_format * length
        raw = file_object.read(offset_size * length)
        offsets = unpack(table_format, raw)
        if offset_size == 3:
            offsets = zip([offsets[x::3] for x in range(3)])
            offsets = [o[0] * 0x100 + o[1] * 0x10 + o[2] for o in offsets]
        return offsets
    
    def encode(self, offsets, offset_size):
        offset_format = self.formats[offset_size]
        table_format = offset_format * len(offsets)
        if offset_size == 3:
            new_offsets = []
            for offset in offsets[:]:
                first = offset // 0x100
                second = (offset % 0x100) // 0x10
                third = (offset % 0x100) % 0x10
                new_offsets += [first, second, third]
            offsets = new_offsets
        encoded = pack(table_format, *offsets)
        return encoded
    

class BinaryPlistTrailerHandler(object):
    def __init__(self):
        self.format = '>6xBB4xL4xL4xL'
    
    def decode(self, file_object):
        file_object.seek(-32, 2)
        trailer = unpack(self.format, file_object.read())
        return trailer
    
    def encode(self, offset_size, reference_size, objects, table_offset):
        number_of_objects = len(objects)
        root_object = 0
        return pack('6xBB4xL4xL4xL', offset_size, reference_size,
                    number_of_objects, root_object, table_offset)
    

def read(file_object):
    object_handler = BinaryPlistObjectHandler()
    table_handler = BinaryPlistTableHandler()
    trailer_handler = BinaryPlistTrailerHandler()
    trailer = trailer_handler.decode(file_object)
    object_handler.set_reference_size(trailer[1])
    table = table_handler.decode(file_object, trailer[0], 
                                 trailer[2], trailer[4])
    objects = []
    for offset in table:
        file_object.seek(offset)
        object_ = object_handler.decode(file_object)
        objects.append(object_)
    object_handler.set_objects(objects)
    root_object_number = trailer[3]
    root_object = objects[root_object_number]
    return object_handler.unflatten(root_object)

def write(file_object, root_object):
    '''Write the root_object to file_object.'''
    object_handler = BinaryPlistObjectHandler()
    table_handler = BinaryPlistTableHandler()
    trailer_handler = BinaryPlistTrailerHandler()
    objects = []
    object_handler.collect_objects(root_object, objects)
    object_handler.set_objects(objects)
    object_handler.flatten_objects(objects)
    reference_size = get_byte_width(len(objects), 2)
    object_handler.set_reference_size(reference_size)
    offsets = []
    file_object.write('bplist00')
    for object_ in objects:
        offsets.append(file_object.tell())
        encoded_object = object_handler.encode(object_)
        file_object.write(encoded_object)
    table_offset = file_object.tell()
    offset_size = get_byte_width(table_offset, 4)
    table = table_handler.encode(offsets, offset_size)
    trailer = trailer_handler.encode(offset_size, reference_size, objects,
                                     table_offset)
    file_object.write(table)
    file_object.write(trailer)

def get_byte_width(value_to_store, max_byte_width):
    for byte_width in range(max_byte_width):
        if 0x100 ** byte_width <= value_to_store < 0x100 ** (byte_width + 1):
            return byte_width + 1
    raise ValueError

def find_with_type(value, list_):
    '''
    Find value in list_, matching both for equality and type, and
    return the index it was found at. If not found, raise ValueError.
    '''
    for index, comparison_value in enumerate(list_):
        if (type(value) == type(comparison_value) and 
            value == comparison_value):
            return index
    raise ValueError

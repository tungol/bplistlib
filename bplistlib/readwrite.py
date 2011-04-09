from .classes import BinaryPlistObjectHandler, BinaryPlistTableHandler
from .classes import BinaryPlistTrailerHandler
from .functions import get_byte_width


def read(file_object):
    trailer = read_trailer(file_object)
    offset_size, reference_size, length, root, table_offset = trailer
    offsets = read_table(file_object, offset_size, length, table_offset)
    root_object = read_objects(file_object, offsets, reference_size, root)
    return root_object


def read_trailer(file_object):
    trailer_handler = BinaryPlistTrailerHandler()
    trailer = trailer_handler.decode(file_object)
    return trailer


def read_table(file_object, offset_size, length, table_offset):
    table_handler = BinaryPlistTableHandler()
    offsets = table_handler.decode(file_object, offset_size,
                                   length, table_offset)
    return offsets


def read_objects(file_object, offsets, reference_size, root):
    object_handler = BinaryPlistObjectHandler()
    object_handler.set_reference_size(reference_size)
    objects = []
    for offset in offsets:
        file_object.seek(offset)
        object_ = object_handler.decode(file_object)
        objects.append(object_)
    root_object = objects[root]
    return object_handler.unflatten(root_object, objects)


def write(file_object, root_object):
    '''Write the root_object to file_object.'''
    file_object.write('bplist00')
    offsets = write_objects(file_object, root_object)
    table_offset = write_table(file_object, offsets)
    write_trailer(file_object, offsets, table_offset)


def write_objects(file_object, root_object):
    objects = []
    object_handler = BinaryPlistObjectHandler()
    object_handler.collect_objects(root_object, objects)
    object_handler.flatten_objects(objects)
    reference_size = get_byte_width(len(objects), 2)
    object_handler.set_reference_size(reference_size)
    offsets = []
    for object_ in objects:
        offsets.append(file_object.tell())
        encoded_object = object_handler.encode(object_)
        file_object.write(encoded_object)
    return offsets


def write_table(file_object, offsets):
    table_handler = BinaryPlistTableHandler()
    table_offset = file_object.tell()
    table = table_handler.encode(offsets)
    file_object.write(table)
    return table_offset


def write_trailer(file_object, offsets, table_offset):
    trailer_handler = BinaryPlistTrailerHandler()
    trailer = trailer_handler.encode(offsets, table_offset)
    file_object.write(trailer)

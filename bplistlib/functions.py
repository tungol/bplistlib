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

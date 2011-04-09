#!/usr/bin/env python
# encoding: utf-8
'''This file contains the public functions for the module bplistlib.'''


from cStringIO import StringIO
from plistlib import readPlist, readPlistFromString
from .readwrite import read, write


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
        root_object = readPlist(path_or_file)
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
        return readPlistFromString(data)


def read_binary_plist(path_or_file):
    '''
    Parse a binary plist from a path or file object, and return the root
    object.
    '''
    did_open = False
    if isinstance(path_or_file, (str, unicode)):
        path_or_file = open(path_or_file)
        did_open = True
    root_object = read(path_or_file)
    if did_open:
        path_or_file.close()
    return root_object


def read_binary_plist_from_string(data):
    '''Parse a binary plist from a string and return the root object.'''
    return read_binary_plist(StringIO(data))


def write_binary_plist(path_or_file, root_object):
    '''
    Write a binary plist representation of the root object to the path or
    file object given.
    '''
    did_open = False
    if isinstance(path_or_file, (str, unicode)):
        path_or_file = open(path_or_file, "w")
        did_open = True
    write(path_or_file, root_object)
    if did_open:
        path_or_file.close()


def write_binary_plist_to_string(root_object):
    '''
    Encode the given root object as a binary plist and return a string of the
    encoding.
    '''
    string_io_object = StringIO()
    write_binary_plist(string_io_object, root_object)
    return string_io_object.getvalue()

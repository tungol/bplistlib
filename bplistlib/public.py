# encoding: utf-8
"""This file contains the public functions for the module bplistlib."""


from cStringIO import StringIO
import plistlib
from .readwrite import read, write


def readPlist(path_or_file, binary=None):
    """
    Read a plist from path_or_file. If the named argument binary is set to
    True, then assume path_or_file is a binary plist. If it's set to false,
    then assume it's an xml plist. Otherwise, try to detect the type and act
    accordingly. Return the root object.
    """
    did_open = False
    if isinstance(path_or_file, (str, unicode)):
        path_or_file = open(path_or_file)
        did_open = True
    if binary is True:
        root_object = read(path_or_file)
    elif binary is False:
        root_object = plistlib.readPlist(path_or_file)
    else:
        if path_or_file.read(8) == 'bplist00':
            root_object = read(path_or_file)
        else:
            path_or_file.seek(0)  # I'm not sure if this is necessary
            root_object = plistlib.readPlist(path_or_file)
    if did_open:
        path_or_file.close()
    return root_object


def readPlistFromString(data, binary=None):
    """
    Read a plist from a given string. If the named argument binary is set to
    True, then assume a binary plist. If it's set to False, then assume an xml
    plist. Otherwise, try to detect the type and act accordingly. Return the
    root object.
    """
    return readPlist(StringIO(data), binary=binary)


def writePlist(root_object, path_or_file, binary=False):
    """
    Write root_object to path_or_file. If the named argument binary is set to
    True, write a binary plist, otherwise write an xml one.
    """
    did_open = False
    if isinstance(path_or_file, (str, unicode)):
        path_or_file = open(path_or_file, "w")
        did_open = True
    if binary is True:
        write(root_object, path_or_file)
    else:
        plistlib.writePlist(root_object, path_or_file)
    if did_open:
        path_or_file.close()


def writePlistToString(root_object, binary=False):
    """
    Write root_object to a string. If the named argument binary is set to
    True, write a binary plist, otherwise write an xml one. Return the string.
    """
    string_io_object = StringIO()
    writePlist(root_object, string_io_object, binary=binary)
    return string_io_object.getvalue()

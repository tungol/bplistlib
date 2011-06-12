bplistlib
=========
Read and write binary .plist files.

This module is a drop-in enhancement of the plistlib module in the
standard libary. There are two different APIs which are roughly
equivalent. The legacy API provides an interface very similar to that
of plistlib, and allows for the use of this module in code already
written to use plistlib. The standard API provides an interface like the
json, pickle, and marshal modules in the standard library. Two classes
are additionally made available.

Legacy API
----------

    writePlist(obj, path_or_file[, binary])

Write obj to path_or_file. If path_or_file is a string, assume
it's a path and open that path for writing to.

If binary is True (default: False), write a binary plist file. Otherwise
an XML one is written.

    writePlistToString(obj[, binary])

Serialize obj to a plist formatted string.

If binary is True (default: False), format as a binary plist file,
Otherwise format as an XML one.

    readPlist(path_or_file[, binary])

Read an object from a plist formatted file. If path_or_file is a string,
assume it's a valid path and open up the file at that location for
reading first.

If binary is True, assume a binary formatted plist. If it is False,
assume an XML formatted plist. Otherwise, automatically detect the type.
The default behavior is to detect the type automatically.

    readPlistFromString(s[, binary])

Read an object from the plist formatted string, s.

If binary is True, assume a binary formatted plist. If it is False,
assume an XML formatted plist. Otherwise, automatically detect the type.
The default behavior is to detect the type automatically.

Standard API
------------

    dump(obj, fp[, binary])

Serialize obj as a property list formatted stream to fp (a
.write()-supporting file-like object).

If binary is True (default: False), serialize as a binary formatted
plist, otherwise as an XML one.

    dumps(obj[, binary])

SSerialize obj to a property list formatted str. The arguments have
the same meaning as in dump().

    load(fp[, binary])

Deserialize fp (a .read() and .seek()-supporting file-like object
containing a property list document) to a Python object.

If binary is True, assume a binary formatted plist. If binary is False
assume an XML formatted one. Otherwise, automatically detect the
formatting. The default behavior is to detect the formatting.

    loads(s[, binary])

Deserialize s (a str instance containing a property list document) to a
Python object. The arguments have the same meaning as in load().

Classes
-------

    Fill()

This allows for the conversion of a Fill type object from binary
property lists into a Python object and vice versa. I don't know what
Fill objects are for. There are no options or attributes.

    UID(value)

This allows for the conversion of UID typed objects from binary
property lists into Python objects and vice versa. The value can be any
positive integer.

Known issues:
-------------
The actual plist format is more restrictive than is enforced here. In
particular, key values in a plist dictionary must be strings, which is
not enforced. There may be other unenforced restrictions, be reasonable.

plutil notes mention "Output of float precision in binary format". Not
sure what that means.

Acknowledgements
----------------

I figured out details of the binary plist format from examining the perl
program pluitl.pl, version 1.6 which is available under the following
terms:

Any use is fine with attribution.

Author: Pete M. Wilson
Website: http://scw.us/iPhone/plutil/
Email: scw@gamewood.net
Copyright: 2007-2008 Starlight Computer Wizardry

Wording on some documentation modeled very heavily on wording in
documentation in the Python standard library.
bplistlib
=========
Read and write binary .plist files.

This module is a drop-in enhancement of the plistlib module in the standard libary. It provides four functions, which each have the same call signature as a function with the same name in plistlib, with the addition of an optional keyword argument, binary.

To write a plist use writePlist(root_object, path_or_file) or writePlistToString(root_object). Called like this, these functions will write an xml plist using plistlib. To write a binary plist, use writePlist(root_object, path_or_file, binary=True) or writePlistToString(root_object, binary=True).

To read a plist use readPlist(path_or_file) or readPlistFromString(data). Like this, these functions will attempt to determine whether the plist is binary or xml. If you know which you are reading, you can pass binary=True or binary=False in as an additional argument, for binary or xml plists, respectively.

Known issues:
The actual plist format is more restrictive than is enforced here. In particular, key values in a plist dictionary must be strings, which is not enforced. There may be other unenforced restrictions, be reasonable.


Acknowledgements
----------------

Early versions of read support in bplistlib were derived largely from the perl program pluil.pl, version 1.6 which is available under the following terms: 

Any use is fine with attribution.

Author: Pete M. Wilson
Website: http://scw.us/iPhone/plutil/
Email: scw@gamewood.net
Copyright: 2007-2008 Starlight Computer Wizardry
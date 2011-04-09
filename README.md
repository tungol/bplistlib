bplistlib
=========
Read and write binary .plist files.

This module is a drop-in enhancement of the plistlib module in the standard
libary. It provides four functions, which each have the same call signature
as a function with the same name in plistlib, with the addition of an
optional keyword argument, binary.

To write a plist use one of:

    writePlist(root_object, path_or_file)
    writePlistToString(root_object)

Called like this, these functions will write an xml plist using plistlib.
To write a binary plist, use one of:

    writePlist(root_object, path_or_file, binary=True)
    writePlistToString(root_object, binary=True)

To read a plist use one of:

    readPlist(path_or_file)
    readPlistFromString(data)

Like this, these functions will attempt to determine whether the plist is
binary or xml. If you know you have a binary plist, you can use one of:

    readPlist(path_or_file, binary=True)
    readPlistFromString(data, binary=True)

If you know you have an xml plist, you can use:

    readPlist(path_or_file, binary=False)
    readPlistFromString(data, binary=False)


Known issues:
The actual plist format is more restrictive than is enforced here. In
particular, key values in a plist dictionary must be strings, which is not
enforced. There may be other unenforced restrictions, be reasonable.


Acknowledgements
----------------

I figured out details of the binary plist format from examining the perl
program pluil.pl, version 1.6 which is available under the following
terms:

Any use is fine with attribution.

Author: Pete M. Wilson  
Website: http://scw.us/iPhone/plutil/  
Email: scw@gamewood.net  
Copyright: 2007-2008 Starlight Computer Wizardry
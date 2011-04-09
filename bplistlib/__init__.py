# encoding: utf-8
'''
bplistlib: Read and write binary .plist files.

This module is a drop-in enhancement of the plistlib module in the standard
libary. It provides four functions, which each have the same call signature as
a function with the same name in plistlib, with the addition of an optional
keyword argument, binary.

To write a plist use writePlist(root_object, path_or_file) or
writePlistToString(root_object). Called like this, these functions will write
an xml plist using plistlib. To write a binary plist, use
writePlist(root_object, path_or_file, binary=True) or
writePlistToString(root_object, binary=True).

To read a plist use readPlist(path_or_file) or readPlistFromString(data). Like
this, these functions will attempt to determine whether the plist is binary or
xml. If you know which you are reading, you can pass binary=True or
binary=False in as an additional argument, for binary or xml plists,
respectively.

Known issues:
The actual plist format is more restrictive than is enforced here.
'''


from .public import readPlist, readPlistFromString
from .public import writePlist, writePlistToString


__all__ = ['readPlist', 'readPlistFromString',
           'writePlist', 'writePlistToString']

__packages__ = ['bplistlib']
__version__ = '0.1'
__author__ = 'Stephen Morton'
__author_email__ = 'tungolcraft@gmail.com'
__description__ = 'Read and write binary .plist files.'
__license__ = 'BSD'
__platforms__ = 'any'
__url__ = 'https://github.com/tungolcraft/bplistlib'
__classifiers__ = [
  'Development Status :: 4 - Beta',
  'Intended Audience :: End Users/Desktop',
  'License :: OSI Approved :: BSD License',
  'Operating System :: OS Independent',
  'Programming Language :: Python',
  'Topic :: Software Development :: Libraries :: Python Modules',
]

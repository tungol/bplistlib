#!/usr/bin/env python
# encoding: utf-8
'''
bplistlib -- read binary .plist files. No write support.

Functions:

These two functions are analagous to the readPlist and readPlistFromString
functions available in plistlib:

readBPlist
readBPlistFromString

These two functions can discriminate between an XML plist file and a binary
plist file, and run the appropriate functions to parse that file:

readAnyPlist
readAnyPlistFromString
----------

bplistlib.py was derived largely from the perl program pluil.pl, version 1.6
which is available under the following terms:

Any use is fine with attribution.

Author: Pete M. Wilson
Website: http://scw.us/iPhone/plutil/
Email: scw@gamewood.net
Copyright: 2007-2008 Starlight Computer Wizardry
'''

from bplistlib import readAnyPlist, readBPlist, readAnyPlistFromString
from bplistlib import readBPlistFromString, writeBPlist, writeBPlistToString

__all__ = ['readAnyPlist', 'readBPlist', 'readAnyPlistFromString',
           'readBPlistFromString', 'writeBPlist', 'writeBPlistToString']

__version__ = '0.1'
__author__ = 'Stephen Morton'
__author_email__ = 'tungolcraft@gmail.com'
__description__ = 'Read and write binary .plist files.'
__license__ = 'BSD'
__url__ = 'https://github.com/tungolcraft/bplistlib'
__classifiers__ = [
  'Development Status :: 4 - Beta',
  'Intended Audience :: End Users/Desktop',
  'License :: OSI Approved :: BSD License',
  'Operating System :: OS Independent',
  'Programming Language :: Python',
  'Topic :: Software Development :: Libraries :: Python Modules'
]

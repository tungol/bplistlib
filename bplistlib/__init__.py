#!/usr/bin/env python
# encoding: utf-8


from .public import read_any_plist, read_any_plist_from_string
from .public import read_binary_plist, read_binary_plist_from_string
from .public import write_binary_plist, write_binary_plist_to_string


__all__ = ['read_any_plist', 'read_any_plist_from_string',
           'read_binary_plist', 'read_binary_plist_from_string',
           'write_binary_plist', 'write_binary_plist_to_string']

__packages__ = ['bplistlib']
__version__ = '0.1pre'
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

#!/usr/bin/env python
# encoding: utf-8

'''setup.py for bplistlib.'''

from distutils.core import setup
import bplistlib

setup(
      name = "bplistlib",
      version = bplistlib.__version__,
      packages = ['bplistlib'],
      author = bplistlib.__author__,
      author_email = bplistlib.__author_email__,
      description = bplistlib.__description__,
      license = bplistlib.__license__,
      long_description = bplistlib.__doc__,
      platforms='any',
      url = bplistlib.__url__,
      classifiers = bplistlib.__classifiers__
)

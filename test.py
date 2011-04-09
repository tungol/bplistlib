#!/usr/bin/env python
# encoding: utf-8
'''Test suite for bplistlib. Pretty good coverage.'''

from datetime import datetime
from plistlib import Data
from os import remove
import bplistlib as bp


test_values = [True, False, None, 1, 1.01, 2.0 ** 128, datetime.now(),
               Data('1234'), 'hello', u'world', [1,2,3,4], {1:2, 3:4},
               range(0x100)]
for value in test_values:
    plist = bp.writePlistToString(value, binary=True)
    result = bp.readPlistFromString(plist)
    print repr(result)
big = []
for i in range(10):
    big.append(Data(str(i) * 1700000))
bp.readPlistFromString(bp.writePlistToString(big, binary=True), binary=True)

a = {'1':2, '3':4}
bp.readPlistFromString(bp.writePlistToString(a))
bp.writePlist(a, 'tmp')
bp.readPlist('tmp', binary=False)
remove('tmp')

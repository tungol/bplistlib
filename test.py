#!/usr/bin/env python
# encoding: utf-8
"""Test suite for bplistlib. Pretty good coverage."""

from datetime import datetime
from plistlib import Data
from os import remove
import unittest
import random
import bplistlib as bp


class Tests(unittest.TestCase):
    
    def test_true(self):
        value = True
        result = through_string(value)
        self.assertIsInstance(result, type(value))
        self.assertIs(value, result)
    
    def test_false(self):
        value = False
        result = through_string(value)
        self.assertIsInstance(result, type(value))
        self.assertIs(value, result)
    
    def test_none(self):
        value = None
        result = through_string(value)
        self.assertIsInstance(result, type(value))
        self.assertIs(value, result)
    
    def test_small_integer(self):
        for i in range(20):
            value = random.randint(-500, 500)
            result = through_string(value)
            self.assertIsInstance(result, type(value))
            self.assertEqual(value, result)
    
    def test_large_integer(self):
        for i in range(20):
            value = random.randint(-500, 500) * 2.0 ** 128
            result = through_string(value)
            self.assertIsInstance(result, type(value))
            self.assertEqual(value, result)
    
    def test_small_float(self):
        for i in range(20):
            value = random.uniform(-500, 500)
            result = through_string(value)
            self.assertIsInstance(result, type(value))
            self.assertAlmostEqual(value, result, places=3)
    
    def test_large_float(self):
        for i in range(20):
            value = random.uniform(-500, 500) * 2.0 ** 128
            result = through_string(value)
            self.assertIsInstance(result, type(value))
            self.assertAlmostEqual(value, result, places=3)
    
    def test_date(self):
        value = datetime.now()
        result = through_string(value)
        self.assertIsInstance(result, type(value))
        self.assertEqual(value.year, result.year)
        self.assertEqual(value.month, result.month)
        self.assertEqual(value.day, result.day)
        self.assertEqual(value.hour, result.hour)
        self.assertEqual(value.minute, result.minute)
    
    def test_data(self):
        value = Data('\xe0\x54\x6e\xb3\x2e\x7f\xe2\x0c\xd4\xad\x05\x49\xfc\xe2\xe4\xb8')
        result = through_string(value)
        self.assertIsInstance(result, Data)
        self.assertEqual(value.data, result.data)
    
    def test_string(self):
        value = 'hello'
        result = through_string(value)
        self.assertIsInstance(result, type(value))
        self.assertEqual(value, result)
    
    def test_unicode(self):
        value = u'world'
        result = through_string(value)
        self.assertIsInstance(result, type(value))
        self.assertEqual(value, result)
    
    def test_array(self):
        value = [1, 2, 3, 4]
        result = through_string(value)
        self.assertIsInstance(result, type(value))
        self.assertEqual(value, result)
    
    def test_dictionary(self):
        value = {1: 2, 3: 4}
        result = through_string(value)
        self.assertIsInstance(result, type(value))
        self.assertEqual(value, result)
    
    def test_many_objects(self):
        value = range(0x100)
        result = through_string(value)
        self.assertIsInstance(result, type(value))
        self.assertEqual(value, result)
    
    def test_high_offsets(self):
        value = []
        for i in range(10):
            value.append(str(i) * 1700000)
        result = through_string(value)
        self.assertIsInstance(result, type(value))
        self.assertEqual(value, result)
    
    def test_binary_equals_true(self):
        value = True
        result = through_string(value, read_binary=True)
        self.assertIsInstance(result, type(value))
        self.assertIs(value, result)
    
    def test_not_binary(self):
        value = {'1': 2, '3': 4}
        fn = 'tmp'
        bp.writePlist(value, fn)
        result = bp.readPlist(fn)
        self.assertIsInstance(result, type(value))
        self.assertEqual(value, result)
        remove('tmp')
    
    def test_not_binary2(self):
        value = {'1': 2, '3': 4}
        fn = 'tmp'
        bp.writePlist(value, fn)
        result = bp.readPlist(fn, binary=False)
        self.assertIsInstance(result, type(value))
        self.assertEqual(value, result)
        remove('tmp')
    

def through_string(value, write_binary=True, read_binary=None):
    plist = bp.writePlistToString(value, binary=write_binary)
    return bp.readPlistFromString(plist, binary=read_binary)


if __name__ == '__main__':
    unittest.main()
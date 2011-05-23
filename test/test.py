#!/usr/bin/env python
# encoding: utf-8
"""Test suite for bplistlib. Pretty good coverage."""
# although note that because everything is round trip encode/decode,
# as long as the bug is symmetric, deviations from spec in encoded form
# may be missed.

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
    
    def test_fill(self):
        value = bp.Fill
        result = through_string(value)
        self.assertIsInstance(result, type(value))
        self.assertIs(value, result)
    
    def test_fill_representation(self):
        value = repr(bp.Fill)
        self.assertIsInstance(value, str)
        self.assertEqual(value, 'Fill')
    
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
        value = Data('\xe0\x54\x6e\xb3\x2e\x7f\xe2\x0c\xd4\xad\x05\x49\xfc')
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
    
    def test_uid(self):
        value = bp.UID(25)
        result = through_string(value)
        self.assertIsInstance(result, type(value))
        self.assertEqual(value, result)
    
    def test_big_uid(self):
        value = bp.UID(2225)
        result = through_string(value)
        self.assertIsInstance(result, type(value))
        self.assertEqual(value, result)
    
    def test_uid_representation(self):
        value = repr(bp.UID(36))
        self.assertIsInstance(value, str)
        self.assertEqual(value, 'UID(36)')
    
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
    plist = bp.dumps(value, binary=write_binary)
    return bp.loads(plist, binary=read_binary)



def suite():
    suite = unittest.TestSuite()
    methods = [m for m in dir(Tests) if callable(getattr(Tests, m))
                                     and m[:5] == 'test_']
    for method in methods:
        suite.addTest(Tests(method))
    return suite

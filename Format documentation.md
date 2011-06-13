This file describes the format of binary .plist files.

Available types
===============

The following types are available in a binary plist:

 1. singleton (boolean, null, fill)
 2. integer
 3. float
 4. date
 5. binary data
 6. single byte string
 7. double byte string
 8. UID
 9. array
 10. dictionary


File Sections
=============

A binary plist file has four sections:

1. The first 8 bytes are an identifier and always equal to 'bplist00'.

2. Second is all of the elements in the plist, encoded and concatenated.

3. Third is the concatenation of the offsets of all of the elements in the 
   plist, each offset given as an unsigned integer in a fixed number of 
   bytes. An object in the plist has a reference number that is based on the 
   0-based indexing of this table, e.g. object number 0 is the object at the 
   offset given first in this table.

4. The final 32 bytes, the "trailer" section.


Trailer
=======

The final 32 bytes of a binary plist have the following format:

  1. 6 bytes of \x00 padding
  
  2. a 1 byte integer which is the number of bytes for an offset value. 
     Valid values are 1, 2, 3, or 4. Offset values are encoded as unsigned, 
     big endian integers. Must be wide enough to encode the offset of the
     offset table, not just the highest object offset.
     
  3. a 1 byte integer which is the number of bytes for an object reference 
     number. Valid values are 1 or 2. Reference numbers are encoded as 
     unsigned, bug endian integers.
     
  4. 4 bytes of \x00 padding
  
  5. a 4 byte integer which is the number of objects in the plist
  
  6. 4 bytes of \x00 padding
  
  7. a 4 byte integer which is the reference number of the root object in 
     the plist. This is usually zero.
     
  8. 4 bytes of \x00 padding
  
  9. a 4 byte integer which is the offset in the file of the start of the 
     offset table, named above as the third element in a binary plist


Object encoding
===============

The encoding of the available types are as follows:

The first four bits are an id number of the object type, according to the 
following mapping:

 0x0 singleton
 0x1 integer
 0x2 float
 0x3 date
 0x4 binary data
 0x5 single byte string
 0x6 double byte string
 0x8 UID
 0xa array
 0xd dictionary

The second four bits are the size of the object. If the value given is 15, 
this means that the true object size is greater than can be expressed in 
four bits. In this case, the next byte is the start of the true size,
encoded like the integer objects, except the value is unsigned. This is not
the case for 0x0 type objects however, see below for details. I will refer to
this value as the object length.

The encoding for the remainder of the object varies by type. The "byte 
length" is the number of bytes used in encoding the object, not counting the 
encoding of the type id number and object length already discussed.


Singleton
---------

Type number 0x0 groups together boolean values, a null value, and something
called 'fill' by plutil.pl. I don't know what fill is for. The object length
is actually the value of the object, and the byte length is always zero. A
value of 0 means null, 8 means False, 9 means True, and 15 means fill. Any
other value is invalid.


Integer
-------

The byte length is equal to 2 to the power of the object length. Valid 
object lengths are 0, 1, 2, and 3 for 1, 2, 4, and 8 byte integers, 
respectively. The encoding is as a big-endian, signed integer in the 
appropriate number of bytes.


Float
-----

The object length to byte length conversion is the same as for integers. The 
object length can be 2 or 3, corresponding to a byte length of 4 or 8. The 
encoding is as a single-precision or a double-precision float, accordingly. 
Byte order is reversed from IEEE 754.


Date
----

Dates are stored as a float with a value of seconds since the epoch of 1 
January 2001, 0:00:00 GMT. Encoding is the same as the encoding for floats.


Binary Data
-----------

The byte length is the object length, and any value is valid. The bytes are 
not interpreted.


Single Byte String
------------------

The byte length is the object length, and any value is valid. Encoding is
ASCII.


Double Byte String
------------------

The byte length is twice the object length, and any value is valid. The 
encoding is utf-16 (big endian).


UID
---

Encoding is as integers, except values are unsigned. These are used
extensively in files written using NSKeyedArchiver, a serializer for
Objective-C objects. The UID value seems to be the index of a value within
the $objects list inside such a plist.

Array
-----

The byte length is the object length times the number of bytes per object 
reference for this plist file, i.e. either one or two times the object 
length. Any object length is valid. The encoding is the concatenation of 
object reference numbers as unsigned, big-endian integers each encoded in 
the number of bytes per object reference for this plist file.


Dictionary
----------

The byte length is twice the object length times the number of bytes per 
object reference. The encoding is as the concatenation of two encoded 
arrays, the first of keys and the second of values. The first value in the 
list of keys corresponds to the first value in the list of values, and so 
on.

Final Notes
===========

When writing a binary plist file, any values that repeat within the file 
should be encoded only once and that single object referenced where ever 
that value repeats.
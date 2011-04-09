from datetime import datetime
from plistlib import Data
import bplistlib as bp
test_values = [True, False, None, 1, 1.01, 2.0 ** 128, datetime.now(),
               Data('1234'), 'hello', u'world', [1,2,3,4], {1:2, 3:4},
               range(0x100)]
for value in test_values:
    plist = bp.write_binary_plist_to_string(value)
    result = bp.read_any_plist_from_string(plist)
    print repr(result)
big = []
for i in range(10):
    big.append(Data(str(i) * 1700000))
bp.read_any_plist_from_string(bp.write_binary_plist_to_string(big))
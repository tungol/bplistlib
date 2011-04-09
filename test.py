from datetime import datetime
from plistlib import Data
import bplistlib as bp
test_values = [True, False, None, 1, 1.01, datetime.now(), Data('1234'),
               'hello', u'world', [1,2,3,4], {1:2, 3:4}]
for value in test_values:
    plist = bp.write_binary_plist_to_string(value)
    result = bp.read_any_plist_from_string(plist)
    print repr(result)
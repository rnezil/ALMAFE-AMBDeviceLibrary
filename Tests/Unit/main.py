import os
import sys
from os.path import dirname
import unittest

# # add the top-level project path to PYTHONPATH:
# projectRoot = dirname(dirname(dirname(__file__)))
#
# if not projectRoot in sys.path:
#     sys.path.append(projectRoot)
#
# # and change to that directory:
# os.chdir(projectRoot)

# from AMBDevice.Tests.Unit.AMBConnection import test_AMBConnection
from Tests.Unit.AMBDevice import test_AMBDevice
        
if __name__ == "__main__":
    unittest.main() # run all tests
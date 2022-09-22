import os
import sys
from os.path import dirname
import unittest

# add the top-level project path to PYTHONPATH:
projectRoot = dirname(dirname(dirname(__file__)))

if not projectRoot in sys.path:
    sys.path.append(projectRoot)

# and change to that directory:
os.chdir(projectRoot)

from Tests.Unit.AMBConnectionNican import test_AMBConnectionNican
from Tests.Unit.AMBConnectionDLL import test_AMBConnectionDLL
from Tests.Unit.AMBDevice import test_AMBDeviceNican
from Tests.Unit.AMBDevice import test_AMBDeviceDLL
from Tests.Unit.FEMCDevice import test_FEMCDevice
from Tests.Unit.LODevice import test_LODevice
from Tests.Unit.CCADevice import test_CCADevice
from Tests.Unit.IVCurve import test_IVCurve

if __name__ == "__main__":
    try:
        unittest.main() # run all tests
    except SystemExit as e:
        pass # silence this exception
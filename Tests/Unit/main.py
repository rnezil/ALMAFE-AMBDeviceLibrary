import os
import sys
from os.path import dirname
import unittest
import logging

LOG_TO_FILE = False
LOG_FILE = 'ALMAFE-AMBDeviceLibrary.log'

logger = logging.getLogger("ALMAFE-AMBDeviceLibrary")
logger.setLevel(logging.DEBUG)
if LOG_TO_FILE:
    handler = logging.FileHandler(LOG_FILE)
else:
    handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(fmt = '%(asctime)s %(levelname)s:%(message)s'))
logger.addHandler(handler)
logger.info("-----------------------------------------------------------------")

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
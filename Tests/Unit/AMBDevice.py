import unittest

from AMB.AMBConnection import AMBConnection
from AMB.AMBDevice import AMBDevice

class test_AMBDevice(unittest.TestCase):
    SET_FE_MODE             = 0x2100E
    GET_AMBSI_PROTOCOL_REV  = 0x30000
    
    def setUp(self):
        self.conn = AMBConnection(channel = 0, forceLocal = True, resetOnError = True)
        self.dev = AMBDevice(self.conn, nodeAddr = 0x13)
        
    def tearDown(self):
        self.dev.shutdown()
        self.conn.shutdown()
        self.dev = None
        self.conn = None
        
    def test_command(self):
        # this assumes that the device is an FEMC module.   The AMBSI alone has no commands we can test.
        self.dev.command(self.SET_FE_MODE, b'\0x00')
        self.dev.command(self.SET_FE_MODE, b'\0x01')
        self.dev.command(self.SET_FE_MODE, b'\0x02')
        self.dev.command(self.SET_FE_MODE, b'\0x03')
        self.dev.command(self.SET_FE_MODE, b'\0x00')
        
    def test_monitor(self):
        data = self.dev.monitor(self.GET_AMBSI_PROTOCOL_REV)
        self.assertIsInstance(data, bytearray)
        self.assertTrue(len(data) > 0)
    
    def test_getAmbsiProtocolRev(self):
        revisionStr = self.dev.getAmbsiProtocolRev()
        self.assertIsInstance(revisionStr, str)
        self.assertTrue(len(revisionStr) >= 5)
        
    def test_getAmbsiErrors(self):
        numErr, lastErr = self.dev.getAmbsiErrors()
        self.assertIsInstance(numErr, int)
        self.assertIsInstance(lastErr, int)
        
    def test_getAmbsiNumTrans(self):
        num = self.dev.getAmbsiNumTrans()
        self.assertIsInstance(num, int)
        self.assertTrue(num > 0)
        
    def test_getAmbsiTemperature(self):
        temp = self.dev.getAmbsiTemperature()
        self.assertIsInstance(temp, float)
        self.assertTrue(temp != 0.0)
        
    def test_getAmbsiSoftwareRev(self):
        revisionStr = self.dev.getAmbsiProtocolRev()
        self.assertIsInstance(revisionStr, str)
        self.assertTrue(len(revisionStr) >= 5)
        
    
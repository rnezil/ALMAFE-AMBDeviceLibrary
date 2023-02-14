import unittest
from AMB.AMBConnectionDLL import AMBConnectionDLL
from AMB.AMBConnectionNican import AMBConnectionNican
from AMB.AMBDevice import AMBDevice

class t_AMBDevice(unittest.TestCase):
    GET_FE_MODE             = 0x2000E    
    SET_FE_MODE             = 0x2100E
    GET_AMBSI_PROTOCOL_REV  = 0x30000
    
    def setUp(self):
        pass
        
    def tearDown(self):
        if self.dev:
            self.dev.shutdown()
            self.dev = None
        
    def impl_t_command(self, conn):
        self.dev = AMBDevice(conn, nodeAddr = 0x13)
        # this assumes that the device is an FEMC module.   The AMBSI alone has no commands we can test.
        prevMode = self.dev.monitor(self.GET_FE_MODE)
        self.dev.command(self.SET_FE_MODE, b'\x00')
        mode = self.dev.monitor(self.GET_FE_MODE)
        self.assertTrue(mode == b'\x00', "SET_FE_MODE failed")
        self.dev.command(self.SET_FE_MODE, b'\x01')
        mode = self.dev.monitor(self.GET_FE_MODE)
        self.assertTrue(mode == b'\x01', "SET_FE_MODE failed")
        # not testing x02 because that starts the FTP server in FEMC >= 3.5
        self.dev.command(self.SET_FE_MODE, b'\x03')
        mode = self.dev.monitor(self.GET_FE_MODE)
        self.assertTrue(mode == b'\x03', "SET_FE_MODE failed")
        self.dev.command(self.SET_FE_MODE, prevMode)
        mode = self.dev.monitor(self.GET_FE_MODE)
        self.assertTrue(mode == prevMode, "SET_FE_MODE failed")
        
    def impl_t_monitor(self, conn):
        self.dev = AMBDevice(conn, nodeAddr = 0x13)
        data = self.dev.monitor(self.GET_AMBSI_PROTOCOL_REV)
        self.assertIsInstance(data, bytes)
        self.assertTrue(len(data) > 0)
        
    
    def impl_t_getAmbsiProtocolRev(self, conn):
        self.dev = AMBDevice(conn, nodeAddr = 0x13)
        revisionStr = self.dev.getAmbsiProtocolRev()
        self.assertIsInstance(revisionStr, str)
        self.assertTrue(len(revisionStr) >= 5)
        
    def impl_t_getAmbsiErrors(self, conn):
        self.dev = AMBDevice(conn, nodeAddr = 0x13)
        numErr, lastErr = self.dev.getAmbsiErrors()
        self.assertIsInstance(numErr, int)
        self.assertIsInstance(lastErr, int)
        
    def impl_t_getAmbsiNumTrans(self, conn):
        self.dev = AMBDevice(conn, nodeAddr = 0x13)
        num = self.dev.getAmbsiNumTrans()
        self.assertIsInstance(num, int)
        self.assertTrue(num > 0)
        
    def impl_t_getAmbsiTemperature(self, conn):
        self.dev = AMBDevice(conn, nodeAddr = 0x13)
        temp = self.dev.getAmbsiTemperature()
        self.assertIsInstance(temp, float)
        self.assertTrue(temp != 0.0)
        
    def impl_t_getAmbsiSoftwareRev(self, conn):
        self.dev = AMBDevice(conn, nodeAddr = 0x13)
        revisionStr = self.dev.getAmbsiProtocolRev()
        self.assertIsInstance(revisionStr, str)
        self.assertTrue(len(revisionStr) >= 5)
        
class test_AMBDeviceNican(t_AMBDevice):
    conn = None
    
    @classmethod
    def setUpClass(cls):
        cls.conn = AMBConnectionNican(channel = 0, resetOnError = True)
        
    @classmethod
    def tearDownClass(cls):
        cls.conn.shutdown()
    
    def setUp(self):
        super(test_AMBDeviceNican, self).setUp()

    def tearDown(self):
        super(test_AMBDeviceNican, self).tearDown()
    
    def test_command(self):
        self.impl_t_command(self.conn)
        
    def test_monitor(self):
        self.impl_t_monitor(self.conn)
        
    def test_getAmbsiProtocolRev(self):
        self.impl_t_getAmbsiProtocolRev(self.conn)
        
    def test_getAmbsiErrors(self):
        self.impl_t_getAmbsiErrors(self.conn)
    
    def test_getAmbsiNumTrans(self):
        self.impl_t_getAmbsiNumTrans(self.conn)
        
    def test_getAmbsiTemperature(self):
        self.impl_t_getAmbsiTemperature(self.conn)
        
    def test_getAmbsiSoftwareRev(self):
        self.impl_t_getAmbsiSoftwareRev(self.conn) 
    
class test_AMBDeviceDLL(t_AMBDevice):
    conn = None
    
    @classmethod
    def setUpClass(cls):
        cls.conn = AMBConnectionDLL(channel = 0, dllName = 'L:\ALMA-FEControl\FrontEndAMBDLL\deploy\FrontEndAMB.dll')
        
    @classmethod
    def tearDownClass(cls):
        cls.conn.shutdown()
         
    def setUp(self):
        super(test_AMBDeviceDLL, self).setUp()

    def tearDown(self):
        super(test_AMBDeviceDLL, self).tearDown()
        
    def test_command(self):
        self.impl_t_command(self.conn)
        
    def test_monitor(self):
        self.impl_t_monitor(self.conn)
        
    def test_getAmbsiProtocolRev(self):
        self.impl_t_getAmbsiProtocolRev(self.conn)
        
    def test_getAmbsiErrors(self):
        self.impl_t_getAmbsiErrors(self.conn)
    
    def test_getAmbsiNumTrans(self):
        self.impl_t_getAmbsiNumTrans(self.conn)
        
    def test_getAmbsiTemperature(self):
        self.impl_t_getAmbsiTemperature(self.conn)
        
    def test_getAmbsiSoftwareRev(self):
        self.impl_t_getAmbsiSoftwareRev(self.conn) 

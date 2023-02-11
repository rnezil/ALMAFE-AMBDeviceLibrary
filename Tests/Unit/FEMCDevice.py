import unittest
from AMB.AMBConnectionNican import AMBConnectionNican
from AMB.AMBConnectionDLL import AMBConnectionDLL
from AMB.FEMCDevice import FEMCDevice
from time import sleep

class test_FEMCDevice(unittest.TestCase):
    GET_YTO_COARSE_TUNE    = 0x00800
    SET_YTO_COARSE_TUNE    = 0x10800
    GET_PHOTOMIXER_ENABLE  = 0x00810
    SET_PHOTOMIXER_ENABLE  = 0x10810
    GET_PHOTOMIXER_VOLTAGE = 0x00814
    GET_PA_DRAIN_VOLTAGE   = 0x00841
    SET_PA_DRAIN_VOLTAGE   = 0x10841
    conn = None
    
    @classmethod
    def setUpClass(cls):
        # cls.conn = AMBConnectionNican(channel = 0, resetOnError = True)
        cls.conn = AMBConnectionDLL(channel = 0)
        
    @classmethod
    def tearDownClass(cls):
        cls.conn.shutdown()
        
    def setUp(self):
        self.dev = FEMCDevice(self.conn, 0x13)
        self.dev.initSession(FEMCDevice.MODE_SIMULATE)
        
    def tearDown(self):
        self.dev.shutdown()
    
    def test_getFemcVersion(self):
        data = self.dev.getFemcVersion()
        self.assertTrue(data is not None, "Failed getFemcVersion()")
        self.assertTrue(len(data) >= 5)

    def test_setFeMode(self):
        prevMode = self.dev.getFeMode()
        self.dev.setFeMode(FEMCDevice.MODE_OPERATIONAL)
        mode = self.dev.getFeMode()
        self.assertTrue(mode == FEMCDevice.MODE_OPERATIONAL, "SET_FE_MODE failed")
        self.dev.setFeMode(FEMCDevice.MODE_TROUBLESHOOTING)
        mode = self.dev.getFeMode()
        self.assertTrue(mode == FEMCDevice.MODE_TROUBLESHOOTING, "SET_FE_MODE failed")
        # not testing MODE_MAINTENANCE because that starts the FTP server in FEMC >= 3.5
        self.dev.setFeMode(FEMCDevice.MODE_SIMULATE)
        mode = self.dev.getFeMode()
        self.assertTrue(mode == FEMCDevice.MODE_SIMULATE, "SET_FE_MODE failed")
        self.dev.setFeMode(prevMode)
        mode = self.dev.getFeMode()
        self.assertTrue(mode == prevMode, "SET_FE_MODE failed")

    def test_getEsnList(self):
        esns = self.dev.getEsnList(True)
        self.assertIsNotNone(esns, "getEsnList failed")
        self.assertTrue(len(esns) >= 1)
        
    def test_getEsnString(self):
        esns = self.dev.getEsnString()
        self.assertTrue(len(esns) >= 10)
        print(esns)

    def test_setBandPower(self):
        self.dev.setAllBandsOff()
        self.dev.setBandPower(FEMCDevice.PORT_BAND7, True)
        sleep(0.2)
        self.assertTrue(self.dev.getNumBandsPowered() == 1)
        self.dev.setBandPower(FEMCDevice.PORT_BAND6, True)
        sleep(0.2)
        self.assertTrue(self.dev.getNumBandsPowered() == 2)
        self.dev.setBandPower(FEMCDevice.PORT_BAND7, False)
        self.dev.setBandPower(FEMCDevice.PORT_BAND6, False)
        sleep(0.2)
        self.assertTrue(self.dev.getNumBandsPowered() == 0)
        
    def test_monitor(self):
        self.dev.setBandPower(FEMCDevice.PORT_BAND6, True)
        sleep(0.2)
        self.dev.setPort(FEMCDevice.PORT_BAND6)
        data = self.dev.monitor(self.GET_YTO_COARSE_TUNE)
        tune = self.dev.unpackU16(data)
        self.assertTrue(tune >= 0 and tune <= 4095)
        
        data = self.dev.monitor(self.GET_PHOTOMIXER_ENABLE)
        enable = self.dev.unpackBool(data)
        self.assertIsNotNone(enable)
        
        data = self.dev.monitor(self.GET_PHOTOMIXER_VOLTAGE)
        volts = self.dev.unpackFloat(data)
        self.assertTrue(volts >= 0.0 and volts <= 5.0)
                        
    def test_command(self):
        self.dev.setBandPower(FEMCDevice.PORT_BAND6, True)
        sleep(0.2)
        self.dev.setPort(FEMCDevice.PORT_BAND6)
        self.assertTrue(self.dev.command(self.SET_PHOTOMIXER_ENABLE, FEMCDevice.packBool(False)))
        enable = self.dev.unpackBool(self.dev.monitor(self.GET_PHOTOMIXER_ENABLE))
        self.assertFalse(enable)
        
        self.assertTrue(self.dev.command(self.SET_PHOTOMIXER_ENABLE, FEMCDevice.packBool(True)))
        enable = self.dev.unpackBool(self.dev.monitor(self.GET_PHOTOMIXER_ENABLE))
        self.assertTrue(enable)
    
        self.assertTrue(self.dev.command(self.SET_PA_DRAIN_VOLTAGE, FEMCDevice.packFloat(1.2)))
        volts = self.dev.unpackFloat(self.dev.monitor(self.GET_PA_DRAIN_VOLTAGE))
        self.assertTrue(volts >= 0.0 and volts <= 5.0)

        self.assertTrue(self.dev.command(self.SET_YTO_COARSE_TUNE, FEMCDevice.packU16(1234)))
        tune = self.dev.unpackU16(self.dev.monitor(self.GET_YTO_COARSE_TUNE))
        self.assertTrue(tune == 1234)
        
    def test_getAmbsiProtocolRev(self):
        # test that we can call AMBDevice methods on an FEMCDevice object
        revisionStr = self.dev.getAmbsiProtocolRev()
        self.assertIsInstance(revisionStr, str)
        self.assertTrue(len(revisionStr) >= 5)
        
    def test_getAmbsiErrors(self):
        # test that we can call AMBDevice methods on an FEMCDevice object
        numErr, lastErr = self.dev.getAmbsiErrors()
        self.assertIsInstance(numErr, int)
        self.assertIsInstance(lastErr, int)
        
    def test_getAmbsiNumTrans(self):
        # test that we can call AMBDevice methods on an FEMCDevice object
        num = self.dev.getAmbsiNumTrans()
        self.assertIsInstance(num, int)
        self.assertTrue(num > 0)
        
    def test_getAmbsiTemperature(self):
        # test that we can call AMBDevice methods on an FEMCDevice object
        temp = self.dev.getAmbsiTemperature()
        self.assertIsInstance(temp, float)
        self.assertTrue(temp != 0.0)
        
    def test_getAmbsiSoftwareRev(self):
        # test that we can call AMBDevice methods on an FEMCDevice object
        revisionStr = self.dev.getAmbsiProtocolRev()
        self.assertIsInstance(revisionStr, str)
        self.assertTrue(len(revisionStr) >= 5)        
